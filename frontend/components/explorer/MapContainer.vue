<template>
    <div ref="mapContainer" class="map-container" />
</template>

<script setup lang="ts">
import mapboxgl from "mapbox-gl";
import type { FeatureCollection, Geometry } from "geojson";
import { useMap } from "~/composables/explorer/useMap";
import type { GeoJSONFeatureCollection } from "~/utils/api";
import { useChoropleth, CHOROPLETH_SOURCE_ID } from "~/composables/explorer/useChoropleth";
import {
    fetchMapData,
    fetchAllCountyMapData,
    fetchZipsInCounty,
    MAX_FEATURES_PER_REQUEST,
} from "~/composables/api/useMapData";
import { createMapFeatureCache } from "~/utils/mapFeatureCache";

const MAX_FETCH_ROUNDS = 5;
const MOVEEND_DEBOUNCE_MS = 300;

function emptyFc(): GeoJSONFeatureCollection {
    return { type: "FeatureCollection", features: [] };
}

function boundsFromGeometry(geometry: Geometry): mapboxgl.LngLatBounds {
    const bounds = new mapboxgl.LngLatBounds();
    if (geometry.type === "Polygon") {
        for (const ring of geometry.coordinates as number[][][]) {
            for (const [lng, lat] of ring) {
                bounds.extend([lng, lat]);
            }
        }
    } else if (geometry.type === "MultiPolygon") {
        for (const poly of geometry.coordinates as number[][][][]) {
            for (const ring of poly) {
                for (const [lng, lat] of ring) {
                    bounds.extend([lng, lat]);
                }
            }
        }
    }
    return bounds;
}

const mapContainer = ref<HTMLElement | null>(null);
const store = useExplorerStore();
const { initMap, destroyMap, getMap } = useMap();
const {
    addLegacyChoroplethLayer,
    ensureCountyZipLayers,
    setZipLayerData,
    updateLegacyChoroplethColors,
    updateCountyZipChoroplethColors,
    removeLegacyChoroplethLayer,
    removeCountyZipLayers,
    COUNTY_HIT_ID,
} = useChoropleth();

const featureCache = createMapFeatureCache();

let filterEpoch = 0;
let loadAbort = new AbortController();
let moveendTimer: ReturnType<typeof setTimeout> | null = null;
let loadChain: Promise<void> = Promise.resolve();
let drilledCountyId: number | null = null;
let countyInteractionsBound = false;

function isLegacyZipViewport(): boolean {
    return store.geoLevel === "zipcode";
}

function stripAllChoroplethLayers(map: mapboxgl.Map): void {
    unbindCountyInteractions(map);
    removeLegacyChoroplethLayer(map);
    removeCountyZipLayers(map);
}

function unbindCountyInteractions(map: mapboxgl.Map): void {
    if (!countyInteractionsBound) return;
    map.off("click", COUNTY_HIT_ID, onCountyHitClick);
    map.off("mouseenter", COUNTY_HIT_ID, onCountyHitEnter);
    map.off("mouseleave", COUNTY_HIT_ID, onCountyHitLeave);
    countyInteractionsBound = false;
}

function bindCountyInteractions(map: mapboxgl.Map): void {
    if (countyInteractionsBound) return;
    map.on("click", COUNTY_HIT_ID, onCountyHitClick);
    map.on("mouseenter", COUNTY_HIT_ID, onCountyHitEnter);
    map.on("mouseleave", COUNTY_HIT_ID, onCountyHitLeave);
    countyInteractionsBound = true;
}

function onCountyHitEnter(): void {
    const map = getMap();
    if (map) map.getCanvas().style.cursor = "pointer";
}

function onCountyHitLeave(): void {
    const map = getMap();
    if (map) map.getCanvas().style.cursor = "";
}

async function onCountyHitClick(e: mapboxgl.MapLayerMouseEvent): Promise<void> {
    if (isLegacyZipViewport()) return;
    const map = getMap();
    if (!map || !e.features?.length) return;

    const feat = e.features[0];
    const id = feat.properties?.id as number | undefined;
    const geoType = feat.properties?.geo_type as string | undefined;
    if (id == null || geoType !== "county") return;

    const geometry = feat.geometry as Geometry | undefined;
    if (!geometry) return;

    drilledCountyId = id;
    const b = boundsFromGeometry(geometry);
    map.fitBounds(b, { padding: 48, duration: 900, maxZoom: 12 });

    const epochAtStart = filterEpoch;
    const signal = loadAbort.signal;
    store.isLoading = true;
    try {
        const zips = await fetchZipsInCounty({
            countyGeographyId: id,
            metric: store.metric,
            timeStart: store.timeStart,
            timeEnd: store.timeEnd,
            signal,
        });
        if (epochAtStart !== filterEpoch || signal.aborted) return;
        store.setZipGeojsonData(zips);
        if (!map.isStyleLoaded()) return;
        setZipLayerData(map, zips);
        updateCountyZipChoroplethColors(
            map,
            store.mode,
            store.currentPeriod,
            store.geojsonData,
            zips,
        );
    } catch (err) {
        if (signal.aborted || epochAtStart !== filterEpoch) return;
        console.error("Failed to load zip map data:", err);
    } finally {
        if (epochAtStart === filterEpoch) {
            store.isLoading = false;
        }
    }
}

function bumpFilterEpochFullReset(): void {
    filterEpoch += 1;
    featureCache.reset();
    store.clearGeojsonData();
    drilledCountyId = null;
    loadAbort.abort();
    loadAbort = new AbortController();

    const map = getMap();
    if (map?.isStyleLoaded()) {
        stripAllChoroplethLayers(map);
    }
}

function bumpFilterEpochKeepDrill(): void {
    filterEpoch += 1;
    loadAbort.abort();
    loadAbort = new AbortController();
}

/** Mapbox can finish `load` before `isStyleLoaded()` is reliable; always add layers after style is ready. */
function runWhenStyleReady(map: mapboxgl.Map, fn: () => void): void {
    if (map.isStyleLoaded()) {
        fn();
    } else {
        map.once("style.load", fn);
    }
}

function bumpLegacyViewportReset(): void {
    filterEpoch += 1;
    featureCache.reset();
    store.clearGeojsonData();
    loadAbort.abort();
    loadAbort = new AbortController();

    const map = getMap();
    if (map?.isStyleLoaded()) {
        const src = map.getSource(CHOROPLETH_SOURCE_ID) as mapboxgl.GeoJSONSource | undefined;
        if (src) {
            src.setData(emptyFc() as unknown as FeatureCollection);
        }
    }
}

async function loadCountyFirstData(preserveDrill: boolean): Promise<void> {
    const map = getMap();
    if (!map) return;

    const epochAtStart = filterEpoch;
    const signal = loadAbort.signal;

    if (!preserveDrill) {
        store.clearZipGeojsonData();
        drilledCountyId = null;
    } else {
        store.setZipGeojsonData(null);
        if (map.isStyleLoaded()) {
            setZipLayerData(map, emptyFc());
        }
    }

    store.isLoading = true;
    try {
        const counties = await fetchAllCountyMapData({
            metric: store.metric,
            timeStart: store.timeStart,
            timeEnd: store.timeEnd,
            signal,
        });
        if (epochAtStart !== filterEpoch || signal.aborted) return;

        store.setCountyGeojsonData(counties);

        runWhenStyleReady(map, () => {
            if (epochAtStart !== filterEpoch || signal.aborted) return;

            try {
                const zipFc = store.zipGeojsonData ?? emptyFc();
                ensureCountyZipLayers(map, counties, zipFc);
                bindCountyInteractions(map);
                updateCountyZipChoroplethColors(
                    map,
                    store.mode,
                    store.currentPeriod,
                    counties,
                    store.zipGeojsonData,
                );

                if (preserveDrill && drilledCountyId != null) {
                    void (async () => {
                        const zips = await fetchZipsInCounty({
                            countyGeographyId: drilledCountyId,
                            metric: store.metric,
                            timeStart: store.timeStart,
                            timeEnd: store.timeEnd,
                            signal,
                        });
                        if (epochAtStart !== filterEpoch || signal.aborted) return;
                        store.setZipGeojsonData(zips);
                        runWhenStyleReady(map, () => {
                            if (epochAtStart !== filterEpoch || signal.aborted) return;
                            setZipLayerData(map, zips);
                            updateCountyZipChoroplethColors(
                                map,
                                store.mode,
                                store.currentPeriod,
                                store.geojsonData,
                                zips,
                            );
                        });
                    })();
                }
            } catch (layerErr) {
                console.error("County choropleth layer error:", layerErr);
            }
        });
    } catch (err) {
        if (signal.aborted || epochAtStart !== filterEpoch) return;
        console.error("Failed to load county map data:", err);
    } finally {
        if (epochAtStart === filterEpoch) {
            store.isLoading = false;
        }
    }
}

async function loadMapDataOnce(): Promise<void> {
    const map = getMap();
    if (!map) return;

    const epochAtStart = filterEpoch;
    const signal = loadAbort.signal;

    const bounds = map.getBounds();
    if (!bounds) return;
    const boundsTuple: [number, number, number, number] = [
        bounds.getWest(),
        bounds.getSouth(),
        bounds.getEast(),
        bounds.getNorth(),
    ];

    store.isLoading = true;
    try {
        let round = 0;
        while (round < MAX_FETCH_ROUNDS) {
            if (epochAtStart !== filterEpoch || signal.aborted) {
                return;
            }

            const excludeIds = featureCache.getLoadedIds();
            const data = await fetchMapData({
                metric: store.metric,
                geoType: store.effectiveGeoType,
                timeStart: store.timeStart,
                timeEnd: store.timeEnd,
                bounds: boundsTuple,
                zoom: map.getZoom(),
                excludeGeographyIds: excludeIds,
                signal,
            });

            if (epochAtStart !== filterEpoch || signal.aborted) {
                return;
            }

            featureCache.mergeIncoming(data.features);
            featureCache.evict(boundsTuple);

            const merged = featureCache.toCollection();
            store.setGeojsonData(merged);
            addLegacyChoroplethLayer(map, merged);
            updateLegacyChoroplethColors(map, store.mode, store.currentPeriod, merged);

            round += 1;
            if (data.features.length < MAX_FEATURES_PER_REQUEST) {
                break;
            }
        }
    } catch (err) {
        if (signal.aborted || epochAtStart !== filterEpoch) {
            return;
        }
        console.error("Failed to load map data:", err);
    } finally {
        if (epochAtStart === filterEpoch) {
            store.isLoading = false;
        }
    }
}

function enqueueCountyLoad(preserveDrill: boolean): void {
    loadChain = loadChain
        .then(() => loadCountyFirstData(preserveDrill))
        .catch((err) => {
            console.error("County load chain error:", err);
        });
}

function enqueueLoad(): void {
    loadChain = loadChain.then(() => loadMapDataOnce()).catch(() => {});
}

function scheduleDebouncedLoad(): void {
    if (moveendTimer !== null) {
        clearTimeout(moveendTimer);
    }
    moveendTimer = setTimeout(() => {
        moveendTimer = null;
        if (!store.isPlaying) {
            enqueueLoad();
        }
    }, MOVEEND_DEBOUNCE_MS);
}

watch(
    () => store.currentPeriod,
    (period) => {
        const map = getMap();
        if (!map || !period) return;
        if (isLegacyZipViewport()) {
            updateLegacyChoroplethColors(map, store.mode, period, store.geojsonData);
        } else {
            updateCountyZipChoroplethColors(
                map,
                store.mode,
                period,
                store.geojsonData,
                store.zipGeojsonData,
            );
        }
    },
);

watch(
    () => store.mode,
    () => {
        const map = getMap();
        if (!map || !store.currentPeriod) return;
        if (isLegacyZipViewport()) {
            updateLegacyChoroplethColors(map, store.mode, store.currentPeriod, store.geojsonData);
        } else {
            updateCountyZipChoroplethColors(
                map,
                store.mode,
                store.currentPeriod,
                store.geojsonData,
                store.zipGeojsonData,
            );
        }
    },
);

watch(
    () => [store.metric, store.timeStart, store.timeEnd] as const,
    () => {
        if (isLegacyZipViewport()) {
            bumpLegacyViewportReset();
            const map = getMap();
            if (map?.loaded()) {
                enqueueLoad();
            }
            return;
        }
        bumpFilterEpochKeepDrill();
        const map = getMap();
        if (map?.loaded()) {
            enqueueCountyLoad(true);
        }
    },
);

watch(
    () => store.geoLevel,
    () => {
        bumpFilterEpochFullReset();
        const map = getMap();
        if (!map?.loaded()) return;
        if (isLegacyZipViewport()) {
            enqueueLoad();
        } else {
            enqueueCountyLoad(false);
        }
    },
);

onMounted(() => {
    if (!mapContainer.value) return;

    const map = initMap(mapContainer.value);

    map.on("load", () => {
        if (isLegacyZipViewport()) {
            enqueueLoad();
        } else {
            enqueueCountyLoad(false);
        }
    });

    map.on("moveend", () => {
        if (store.isPlaying) return;
        if (isLegacyZipViewport()) {
            scheduleDebouncedLoad();
        }
    });
});

onUnmounted(() => {
    if (moveendTimer !== null) {
        clearTimeout(moveendTimer);
        moveendTimer = null;
    }
    loadAbort.abort();
    destroyMap();
});
</script>

<style scoped>
.map-container {
    width: 100%;
    height: 100%;
    position: absolute;
    top: 0;
    left: 0;
}
</style>
