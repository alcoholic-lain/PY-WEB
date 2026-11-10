(() => {
    const storageKey = "transconnect-theme";
    const root = document.documentElement;
    const systemTheme = window.matchMedia("(prefers-color-scheme: dark)");
    let userPreference = false;

    function readPreference() {
        try {
            const theme = window.localStorage.getItem(storageKey);
            return theme === "light" || theme === "dark" ? theme : null;
        } catch (error) {
            if (error.name !== "SecurityError") throw error;
            return null;
        }
    }

    function applyTheme(theme) {
        root.dataset.theme = theme;
        const dark = theme === "dark";
        const toggle = document.querySelector("[data-theme-toggle]");

        if (toggle) {
            toggle.setAttribute("aria-pressed", String(dark));
            toggle.setAttribute(
                "aria-label",
                `Activer le thème ${dark ? "clair" : "sombre"}`
            );
            toggle.querySelector("[data-theme-icon]").textContent = dark ? "☀" : "◐";
            toggle.querySelector("[data-theme-label]").textContent =
                `Mode ${dark ? "clair" : "sombre"}`;
        }

        document.querySelector('meta[name="theme-color"]').content =
            dark ? "#101c26" : "#102a43";
    }

    const preference = readPreference();
    userPreference = preference !== null;
    applyTheme(preference || (systemTheme.matches ? "dark" : "light"));

    systemTheme.addEventListener("change", (event) => {
        if (!userPreference) applyTheme(event.matches ? "dark" : "light");
    });

    document.addEventListener("DOMContentLoaded", () => {
        const toggle = document.querySelector("[data-theme-toggle]");
        if (!toggle) return;

        applyTheme(root.dataset.theme);
        toggle.addEventListener("click", () => {
            const theme = root.dataset.theme === "dark" ? "light" : "dark";
            userPreference = true;
            applyTheme(theme);

            try {
                window.localStorage.setItem(storageKey, theme);
            } catch (error) {
                if (error.name !== "SecurityError") throw error;
            }
        });
    });
})();
