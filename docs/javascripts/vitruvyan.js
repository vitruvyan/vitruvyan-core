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

  function computeLanguageLinks() {
    const { pathname, search, hash } = window.location;

    const suffix = `${search || ""}${hash || ""}`;

    // The simple-blog theme generates a single `search.html` at the site root.
    // Avoid generating a broken /it/... search URL.
    if (pathname.endsWith("/search.html") || pathname === "/search.html") {
      return {
        en: "/admin/" + suffix,
        it: "/it/admin/" + suffix,
        active: pathname.includes("/it/") ? "it" : "en",
      };
    }

    // Prefer the production routing scheme (/admin/ and /it/admin/).
    if (pathname.includes("/it/admin/")) {
      return {
        en: pathname.replace("/it/admin/", "/admin/") + suffix,
        it: pathname + suffix,
        active: "it",
      };
    }
    if (pathname.includes("/admin/")) {
      return {
        en: pathname + suffix,
        it: pathname.replace("/admin/", "/it/admin/") + suffix,
        active: "en",
      };
    }

    // Fallback for static/local routes (/docs/ and /it/docs/).
    if (pathname.startsWith("/it/")) {
      return {
        en: pathname.replace(/^\/it\//, "/") + suffix,
        it: pathname + suffix,
        active: "it",
      };
    }

    return {
      en: pathname + suffix,
      it: `/it${pathname}` + suffix,
      active: "en",
    };
  }

  function setupLanguageSwitch() {
    const navbar = document.querySelector("nav.navbar");
    if (!navbar) return;

    if (document.getElementById("kb-lang-switch")) return;

    const outerNav = navbar.querySelector("#navbarsMenu > ul.navbar-nav");
    if (!outerNav) return;

    const searchItem = outerNav.querySelector(".md-search-icon")?.closest("li.nav-item") || null;

    const { en, it, active } = computeLanguageLinks();

    const li = document.createElement("li");
    li.className = "nav-item kb-lang-switch";
    li.id = "kb-lang-switch";

    const enLink = document.createElement("a");
    enLink.className = `nav-link text-decoration-none kb-lang-switch__link${active === "en" ? " is-active" : ""}`;
    enLink.href = en;
    enLink.textContent = "EN";
    enLink.setAttribute("aria-label", "Switch language to English");

    const sep = document.createElement("span");
    sep.className = "kb-lang-switch__sep";
    sep.textContent = "/";
    sep.setAttribute("aria-hidden", "true");

    const itLink = document.createElement("a");
    itLink.className = `nav-link text-decoration-none kb-lang-switch__link${active === "it" ? " is-active" : ""}`;
    itLink.href = it;
    itLink.textContent = "IT";
    itLink.setAttribute("aria-label", "Cambia lingua in Italiano");

    li.appendChild(enLink);
    li.appendChild(sep);
    li.appendChild(itLink);

    if (searchItem) {
      outerNav.insertBefore(li, searchItem);
    } else {
      outerNav.appendChild(li);
    }
  }

  function fixSearchPageMenuLinks() {
    const { pathname } = window.location;
    if (!(pathname.endsWith("/search.html") || pathname === "/search.html")) return;

    // In the current i18n build, `search.html` can be rendered with `/it/...` hrefs.
    // Normalize them to the current context to avoid accidental language jumps.
    const navbar = document.querySelector("nav.navbar");
    if (!navbar) return;

    const inItalianContext = pathname.includes("/it/");
    const anchors = navbar.querySelectorAll("a[href]");
    anchors.forEach((a) => {
      const href = a.getAttribute("href") || "";

      // Normalize "./it/..." or "it/..." to "./..." when not in Italian context.
      if (!inItalianContext && (href.startsWith("./it/") || href.startsWith("it/"))) {
        const normalized = href.replace(/^\.?\/?it\//, "./");
        a.setAttribute("href", normalized);
      }
    });
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

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupLanguageSwitch, { once: true });
  } else {
    setupLanguageSwitch();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", fixSearchPageMenuLinks, { once: true });
  } else {
    fixSearchPageMenuLinks();
  }
})();
