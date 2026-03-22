export function useTimeLapse() {
    const store = useExplorerStore();
    let intervalId: ReturnType<typeof setInterval> | null = null;

    function getIntervalMs(): number {
        const baseMs = 500;
        return baseMs / store.playbackSpeed;
    }

    function startPlayback(): void {
        stopPlayback();
        store.isPlaying = true;

        intervalId = setInterval(() => {
            const advanced = store.advancePeriod();
            if (!advanced) {
                stopPlayback();
            }
        }, getIntervalMs());
    }

    function stopPlayback(): void {
        store.isPlaying = false;
        if (intervalId !== null) {
            clearInterval(intervalId);
            intervalId = null;
        }
    }

    function togglePlayback(): void {
        if (store.isPlaying) {
            stopPlayback();
        } else {
            startPlayback();
        }
    }

    function cleanup(): void {
        stopPlayback();
    }

    return {
        startPlayback,
        stopPlayback,
        togglePlayback,
        cleanup,
    };
}
