import mapboxgl from "mapbox-gl";

let mapInstance: mapboxgl.Map | null = null;

export function useMap() {
    const config = useRuntimeConfig();

    function initMap(container: string | HTMLElement): mapboxgl.Map {
        mapboxgl.accessToken = config.public.mapboxToken as string;

        const map = new mapboxgl.Map({
            container,
            style: "mapbox://styles/mapbox/dark-v11",
            // Start zoomed into a metro so initial zipcode query is fast.
            center: [-97.7431, 30.2672],
            zoom: 9,
            minZoom: 3,
            maxZoom: 18,
            projection: "mercator",
        });

        map.addControl(new mapboxgl.NavigationControl(), "top-right");

        mapInstance = map;
        return map;
    }

    function getMap(): mapboxgl.Map | null {
        return mapInstance;
    }

    function destroyMap(): void {
        if (mapInstance) {
            mapInstance.remove();
            mapInstance = null;
        }
    }

    return {
        initMap,
        getMap,
        destroyMap,
    };
}
