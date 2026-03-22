import { useApiBase } from "~/utils/api";

export interface GeographySearchResult {
    id: number;
    geo_type: string;
    geo_id: string;
    name: string;
    state_code: string;
    bbox: [number, number, number, number] | null;
}

export async function searchGeography(query: string): Promise<GeographySearchResult[]> {
    const base = useApiBase();
    const url = `${base}/api/v1/geography/search/?q=${encodeURIComponent(query)}`;
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Search request failed: ${response.status}`);
    }
    return response.json();
}
