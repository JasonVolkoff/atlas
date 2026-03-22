import type { GeoJSONFeature, GeoJSONFeatureCollection } from "~/utils/api";

export const MAX_CACHED_FEATURES = 15_000;
export const BOUNDS_PADDING_RATIO = 0.15;

function coordsRingBBox(ring: number[][]): [number, number, number, number] | null {
    let west = Infinity;
    let south = Infinity;
    let east = -Infinity;
    let north = -Infinity;
    for (const pt of ring) {
        const lon = pt[0];
        const lat = pt[1];
        if (lon < west) west = lon;
        if (lat < south) south = lat;
        if (lon > east) east = lon;
        if (lat > north) north = lat;
    }
    if (!Number.isFinite(west)) {
        return null;
    }
    return [west, south, east, north];
}

function coordsPolygonBBox(coordinates: number[][][]): [number, number, number, number] | null {
    let west = Infinity;
    let south = Infinity;
    let east = -Infinity;
    let north = -Infinity;
    for (const ring of coordinates) {
        const bb = coordsRingBBox(ring);
        if (!bb) continue;
        const [w, s, e, n] = bb;
        if (w < west) west = w;
        if (s < south) south = s;
        if (e > east) east = e;
        if (n > north) north = n;
    }
    if (!Number.isFinite(west)) {
        return null;
    }
    return [west, south, east, north];
}

function geometryBBox(geometry: GeoJSON.Geometry): [number, number, number, number] | null {
    if (geometry.type === "Polygon") {
        return coordsPolygonBBox(geometry.coordinates as number[][][]);
    }
    if (geometry.type === "MultiPolygon") {
        let west = Infinity;
        let south = Infinity;
        let east = -Infinity;
        let north = -Infinity;
        for (const poly of geometry.coordinates as number[][][][]) {
            const bb = coordsPolygonBBox(poly);
            if (!bb) continue;
            const [w, s, e, n] = bb;
            if (w < west) west = w;
            if (s < south) south = s;
            if (e > east) east = e;
            if (n > north) north = n;
        }
        if (!Number.isFinite(west)) {
            return null;
        }
        return [west, south, east, north];
    }
    return null;
}

function expandBounds(
    bounds: [number, number, number, number],
    ratio: number,
): [number, number, number, number] {
    const [west, south, east, north] = bounds;
    const width = east - west;
    const height = north - south;
    const padW = width * ratio;
    const padH = height * ratio;
    return [west - padW, south - padH, east + padW, north + padH];
}

function bboxesIntersect(
    a: [number, number, number, number],
    b: [number, number, number, number],
): boolean {
    const [aw, as_, ae, an] = a;
    const [bw, bs, be, bn] = b;
    return !(ae < bw || aw > be || an < bs || as_ > bn);
}

export function createMapFeatureCache() {
    const features = new Map<number, GeoJSONFeature>();
    const lastSeen = new Map<number, number>();
    let tick = 0;

    function reset(): void {
        features.clear();
        lastSeen.clear();
        tick = 0;
    }

    function mergeIncoming(incoming: GeoJSONFeature[]): void {
        tick += 1;
        const t = tick;
        for (const feature of incoming) {
            const id = feature.properties.id;
            features.set(id, feature);
            lastSeen.set(id, t);
        }
    }

    function evict(viewBounds: [number, number, number, number]): void {
        const padded = expandBounds(viewBounds, BOUNDS_PADDING_RATIO);
        const outside: number[] = [];
        for (const [id, feature] of features) {
            const bb = geometryBBox(feature.geometry);
            if (!bb || !bboxesIntersect(bb, padded)) {
                outside.push(id);
            }
        }
        for (const id of outside) {
            features.delete(id);
            lastSeen.delete(id);
        }

        if (features.size <= MAX_CACHED_FEATURES) {
            return;
        }

        const ranked = [...features.keys()].map((id) => ({
            id,
            seen: lastSeen.get(id) ?? 0,
        }));
        ranked.sort((x, y) => x.seen - y.seen);
        for (const { id } of ranked) {
            if (features.size <= MAX_CACHED_FEATURES) {
                break;
            }
            features.delete(id);
            lastSeen.delete(id);
        }
    }

    function toCollection(): GeoJSONFeatureCollection {
        return {
            type: "FeatureCollection",
            features: [...features.values()],
        };
    }

    function getLoadedIds(): number[] {
        return [...features.keys()];
    }

    return {
        reset,
        mergeIncoming,
        evict,
        toCollection,
        getLoadedIds,
        get size() {
            return features.size;
        },
    };
}

export type MapFeatureCache = ReturnType<typeof createMapFeatureCache>;
