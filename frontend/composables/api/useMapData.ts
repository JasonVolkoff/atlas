import type { GeoJSONFeatureCollection } from "~/utils/api";
import { useApiBase } from "~/utils/api";

/** Matches backend `housing_data_service.MAX_FEATURES`. */
export const MAX_FEATURES_PER_REQUEST = 500;

/** Use POST when exclude list is long to avoid URL limits. */
export const EXCLUDE_IDS_POST_THRESHOLD = 200;

export interface MapDataParams {
    metric: string;
    geoType: string;
    timeStart: string;
    timeEnd: string;
    bounds: [number, number, number, number];
    zoom: number;
    excludeGeographyIds: number[];
    signal?: AbortSignal;
}

export async function fetchMapData(params: MapDataParams): Promise<GeoJSONFeatureCollection> {
    const base = useApiBase();
    const boundsStr = params.bounds.join(",");
    const excludeIds = params.excludeGeographyIds;
    const usePost = excludeIds.length > EXCLUDE_IDS_POST_THRESHOLD;

    if (usePost) {
        const response = await fetch(`${base}/api/v1/housing/map-data/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                metric: params.metric,
                geo_type: params.geoType,
                time_start: params.timeStart,
                time_end: params.timeEnd,
                bounds: boundsStr,
                zoom: params.zoom,
                exclude_geography_ids: excludeIds,
            }),
            signal: params.signal,
        });
        const responseText = await response.text();
        if (!response.ok) {
            throw new Error(`Map data request failed: ${response.status}`);
        }
        return JSON.parse(responseText) as GeoJSONFeatureCollection;
    }

    const excludeParam =
        excludeIds.length > 0 ? `&exclude_geography_ids=${excludeIds.join(",")}` : "";
    const url =
        `${base}/api/v1/housing/map-data/` +
        `?metric=${encodeURIComponent(params.metric)}` +
        `&geo_type=${encodeURIComponent(params.geoType)}` +
        `&time_start=${encodeURIComponent(params.timeStart)}` +
        `&time_end=${encodeURIComponent(params.timeEnd)}` +
        `&bounds=${encodeURIComponent(boundsStr)}` +
        `&zoom=${params.zoom}` +
        excludeParam;

    const response = await fetch(url, { signal: params.signal });
    const responseText = await response.text();
    if (!response.ok) {
        throw new Error(`Map data request failed: ${response.status}`);
    }
    return JSON.parse(responseText) as GeoJSONFeatureCollection;
}

export interface CountyMapDataParams {
    metric: string;
    timeStart: string;
    timeEnd: string;
    signal?: AbortSignal;
}

export async function fetchAllCountyMapData(
    params: CountyMapDataParams,
): Promise<GeoJSONFeatureCollection> {
    const base = useApiBase();
    const url =
        `${base}/api/v1/housing/county-map-data/` +
        `?metric=${encodeURIComponent(params.metric)}` +
        `&time_start=${encodeURIComponent(params.timeStart)}` +
        `&time_end=${encodeURIComponent(params.timeEnd)}`;

    const response = await fetch(url, { signal: params.signal });
    const responseText = await response.text();
    if (!response.ok) {
        throw new Error(`County map data request failed: ${response.status}`);
    }
    return JSON.parse(responseText) as GeoJSONFeatureCollection;
}

export interface ZipsInCountyParams {
    countyGeographyId: number;
    metric: string;
    timeStart: string;
    timeEnd: string;
    signal?: AbortSignal;
}

export async function fetchZipsInCounty(
    params: ZipsInCountyParams,
): Promise<GeoJSONFeatureCollection> {
    const base = useApiBase();
    const url =
        `${base}/api/v1/housing/counties/${params.countyGeographyId}/zip-map-data/` +
        `?metric=${encodeURIComponent(params.metric)}` +
        `&time_start=${encodeURIComponent(params.timeStart)}` +
        `&time_end=${encodeURIComponent(params.timeEnd)}`;

    const response = await fetch(url, { signal: params.signal });
    const responseText = await response.text();
    if (!response.ok) {
        throw new Error(`Zip map data request failed: ${response.status}`);
    }
    return JSON.parse(responseText) as GeoJSONFeatureCollection;
}
