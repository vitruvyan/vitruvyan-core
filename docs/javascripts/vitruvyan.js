(() => {
  // Guard against double-inclusion (theme injects scripts in head + footer).
  if (window.__vitruvyan_kb_initialized) return;
  window.__vitruvyan_kb_initialized = true;

  function normalizeBaseUrl(baseUrl) {
    if (!baseUrl || typeof baseUrl !== "string") return ".";
    return baseUrl.replace(/\/+$/, "");
  }

  function ensureSiteNameLink() {
    const siteNameEl = document.getElementById("component-site-name");
    if (!siteNameEl) return;

    const baseUrl = normalizeBaseUrl(window.base_url);
    const homeHref = `${baseUrl}/docs/`;

    // If theme already renders a link, just ensure href points to home.
    if (siteNameEl.tagName.toLowerCase() === "a") {
      siteNameEl.setAttribute("href", homeHref);
      return;
    }

    // Replace the span with an anchor to make it clickable + accessible.
    const link = document.createElement("a");
    link.id = siteNameEl.id;
    link.className = siteNameEl.className;
    link.textContent = siteNameEl.textContent || "";
    link.href = homeHref;
    link.style.textTransform = siteNameEl.style.textTransform || "";
    link.setAttribute("aria-label", "Go to documentation home");

    siteNameEl.replaceWith(link);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", ensureSiteNameLink, { once: true });
  } else {
    ensureSiteNameLink();
  }

  function joinBase(baseUrl, path) {
    if (!path || typeof path !== "string") return baseUrl || ".";
    if (path.startsWith("/")) return path;
    const base = normalizeBaseUrl(baseUrl || ".");
    if (base.endsWith("/")) return `${base}${path}`;
    return `${base}/${path}`;
  }

  function setupSearchSuggest() {
    const input = document.getElementById("mkdocs-search-query");
    if (!input) return;

    if (document.getElementById("kb-search-suggest")) return;

    const suggest = document.createElement("div");
    suggest.id = "kb-search-suggest";
    suggest.className = "kb-search-suggest";
    suggest.setAttribute("role", "listbox");
    suggest.hidden = true;

    const list = document.createElement("ul");
    list.className = "kb-search-suggest__list";
    suggest.appendChild(list);

    input.insertAdjacentElement("afterend", suggest);

    function render(results) {
      const q = (input.value || "").trim();
      if (!q || !Array.isArray(results) || results.length === 0) {
        suggest.hidden = true;
        list.replaceChildren();
        return;
      }

      list.replaceChildren();

      const max = 6;
      for (let i = 0; i < Math.min(max, results.length); i += 1) {
        const r = results[i] || {};
        const li = document.createElement("li");
        li.className = "kb-search-suggest__item";

        const a = document.createElement("a");
        a.className = "kb-search-suggest__link";
        a.href = joinBase(window.base_url, r.location || "");
        a.textContent = r.title || r.location || "Result";
        a.setAttribute("role", "option");

        li.appendChild(a);
        list.appendChild(li);
      }

      suggest.hidden = false;
    }

    // Monkey-patch MkDocs search renderer (defined in search/main.js).
    if (typeof window.displayResults === "function" && !window.__kb_displayResults_patched) {
      window.__kb_displayResults_patched = true;
      const original = window.displayResults;
      window.displayResults = function patchedDisplayResults(results) {
        try {
          render(results);
        } catch (_) {
          // Never break search.
        }
        return original(results);
      };
    }

    // Hide suggestions on blur (delay allows click).
    input.addEventListener("blur", () => {
      window.setTimeout(() => {
        suggest.hidden = true;
      }, 120);
    });

    input.addEventListener("focus", () => {
      // If results already rendered, show them again.
      if (list.children.length > 0) suggest.hidden = false;
    });

    // Esc to close.
    input.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        suggest.hidden = true;
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupSearchSuggest, { once: true });
  } else {
    setupSearchSuggest();
  }
})();
