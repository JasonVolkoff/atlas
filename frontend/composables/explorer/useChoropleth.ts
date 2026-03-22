import type mapboxgl from "mapbox-gl";
import type { GeoJSONFeature, GeoJSONFeatureCollection } from "~/utils/api";
import { buildGrowthExpression, buildPriceLevelExpression } from "~/utils/colors";

/** Legacy single-source viewport mode (geo level = zipcode). */
export const CHOROPLETH_SOURCE_ID = "atlas-choropleth";
const LEGACY_SOURCE_ID = CHOROPLETH_SOURCE_ID;
const LEGACY_FILL_ID = "atlas-choropleth-fill";
const LEGACY_OUTLINE_ID = "atlas-choropleth-outline";

export const COUNTY_CHOROPLETH_SOURCE_ID = "atlas-counties";
const COUNTY_FILL_ID = "atlas-counties-fill";
const COUNTY_OUTLINE_ID = "atlas-counties-outline";
/** Invisible top layer so county clicks work when zip polygons are shown above. */
const COUNTY_HIT_ID = "atlas-counties-hit";

export const ZIP_CHOROPLETH_SOURCE_ID = "atlas-zips";
const ZIP_FILL_ID = "atlas-zips-fill";
const ZIP_OUTLINE_ID = "atlas-zips-outline";

export const CHOROPLETH_FILL_OPACITY = 0.5;

/** Stroke width in px; kept high so boundaries read at national + metro zoom. */
const OUTLINE_LINE_WIDTH = 2.25;
const OUTLINE_LINE_OPACITY = 0.95;
/** Slightly lighter than fill so edges separate from dark-v11 land on zoomed-out views. */
const OUTLINE_LINE_COLOR = "#8a8a8a";

export function getChoroplethBeforeLayerId(map: mapboxgl.Map): string | undefined {
    if (!map.isStyleLoaded()) {
        return undefined;
    }
    const layers = map.getStyle().layers;
    if (!layers?.length) {
        return undefined;
    }

    for (const layer of layers) {
        const id = layer.id;
        if (
            id.startsWith("road-") ||
            id.includes("bridge") ||
            id.includes("tunnel") ||
            id.includes("aeroway")
        ) {
            if (map.getLayer(id)) {
                return id;
            }
        }
    }

    for (const layer of layers) {
        if (layer.type === "symbol") {
            const id = layer.id;
            if (map.getLayer(id)) {
                return id;
            }
        }
    }

    return undefined;
}

function featuresForPriceScale(
    county: GeoJSONFeatureCollection | null,
    zips: GeoJSONFeatureCollection | null,
): GeoJSONFeature[] {
    return [...(county?.features ?? []), ...(zips?.features ?? [])];
}

function paintExpression(
    mode: "growth" | "price_level",
    periodKey: string,
    scaleFeatures: GeoJSONFeature[],
): mapboxgl.Expression {
    if (mode === "growth") {
        return buildGrowthExpression(periodKey);
    }
    let min = Infinity;
    let max = -Infinity;
    for (const feature of scaleFeatures) {
        const val = feature.properties.time_series[periodKey];
        if (val != null) {
            if (val < min) min = val;
            if (val > max) max = val;
        }
    }
    if (!isFinite(min)) min = 0;
    if (!isFinite(max)) max = 1000000;
    return buildPriceLevelExpression(periodKey, min, max);
}

export function useChoropleth() {
    function addLegacyChoroplethLayer(map: mapboxgl.Map, data: GeoJSONFeatureCollection): void {
        if (map.getSource(LEGACY_SOURCE_ID)) {
            (map.getSource(LEGACY_SOURCE_ID) as mapboxgl.GeoJSONSource).setData(
                data as unknown as GeoJSON.FeatureCollection,
            );
            return;
        }

        map.addSource(LEGACY_SOURCE_ID, {
            type: "geojson",
            data: data as unknown as GeoJSON.FeatureCollection,
        });

        const beforeId = getChoroplethBeforeLayerId(map);

        map.addLayer(
            {
                id: LEGACY_FILL_ID,
                type: "fill",
                source: LEGACY_SOURCE_ID,
                paint: {
                    "fill-color": "#d9d9d9",
                    "fill-opacity": CHOROPLETH_FILL_OPACITY,
                },
            },
            beforeId,
        );

        map.addLayer(
            {
                id: LEGACY_OUTLINE_ID,
                type: "line",
                source: LEGACY_SOURCE_ID,
                paint: {
                    "line-color": OUTLINE_LINE_COLOR,
                    "line-width": OUTLINE_LINE_WIDTH,
                    "line-opacity": OUTLINE_LINE_OPACITY,
                },
            },
            beforeId,
        );
    }

    function ensureCountyZipLayers(
        map: mapboxgl.Map,
        countyData: GeoJSONFeatureCollection,
        zipData: GeoJSONFeatureCollection,
    ): void {
        const beforeId = getChoroplethBeforeLayerId(map);

        if (!map.getSource(COUNTY_CHOROPLETH_SOURCE_ID)) {
            map.addSource(COUNTY_CHOROPLETH_SOURCE_ID, {
                type: "geojson",
                data: countyData as unknown as GeoJSON.FeatureCollection,
            });
            map.addLayer(
                {
                    id: COUNTY_FILL_ID,
                    type: "fill",
                    source: COUNTY_CHOROPLETH_SOURCE_ID,
                    paint: {
                        "fill-color": "#d9d9d9",
                        "fill-opacity": CHOROPLETH_FILL_OPACITY,
                    },
                },
                beforeId,
            );
            map.addLayer(
                {
                    id: COUNTY_OUTLINE_ID,
                    type: "line",
                    source: COUNTY_CHOROPLETH_SOURCE_ID,
                    paint: {
                        "line-color": OUTLINE_LINE_COLOR,
                        "line-width": OUTLINE_LINE_WIDTH,
                        "line-opacity": OUTLINE_LINE_OPACITY,
                    },
                },
                beforeId,
            );
        } else {
            (map.getSource(COUNTY_CHOROPLETH_SOURCE_ID) as mapboxgl.GeoJSONSource).setData(
                countyData as unknown as GeoJSON.FeatureCollection,
            );
        }

        if (!map.getSource(ZIP_CHOROPLETH_SOURCE_ID)) {
            map.addSource(ZIP_CHOROPLETH_SOURCE_ID, {
                type: "geojson",
                data: zipData as unknown as GeoJSON.FeatureCollection,
            });
            map.addLayer(
                {
                    id: ZIP_FILL_ID,
                    type: "fill",
                    source: ZIP_CHOROPLETH_SOURCE_ID,
                    paint: {
                        "fill-color": "#d9d9d9",
                        "fill-opacity": CHOROPLETH_FILL_OPACITY,
                    },
                },
                beforeId,
            );
            map.addLayer(
                {
                    id: ZIP_OUTLINE_ID,
                    type: "line",
                    source: ZIP_CHOROPLETH_SOURCE_ID,
                    paint: {
                        "line-color": OUTLINE_LINE_COLOR,
                        "line-width": OUTLINE_LINE_WIDTH,
                        "line-opacity": OUTLINE_LINE_OPACITY,
                    },
                },
                beforeId,
            );
            map.addLayer(
                {
                    id: COUNTY_HIT_ID,
                    type: "fill",
                    source: COUNTY_CHOROPLETH_SOURCE_ID,
                    paint: {
                        "fill-color": "#000000",
                        "fill-opacity": 0,
                    },
                },
                beforeId,
            );
        } else {
            (map.getSource(ZIP_CHOROPLETH_SOURCE_ID) as mapboxgl.GeoJSONSource).setData(
                zipData as unknown as GeoJSON.FeatureCollection,
            );
        }
    }

    function setZipLayerData(map: mapboxgl.Map, zipData: GeoJSONFeatureCollection): void {
        const src = map.getSource(ZIP_CHOROPLETH_SOURCE_ID) as mapboxgl.GeoJSONSource | undefined;
        if (src) {
            src.setData(zipData as unknown as GeoJSON.FeatureCollection);
        }
    }

    function updateLegacyChoroplethColors(
        map: mapboxgl.Map,
        mode: "growth" | "price_level",
        periodKey: string,
        data: GeoJSONFeatureCollection | null,
    ): void {
        if (!map.getLayer(LEGACY_FILL_ID)) return;
        const expr = paintExpression(mode, periodKey, data?.features ?? []);
        map.setPaintProperty(LEGACY_FILL_ID, "fill-color", expr);
    }

    function updateCountyZipChoroplethColors(
        map: mapboxgl.Map,
        mode: "growth" | "price_level",
        periodKey: string,
        county: GeoJSONFeatureCollection | null,
        zips: GeoJSONFeatureCollection | null,
    ): void {
        const scaleFeatures = featuresForPriceScale(county, zips);
        const expr = paintExpression(mode, periodKey, scaleFeatures);
        if (map.getLayer(COUNTY_FILL_ID)) {
            map.setPaintProperty(COUNTY_FILL_ID, "fill-color", expr);
        }
        if (map.getLayer(ZIP_FILL_ID)) {
            map.setPaintProperty(ZIP_FILL_ID, "fill-color", expr);
        }
    }

    function clearCountyZipSources(map: mapboxgl.Map): void {
        const empty: GeoJSON.FeatureCollection = {
            type: "FeatureCollection",
            features: [],
        };
        const countySrc = map.getSource(COUNTY_CHOROPLETH_SOURCE_ID) as
            | mapboxgl.GeoJSONSource
            | undefined;
        if (countySrc) {
            countySrc.setData(empty);
        }
        const zipSrc = map.getSource(ZIP_CHOROPLETH_SOURCE_ID) as
            | mapboxgl.GeoJSONSource
            | undefined;
        if (zipSrc) {
            zipSrc.setData(empty);
        }
    }

    function removeLegacyChoroplethLayer(map: mapboxgl.Map): void {
        if (map.getLayer(LEGACY_OUTLINE_ID)) map.removeLayer(LEGACY_OUTLINE_ID);
        if (map.getLayer(LEGACY_FILL_ID)) map.removeLayer(LEGACY_FILL_ID);
        if (map.getSource(LEGACY_SOURCE_ID)) map.removeSource(LEGACY_SOURCE_ID);
    }

    function removeCountyZipLayers(map: mapboxgl.Map): void {
        if (map.getLayer(COUNTY_HIT_ID)) map.removeLayer(COUNTY_HIT_ID);
        if (map.getLayer(ZIP_OUTLINE_ID)) map.removeLayer(ZIP_OUTLINE_ID);
        if (map.getLayer(ZIP_FILL_ID)) map.removeLayer(ZIP_FILL_ID);
        if (map.getLayer(COUNTY_OUTLINE_ID)) map.removeLayer(COUNTY_OUTLINE_ID);
        if (map.getLayer(COUNTY_FILL_ID)) map.removeLayer(COUNTY_FILL_ID);
        if (map.getSource(ZIP_CHOROPLETH_SOURCE_ID)) {
            map.removeSource(ZIP_CHOROPLETH_SOURCE_ID);
        }
        if (map.getSource(COUNTY_CHOROPLETH_SOURCE_ID)) {
            map.removeSource(COUNTY_CHOROPLETH_SOURCE_ID);
        }
    }

    return {
        addLegacyChoroplethLayer,
        ensureCountyZipLayers,
        setZipLayerData,
        updateLegacyChoroplethColors,
        updateCountyZipChoroplethColors,
        clearCountyZipSources,
        removeLegacyChoroplethLayer,
        removeCountyZipLayers,
        LEGACY_FILL_ID,
        COUNTY_HIT_ID,
    };
}
