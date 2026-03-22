<template>
    <div class="explorer">
        <ClientOnly>
            <ExplorerMapContainer />
        </ClientOnly>

        <div class="explorer__controls">
            <ExplorerModeToggle />
        </div>

        <div v-if="store.isLoading" class="explorer__loading">Loading data...</div>

        <ClientOnly>
            <ExplorerColorLegend />
            <ExplorerTimeSlider />
        </ClientOnly>
    </div>
</template>

<script setup lang="ts">
const store = useExplorerStore();

useHead({
    title: "Atlas - Housing Intelligence Platform",
});
</script>

<style scoped>
.explorer {
    position: relative;
    width: 100%;
    height: 100vh;
    overflow: hidden;
}

.explorer__controls {
    position: fixed;
    top: 16px;
    left: 16px;
    z-index: 100;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.explorer__loading {
    position: fixed;
    top: 16px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(10, 10, 10, 0.85);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 12px;
    color: #a3a3a3;
    z-index: 200;
}
</style>
