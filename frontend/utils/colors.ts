/**
 * Color scales for the choropleth map.
 *
 * Growth mode: diverging scale centered on 0%
 * Price Level mode: sequential scale from low to high
 */

/** Fills geographies with boundaries but no metric samples in-range. */
export const NO_DATA_FILL = "#3d3d3d";

export const GROWTH_COLOR_STOPS: [number, string][] = [
    [-50, "#d73027"],
    [-25, "#f46d43"],
    [-10, "#fdae61"],
    [-5, "#fee08b"],
    [0, "#d9d9d9"],
    [5, "#d9ef8b"],
    [10, "#a6d96a"],
    [25, "#66bd63"],
    [50, "#1a9850"],
];

export const PRICE_COLOR_STOPS: [number, string][] = [
    [0, "#f7fcf5"],
    [0.125, "#e5f5e0"],
    [0.25, "#c7e9c0"],
    [0.375, "#a1d99b"],
    [0.5, "#74c476"],
    [0.625, "#41ab5d"],
    [0.75, "#238b45"],
    [0.875, "#006d2c"],
    [1, "#00441b"],
];

function hasMetricDataExpression(): mapboxgl.Expression {
    return ["coalesce", ["get", "has_metric_data"], true] as mapboxgl.Expression;
}

export function buildGrowthExpression(periodKey: string): mapboxgl.Expression {
    const stops: (number | string)[] = [];
    for (const [value, color] of GROWTH_COLOR_STOPS) {
        stops.push(value, color);
    }

    const valueRamp: mapboxgl.Expression = [
        "interpolate",
        ["linear"],
        ["coalesce", ["get", periodKey, ["get", "growth"]], 0],
        ...stops,
    ] as mapboxgl.Expression;

    return [
        "case",
        ["==", hasMetricDataExpression(), false],
        NO_DATA_FILL,
        valueRamp,
    ] as mapboxgl.Expression;
}

export function buildPriceLevelExpression(
    periodKey: string,
    minValue: number,
    maxValue: number,
): mapboxgl.Expression {
    const range = maxValue - minValue || 1;
    const stops: (number | string)[] = [];
    for (const [fraction, color] of PRICE_COLOR_STOPS) {
        stops.push(minValue + fraction * range, color);
    }

    const valueRamp: mapboxgl.Expression = [
        "interpolate",
        ["linear"],
        ["coalesce", ["get", periodKey, ["get", "time_series"]], 0],
        ...stops,
    ] as mapboxgl.Expression;

    return [
        "case",
        ["==", hasMetricDataExpression(), false],
        NO_DATA_FILL,
        valueRamp,
    ] as mapboxgl.Expression;
}
