(() => {
  // Guard against double-inclusion (theme injects scripts in head + footer).
  if (window.__vitruvyan_kb_initialized) return;
  window.__vitruvyan_kb_initialized = true;

  // Backward compatibility: old bookmarks ending with README.md
  // should resolve to MkDocs directory URLs.
  if (window.location.pathname.endsWith("/README.md")) {
    const target = window.location.pathname.replace(/\/README\.md$/, "/");
    window.location.replace(`${target}${window.location.search || ""}${window.location.hash || ""}`);
    return;
  }

  function normalizeBaseUrl(baseUrl) {
    if (!baseUrl || typeof baseUrl !== "string") return ".";
    return baseUrl.replace(/\/+$/, "");
  }

  function ensureCustomCssLoaded() {
    const hrefPattern = /docs\/stylesheets\/vitruvyan\.css(?:\?|$)/;
    const alreadyLoaded = Array.from(
      document.querySelectorAll('link[rel="stylesheet"][href]')
    ).some((el) => hrefPattern.test(el.getAttribute("href") || ""));
    if (alreadyLoaded) return;

    const baseUrl = normalizeBaseUrl(window.base_url);
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = `${baseUrl}/docs/stylesheets/vitruvyan.css`;
    document.head.appendChild(link);
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

  function removeBootstrapPrevNextControls() {
    const links = document.querySelectorAll(
      '.navbar a.nav-link[rel="next"], .navbar a.nav-link[rel="prev"]'
    );
    links.forEach((link) => {
      const item = link.closest("li.nav-item");
      if (item) {
        item.remove();
      } else {
        link.remove();
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener(
      "DOMContentLoaded",
      () => {
        ensureCustomCssLoaded();
        ensureSiteNameLink();
        removeBootstrapPrevNextControls();
      },
      { once: true }
    );
  } else {
    ensureCustomCssLoaded();
    ensureSiteNameLink();
    removeBootstrapPrevNextControls();
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

    // Search page routing
    if (pathname.endsWith("/search.html") || pathname === "/search.html") {
      if (pathname.includes("/admin/")) {
        return {
          en: "/admin/" + suffix,
          it: "/admin/it/" + suffix,
          active: pathname.includes("/admin/it/") ? "it" : "en",
        };
      }
      if (pathname.includes("/docs/")) {
        return {
          en: "/docs/" + suffix,
          it: "/docs/it/" + suffix,
          active: pathname.includes("/docs/it/") ? "it" : "en",
        };
      }
      return {
        en: "/" + suffix,
        it: "/it/" + suffix,
        active: pathname.includes("/it/") ? "it" : "en",
      };
    }

    // Admin KB routing (current): /admin/... and /admin/it/...
    if (pathname.includes("/admin/it/")) {
      return {
        en: pathname.replace("/admin/it/", "/admin/") + suffix,
        it: pathname + suffix,
        active: "it",
      };
    }
    if (pathname.includes("/admin/")) {
      return {
        en: pathname + suffix,
        it: pathname.replace("/admin/", "/admin/it/") + suffix,
        active: "en",
      };
    }

    // Public docs routing (current): /docs/... and /docs/it/...
    if (pathname.includes("/docs/it/")) {
      return {
        en: pathname.replace("/docs/it/", "/docs/") + suffix,
        it: pathname + suffix,
        active: "it",
      };
    }
    if (pathname.includes("/docs/")) {
      return {
        en: pathname + suffix,
        it: pathname.replace("/docs/", "/docs/it/") + suffix,
        active: "en",
      };
    }

    // Legacy routing fallback: /it/admin/... and /it/docs/...
    if (pathname.includes("/it/admin/")) {
      return {
        en: pathname.replace("/it/admin/", "/admin/") + suffix,
        it: pathname.replace("/it/admin/", "/admin/it/") + suffix,
        active: "it",
      };
    }
    if (pathname.includes("/it/docs/")) {
      return {
        en: pathname.replace("/it/docs/", "/docs/") + suffix,
        it: pathname.replace("/it/docs/", "/docs/it/") + suffix,
        active: "it",
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
    li.dataset.open = "false";

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "nav-link kb-lang-switch__toggle";
    toggle.setAttribute("aria-haspopup", "menu");
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-label", "Language menu");
    toggle.innerHTML = `<span class="kb-lang-switch__icon" aria-hidden="true">🌐</span><span>${active.toUpperCase()}</span>`;

    const menu = document.createElement("div");
    menu.className = "kb-lang-switch__menu";
    menu.setAttribute("role", "menu");

    const enLink = document.createElement("a");
    enLink.className = `kb-lang-switch__item${active === "en" ? " is-active" : ""}`;
    enLink.href = en;
    enLink.textContent = "English";
    enLink.setAttribute("role", "menuitem");

    const itLink = document.createElement("a");
    itLink.className = `kb-lang-switch__item${active === "it" ? " is-active" : ""}`;
    itLink.href = it;
    itLink.textContent = "Italiano";
    itLink.setAttribute("role", "menuitem");

    menu.appendChild(enLink);
    menu.appendChild(itLink);
    li.appendChild(toggle);
    li.appendChild(menu);

    const setOpen = (open) => {
      li.dataset.open = open ? "true" : "false";
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    };

    toggle.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      setOpen(li.dataset.open !== "true");
    });

    document.addEventListener("click", () => setOpen(false));
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") setOpen(false);
    });
    menu.addEventListener("click", () => setOpen(false));

    if (searchItem) {
      outerNav.insertBefore(li, searchItem);
    } else {
      outerNav.appendChild(li);
    }
  }

  function computeAuthLinks() {
    const { pathname, search, hash } = window.location;
    const suffix = `${search || ""}${hash || ""}`;

    const inItalianContext =
      pathname.startsWith("/it/") ||
      pathname.includes("/it/docs/") ||
      pathname.includes("/it/admin/") ||
      pathname.includes("/docs/it/") ||
      pathname.includes("/admin/it/");

    const defaultAfterLogin = inItalianContext ? "/docs/it/" : "/docs/";

    // If the user is on the public landing, send them to docs after login.
    const rd =
      pathname === "/" || pathname === "/it/" || pathname === "/index.html" || pathname === "/it/index.html"
        ? defaultAfterLogin
        : `${pathname}${suffix}`;

    const encodedRd = encodeURIComponent(rd);

    return {
      login: `/oauth2/start?rd=${encodedRd}`,
      logout: `/oauth2/sign_out?rd=${encodeURIComponent(inItalianContext ? "/it/" : "/")}`,
    };
  }

  function setupAuthControls() {
    const navbar = document.querySelector("nav.navbar");
    if (!navbar) return;

    if (document.getElementById("kb-auth-controls")) return;

    const outerNav = navbar.querySelector("#navbarsMenu > ul.navbar-nav");
    if (!outerNav) return;

    const searchItem = outerNav.querySelector(".md-search-icon")?.closest("li.nav-item") || null;

    const { login, logout } = computeAuthLinks();

    const li = document.createElement("li");
    li.className = "nav-item kb-auth-controls";
    li.id = "kb-auth-controls";

    const loginLink = document.createElement("a");
    loginLink.className = "nav-link text-decoration-none kb-auth-controls__link kb-auth-controls__link--login";
    loginLink.href = login;
    loginLink.textContent = "Sign in";
    loginLink.setAttribute("aria-label", "Sign in");

    const logoutLink = document.createElement("a");
    logoutLink.className = "nav-link text-decoration-none kb-auth-controls__link kb-auth-controls__link--logout";
    logoutLink.href = logout;
    logoutLink.textContent = "Sign out";
    logoutLink.setAttribute("aria-label", "Sign out");

    li.appendChild(loginLink);
    li.appendChild(logoutLink);

    if (searchItem) {
      outerNav.insertBefore(li, searchItem);
    } else {
      outerNav.appendChild(li);
    }
  }

  function setupMaterialAuthControls() {
    const headerInner = document.querySelector(".md-header__inner");
    if (!headerInner) return;
    if (document.getElementById("kb-auth-controls-material")) return;

    const { login, logout } = computeAuthLinks();

    const container = document.createElement("div");
    container.id = "kb-auth-controls-material";
    container.className = "kb-auth-controls-material";

    const loginLink = document.createElement("a");
    loginLink.className =
      "kb-auth-controls-material__link kb-auth-controls-material__link--login";
    loginLink.href = login;
    loginLink.textContent = "Sign in";
    loginLink.setAttribute("aria-label", "Sign in");

    const logoutLink = document.createElement("a");
    logoutLink.className =
      "kb-auth-controls-material__link kb-auth-controls-material__link--logout";
    logoutLink.href = logout;
    logoutLink.textContent = "Sign out";
    logoutLink.setAttribute("aria-label", "Sign out");

    container.appendChild(loginLink);
    container.appendChild(logoutLink);

    const searchComponent = headerInner.querySelector("[data-md-component='search']");
    if (searchComponent && searchComponent.parentNode === headerInner) {
      searchComponent.insertAdjacentElement("afterend", container);
      return;
    }

    headerInner.appendChild(container);
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

  function setupMaterialHorizontalSubnav() {
    const tabs = document.querySelector(".md-tabs");
    const primaryNav = document.querySelector(".md-nav--primary > .md-nav__list");
    if (!tabs || !primaryNav) return;

    const activeTopItem = primaryNav.querySelector(":scope > .md-nav__item--active");
    if (!activeTopItem) return;

    const childLinks = activeTopItem.querySelectorAll(
      ":scope > .md-nav > .md-nav__list > .md-nav__item > .md-nav__link[href]"
    );
    if (!childLinks || childLinks.length === 0) return;

    let subnav = document.getElementById("kb-subnav");
    if (!subnav) {
      subnav = document.createElement("nav");
      subnav.id = "kb-subnav";
      subnav.className = "kb-subnav";
      subnav.setAttribute("aria-label", "Section submenu");

      const inner = document.createElement("div");
      inner.className = "kb-subnav__inner";

      const list = document.createElement("ul");
      list.className = "kb-subnav__list";

      inner.appendChild(list);
      subnav.appendChild(inner);
      tabs.insertAdjacentElement("afterend", subnav);
    }

    const list = subnav.querySelector(".kb-subnav__list");
    if (!list) return;
    list.replaceChildren();

    const currentPath = window.location.pathname.replace(/\/+$/, "");

    childLinks.forEach((link) => {
      const href = link.getAttribute("href");
      const text = (link.textContent || "").trim();
      if (!href || !text) return;

      const li = document.createElement("li");
      li.className = "kb-subnav__item";

      const a = document.createElement("a");
      a.className = "kb-subnav__link";
      a.href = href;
      a.textContent = text;

      const linkUrl = new URL(href, window.location.href);
      const linkPath = linkUrl.pathname.replace(/\/+$/, "");
      if (linkPath === currentPath) {
        a.classList.add("is-active");
      }

      a.addEventListener("click", (event) => {
        const targetHref = a.getAttribute("href");
        if (!targetHref) return;
        event.preventDefault();
        subnav.classList.remove("is-open");
        window.setTimeout(() => {
          window.location.href = targetHref;
        }, 180);
      });

      li.appendChild(a);
      list.appendChild(li);
    });

    const hasItems = list.children.length > 0;
    subnav.hidden = !hasItems;
    if (!hasItems) return;

    subnav.classList.remove("is-open");
    window.requestAnimationFrame(() => {
      subnav.classList.add("is-open");
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
    document.addEventListener("DOMContentLoaded", setupAuthControls, { once: true });
  } else {
    setupAuthControls();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupMaterialAuthControls, { once: true });
  } else {
    setupMaterialAuthControls();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", fixSearchPageMenuLinks, { once: true });
  } else {
    fixSearchPageMenuLinks();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupMaterialHorizontalSubnav, { once: true });
  } else {
    setupMaterialHorizontalSubnav();
  }
})();
