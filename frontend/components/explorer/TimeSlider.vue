<template>
    <div class="time-slider">
        <div class="time-slider__controls">
            <button class="time-slider__play-btn" @click="togglePlayback">
                {{ store.isPlaying ? "⏸" : "▶" }}
            </button>

            <select
                class="time-slider__speed"
                :value="store.playbackSpeed"
                @change="onSpeedChange"
            >
                <option :value="1">1x</option>
                <option :value="2">2x</option>
                <option :value="4">4x</option>
            </select>

            <select class="time-slider__step" :value="store.timeStep" @change="onStepChange">
                <option value="monthly">Monthly</option>
                <option value="quarterly">Quarterly</option>
                <option value="yearly">Yearly</option>
            </select>
        </div>

        <div class="time-slider__track-wrapper">
            <input
                type="range"
                class="time-slider__track"
                :min="0"
                :max="store.availablePeriods.length - 1"
                :value="store.currentPeriodIndex"
                @input="onSliderInput"
            />
            <div class="time-slider__label">
                {{ formatPeriod(store.currentPeriod) }}
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { useTimeLapse } from "~/composables/explorer/useTimeLapse";

const store = useExplorerStore();
const { togglePlayback, cleanup } = useTimeLapse();

function formatPeriod(period: string): string {
    if (!period) return "";
    const [year, month] = period.split("-");
    const monthNames = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ];
    return `${monthNames[parseInt(month, 10) - 1]} ${year}`;
}

function onSliderInput(event: Event): void {
    const target = event.target as HTMLInputElement;
    const idx = parseInt(target.value, 10);
    if (idx >= 0 && idx < store.availablePeriods.length) {
        store.stopPlayback();
        store.setCurrentPeriod(store.availablePeriods[idx]);
    }
}

function onSpeedChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    store.setPlaybackSpeed(Number(target.value));
}

function onStepChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    store.setTimeStep(target.value as "monthly" | "quarterly" | "yearly");
}

onUnmounted(() => {
    cleanup();
});
</script>

<style scoped>
.time-slider {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: rgba(10, 10, 10, 0.9);
    backdrop-filter: blur(8px);
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding: 12px 24px;
    display: flex;
    align-items: center;
    gap: 16px;
    z-index: 100;
}

.time-slider__controls {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
}

.time-slider__play-btn {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    border: 1px solid rgba(255, 255, 255, 0.2);
    background: rgba(255, 255, 255, 0.05);
    color: #e5e5e5;
    font-size: 14px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.15s;
}

.time-slider__play-btn:hover {
    background: rgba(255, 255, 255, 0.15);
}

.time-slider__speed,
.time-slider__step {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    color: #e5e5e5;
    padding: 4px 8px;
    font-size: 12px;
    cursor: pointer;
}

.time-slider__track-wrapper {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.time-slider__track {
    width: 100%;
    height: 4px;
    appearance: none;
    background: rgba(255, 255, 255, 0.15);
    border-radius: 2px;
    outline: none;
    cursor: pointer;
}

.time-slider__track::-webkit-slider-thumb {
    appearance: none;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: #66bd63;
    cursor: pointer;
}

.time-slider__label {
    text-align: center;
    font-size: 13px;
    font-weight: 600;
    color: #a3a3a3;
    letter-spacing: 0.5px;
}
</style>
