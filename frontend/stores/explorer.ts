import { defineStore } from "pinia";
import type { GeoJSONFeatureCollection } from "~/utils/api";

export type VisualizationMode = "growth" | "price_level";
export type GeoLevel = "auto" | "county" | "zipcode";
export type TimeStep = "monthly" | "quarterly" | "yearly";

function monthKeysBetween(startStr: string, endStr: string): string[] {
    const start = new Date(`${startStr.slice(0, 7)}-01T12:00:00`);
    const end = new Date(`${endStr.slice(0, 7)}-01T12:00:00`);
    const out: string[] = [];
    const d = new Date(start);
    while (d <= end) {
        const y = d.getFullYear();
        const m = d.getMonth() + 1;
        out.push(`${y}-${String(m).padStart(2, "0")}`);
        d.setMonth(d.getMonth() + 1);
    }
    return out;
}

export interface ExplorerState {
    mode: VisualizationMode;
    geoLevel: GeoLevel;
    metric: string;
    timeStart: string;
    timeEnd: string;
    currentPeriod: string;
    isPlaying: boolean;
    playbackSpeed: number;
    timeStep: TimeStep;
    /** National county layer (or legacy viewport merged data when geo level = zipcode). */
    geojsonData: GeoJSONFeatureCollection | null;
    zipGeojsonData: GeoJSONFeatureCollection | null;
    availablePeriods: string[];
    isLoading: boolean;
}

export const useExplorerStore = defineStore("explorer", {
    state: (): ExplorerState => ({
        mode: "growth",
        geoLevel: "county",
        metric: "zhvi",
        timeStart: "2020-01-01",
        timeEnd: new Date().toISOString().slice(0, 10),
        currentPeriod: "",
        isPlaying: false,
        playbackSpeed: 1,
        timeStep: "monthly",
        geojsonData: null,
        zipGeojsonData: null,
        availablePeriods: [],
        isLoading: false,
    }),

    getters: {
        currentPeriodIndex(state): number {
            return state.availablePeriods.indexOf(state.currentPeriod);
        },

        effectiveGeoType(state): string {
            if (state.geoLevel !== "auto") {
                return state.geoLevel;
            }
            return "county";
        },
    },

    actions: {
        setMode(mode: VisualizationMode): void {
            this.mode = mode;
        },

        setCurrentPeriod(period: string): void {
            this.currentPeriod = period;
        },

        setGeoLevel(level: GeoLevel): void {
            this.geoLevel = level;
        },

        togglePlayback(): void {
            this.isPlaying = !this.isPlaying;
        },

        stopPlayback(): void {
            this.isPlaying = false;
        },

        setPlaybackSpeed(speed: number): void {
            this.playbackSpeed = speed;
        },

        setTimeStep(step: TimeStep): void {
            this.timeStep = step;
        },

        _recomputeAvailablePeriods(): void {
            const periodsSet = new Set<string>();
            const collections = [this.geojsonData, this.zipGeojsonData].filter(
                Boolean,
            ) as GeoJSONFeatureCollection[];
            for (const data of collections) {
                for (const feature of data.features) {
                    for (const key of Object.keys(feature.properties.time_series)) {
                        periodsSet.add(key);
                    }
                }
            }
            let periods = Array.from(periodsSet).sort();
            if (periods.length === 0) {
                periods = monthKeysBetween(this.timeStart, this.timeEnd);
            }
            this.availablePeriods = periods;
            const valid = new Set(periods);
            if (periods.length > 0 && (!this.currentPeriod || !valid.has(this.currentPeriod))) {
                this.currentPeriod = periods[periods.length - 1];
            }
        },

        /** Full reset (both layers). */
        setGeojsonData(data: GeoJSONFeatureCollection): void {
            this.geojsonData = data;
            this.zipGeojsonData = null;
            this._recomputeAvailablePeriods();
        },

        /** County national layer only; keeps zip drilldown if present. */
        setCountyGeojsonData(data: GeoJSONFeatureCollection): void {
            this.geojsonData = data;
            this._recomputeAvailablePeriods();
        },

        setZipGeojsonData(data: GeoJSONFeatureCollection | null): void {
            this.zipGeojsonData = data;
            this._recomputeAvailablePeriods();
        },

        clearGeojsonData(): void {
            this.geojsonData = null;
            this.zipGeojsonData = null;
            this.availablePeriods = [];
            this.currentPeriod = "";
        },

        clearZipGeojsonData(): void {
            this.zipGeojsonData = null;
            this._recomputeAvailablePeriods();
        },

        advancePeriod(): boolean {
            const idx = this.currentPeriodIndex;
            let step = 1;
            if (this.timeStep === "quarterly") step = 3;
            if (this.timeStep === "yearly") step = 12;

            const nextIdx = idx + step;
            if (nextIdx >= this.availablePeriods.length) {
                this.isPlaying = false;
                return false;
            }
            this.currentPeriod = this.availablePeriods[nextIdx];
            return true;
        },
    },
});
