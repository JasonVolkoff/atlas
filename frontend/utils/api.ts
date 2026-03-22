export function useApiBase(): string {
    const config = useRuntimeConfig();
    return config.public.apiBaseUrl as string;
}

export interface GeoJSONFeature {
    type: "Feature";
    id: number;
    geometry: GeoJSON.Geometry;
    properties: {
        id: number;
        name: string;
        geo_type: string;
        geo_id: string;
        state_code: string;
        time_series: Record<string, number>;
        growth: Record<string, number | null>;
        /** When false, map uses NO_DATA_FILL. Omitted treated as true (legacy). */
        has_metric_data?: boolean;
    };
}

export interface GeoJSONFeatureCollection {
    type: "FeatureCollection";
    features: GeoJSONFeature[];
}
