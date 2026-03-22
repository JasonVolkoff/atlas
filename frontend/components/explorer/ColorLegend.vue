<template>
    <div class="color-legend">
        <div class="color-legend__title">
            {{ store.mode === "growth" ? "Growth %" : "Home Value" }}
        </div>
        <div class="color-legend__bar">
            <div class="color-legend__gradient" :style="{ background: gradientCss }" />
        </div>
        <div class="color-legend__labels">
            <span>{{ minLabel }}</span>
            <span>{{ midLabel }}</span>
            <span>{{ maxLabel }}</span>
        </div>
        <div class="color-legend__nodata">
            <span class="color-legend__nodata-swatch" :style="{ background: NO_DATA_FILL }" />
            <span class="color-legend__nodata-label">No data</span>
        </div>
        <div v-if="store.mode === 'price_level'" class="color-legend__note">
            Showing range for visible area
        </div>
    </div>
</template>

<script setup lang="ts">
import { GROWTH_COLOR_STOPS, NO_DATA_FILL, PRICE_COLOR_STOPS } from "~/utils/colors";

const store = useExplorerStore();

const gradientCss = computed(() => {
    if (store.mode === "growth") {
        const colors = GROWTH_COLOR_STOPS.map(([, color]) => color).join(", ");
        return `linear-gradient(to right, ${colors})`;
    }
    const colors = PRICE_COLOR_STOPS.map(([, color]) => color).join(", ");
    return `linear-gradient(to right, ${colors})`;
});

const minLabel = computed(() => {
    if (store.mode === "growth") return "-50%";
    return "$0";
});

const midLabel = computed(() => {
    if (store.mode === "growth") return "0%";
    return "";
});

const maxLabel = computed(() => {
    if (store.mode === "growth") return "+50%";
    return "$1M+";
});
</script>

<style scoped>
.color-legend {
    position: fixed;
    bottom: 80px;
    right: 16px;
    background: rgba(10, 10, 10, 0.85);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 10px 14px;
    min-width: 180px;
    z-index: 100;
}

.color-legend__title {
    font-size: 11px;
    font-weight: 600;
    color: #a3a3a3;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
}

.color-legend__bar {
    height: 10px;
    border-radius: 3px;
    overflow: hidden;
}

.color-legend__gradient {
    width: 100%;
    height: 100%;
}

.color-legend__labels {
    display: flex;
    justify-content: space-between;
    font-size: 10px;
    color: #737373;
    margin-top: 4px;
}

.color-legend__nodata {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.color-legend__nodata-swatch {
    width: 18px;
    height: 10px;
    border-radius: 2px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    flex-shrink: 0;
}

.color-legend__nodata-label {
    font-size: 10px;
    color: #737373;
}

.color-legend__note {
    font-size: 9px;
    color: #525252;
    font-style: italic;
    margin-top: 4px;
}
</style>
