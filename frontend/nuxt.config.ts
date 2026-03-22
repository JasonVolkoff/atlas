export default defineNuxtConfig({
    compatibilityDate: "2025-03-01",
    devtools: { enabled: true },

    modules: ["@pinia/nuxt"],

    routeRules: {
        "/": { ssr: false },
    },

    runtimeConfig: {
        public: {
            apiBaseUrl: process.env.NUXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
            mapboxToken: process.env.NUXT_PUBLIC_MAPBOX_TOKEN || "",
        },
    },

    css: ["~/assets/css/main.css"],

    app: {
        head: {
            title: "Atlas - Housing Intelligence Platform",
            meta: [
                { charset: "utf-8" },
                { name: "viewport", content: "width=device-width, initial-scale=1" },
                {
                    name: "description",
                    content: "Data-driven housing market intelligence for real estate investors.",
                },
            ],
            link: [
                {
                    rel: "stylesheet",
                    href: "https://api.mapbox.com/mapbox-gl-js/v3.9.4/mapbox-gl.css",
                },
            ],
        },
    },

    typescript: {
        strict: true,
    },
});
