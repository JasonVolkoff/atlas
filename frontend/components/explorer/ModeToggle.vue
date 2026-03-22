<template>
    <div class="mode-toggle">
        <button
            :class="['mode-toggle__btn', { active: store.mode === 'growth' }]"
            @click="store.setMode('growth')"
        >
            Growth
        </button>
        <button
            :class="['mode-toggle__btn', { active: store.mode === 'price_level' }]"
            @click="store.setMode('price_level')"
        >
            Price Level
        </button>
    </div>
</template>

<script setup lang="ts">
const store = useExplorerStore();
</script>

<style scoped>
.mode-toggle {
    display: flex;
    border-radius: 6px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.15);
}

.mode-toggle__btn {
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 500;
    border: none;
    background: rgba(255, 255, 255, 0.05);
    color: #a3a3a3;
    cursor: pointer;
    transition: all 0.15s;
}

.mode-toggle__btn:hover {
    background: rgba(255, 255, 255, 0.1);
}

.mode-toggle__btn.active {
    background: rgba(102, 189, 99, 0.2);
    color: #66bd63;
}
</style>
