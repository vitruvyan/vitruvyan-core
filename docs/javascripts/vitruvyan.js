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
    // Load legacy stylesheet only for Bootstrap-based pages.
    // Material already ships its own dedicated stylesheet and loading both
    // causes conflicting overrides (especially after auth redirects).
    const isBootstrapPage = Boolean(document.querySelector("nav.navbar"));
    if (!isBootstrapPage) return;

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

    const origin = window.location.origin || "https://kb.vitruvyan.com";
    const registerRedirect = encodeURIComponent(`${origin}/oauth2/callback`);

    return {
      login: `/oauth2/start?rd=${encodedRd}`,
      logout: `/oauth2/sign_out?rd=${encodeURIComponent(inItalianContext ? "/it/" : "/")}`,
      register:
        `https://auth.vitruvyan.com/realms/vitruvyan-core/protocol/openid-connect/registrations` +
        `?client_id=kb&response_type=code&scope=openid%20email%20profile&redirect_uri=${registerRedirect}`,
      profile: "https://auth.vitruvyan.com/auth/realms/vitruvyan-core/account/",
    };
  }

  async function detectAuthenticatedSession() {
    try {
      const response = await fetch("/oauth2/userinfo", {
        method: "GET",
        credentials: "include",
        cache: "no-store",
        redirect: "manual",
      });
      if (response.status === 200 || response.status === 202) return true;
      if (response.status === 401 || response.status === 403) return false;
    } catch (_) {
      // Fallback to cookie heuristic when auth endpoint isn't reachable.
    }

    const cookie = document.cookie || "";
    return (
      /(?:^|;\s*)(?:__Host-)?_oauth2_proxy=/.test(cookie) ||
      /(?:^|;\s*)oauth2_proxy=/.test(cookie) ||
      /(?:^|;\s*)(?:__Host-)?_vitruvyan_kb=/.test(cookie) ||
      /(?:^|;\s*)_vitruvyan_kb=/.test(cookie)
    );
  }

  async function fetchAuthenticatedUser() {
    try {
      const response = await fetch("/oauth2/userinfo", {
        method: "GET",
        credentials: "include",
        cache: "no-store",
      });
      if (!response.ok) return null;
      const data = await response.json();
      if (!data || typeof data !== "object") return null;
      return {
        email: data.email || "",
        name: data.name || data.preferred_username || "",
      };
    } catch (_) {
      return null;
    }
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

    const authLink = document.createElement("a");
    authLink.className = "nav-link text-decoration-none kb-auth-controls__link kb-auth-controls__link--login";
    authLink.href = login;
    authLink.textContent = "Sign in";
    authLink.setAttribute("aria-label", "Sign in");

    li.appendChild(authLink);

    const applyState = (isAuthenticated) => {
      authLink.href = isAuthenticated ? logout : login;
      authLink.textContent = isAuthenticated ? "Sign out" : "Sign in";
      authLink.setAttribute("aria-label", isAuthenticated ? "Sign out" : "Sign in");
      authLink.classList.toggle("kb-auth-controls__link--logout", isAuthenticated);
      authLink.classList.toggle("kb-auth-controls__link--login", !isAuthenticated);
    };

    detectAuthenticatedSession().then(applyState).catch(() => applyState(false));

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

    const { login, logout, register, profile } = computeAuthLinks();

    const container = document.createElement("div");
    container.id = "kb-auth-controls-material";
    container.className = "kb-auth-controls-material";
    container.dataset.open = "false";

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "kb-auth-controls-material__toggle";
    toggle.setAttribute("aria-haspopup", "menu");
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-label", "Account menu");
    toggle.textContent = "Account";

    const menu = document.createElement("div");
    menu.className = "kb-auth-controls-material__menu";
    menu.setAttribute("role", "menu");

    const header = document.createElement("div");
    header.className = "kb-auth-controls-material__header";
    header.textContent = "Guest";
    menu.appendChild(header);

    const actions = document.createElement("div");
    actions.className = "kb-auth-controls-material__actions";

    const primaryAction = document.createElement("a");
    primaryAction.className = "kb-auth-controls-material__item";
    primaryAction.href = login;
    primaryAction.textContent = "Login";
    primaryAction.setAttribute("role", "menuitem");

    const secondaryAction = document.createElement("a");
    secondaryAction.className = "kb-auth-controls-material__item";
    secondaryAction.href = register;
    secondaryAction.textContent = "Register";
    secondaryAction.setAttribute("role", "menuitem");
    secondaryAction.rel = "noopener";

    const dangerAction = document.createElement("a");
    dangerAction.className = "kb-auth-controls-material__item kb-auth-controls-material__item--danger";
    dangerAction.href = logout;
    dangerAction.textContent = "Sign out";
    dangerAction.setAttribute("role", "menuitem");

    actions.appendChild(primaryAction);
    actions.appendChild(secondaryAction);
    menu.appendChild(actions);

    container.appendChild(toggle);
    container.appendChild(menu);

    const setOpen = (open) => {
      container.dataset.open = open ? "true" : "false";
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    };

    toggle.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      setOpen(container.dataset.open !== "true");
    });

    document.addEventListener("click", () => setOpen(false));
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") setOpen(false);
    });
    menu.addEventListener("click", () => setOpen(false));

    const applyState = (isAuthenticated, user) => {
      actions.replaceChildren();
      if (isAuthenticated) {
        const displayName = (user?.email || user?.name || "Signed in").trim();
        header.textContent = displayName;
        toggle.textContent = "Account";

        const profileAction = document.createElement("a");
        profileAction.className = "kb-auth-controls-material__item";
        profileAction.href = profile;
        profileAction.textContent = "Profile settings";
        profileAction.setAttribute("role", "menuitem");
        profileAction.target = "_blank";
        profileAction.rel = "noopener";

        actions.appendChild(profileAction);
        actions.appendChild(dangerAction);
        return;
      }

      header.textContent = "Guest";
      toggle.textContent = "Sign in";
      actions.appendChild(primaryAction);
      actions.appendChild(secondaryAction);
    };

    Promise.all([detectAuthenticatedSession(), fetchAuthenticatedUser()])
      .then(([isAuthenticated, user]) => applyState(Boolean(isAuthenticated || user), user))
      .catch(() => applyState(false, null));

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

  function setupMaterialMegaMenu() {
    const tabs = document.querySelector(".md-tabs");
    const tabsList = tabs?.querySelector(".md-tabs__list");
    const primaryList =
      document.querySelector(".md-nav--primary > .md-nav__list") ||
      document.querySelector(".md-sidebar--primary .md-nav__list");
    if (!tabs || !tabsList || !primaryList) return;

    // Keep mega-menu typography aligned with the actual tab typography
    // from the active Material theme.
    const tabSample = tabsList.querySelector(":scope > .md-tabs__item > .md-tabs__link");
    if (tabSample) {
      const computed = window.getComputedStyle(tabSample);
      document.documentElement.style.setProperty("--kb-tabs-font-size", computed.fontSize);
      document.documentElement.style.setProperty("--kb-tabs-font-family", computed.fontFamily);
    }

    const normalize = (label) => (label || "").toLowerCase().replace(/\s+/g, " ").trim();
    const descriptionMap = [
      {
        match: /sacred orders/i,
        text: "Governance services: memory, audit, truth validation, archival persistence.",
      },
      {
        match: /oculus prime/i,
        text: "Edge runtime for offline-first execution, ingestion and local orchestration.",
      },
      {
        match: /synaptic conclave|cognitive bus/i,
        text: "Event bus for inter-service communication, streaming and observability.",
      },
    ];
    const resolveDescription = (label) => {
      const value = (label || "").trim();
      if (!value) return "";
      const found = descriptionMap.find((d) => d.match.test(value));
      return found ? found.text : "";
    };

    const textOf = (el) => ((el?.textContent || "").replace(/\s+/g, " ").trim());
    const sectionsMap = new Map();
    const topItems = primaryList.querySelectorAll(":scope > .md-nav__item");
    topItems.forEach((item) => {
      const topAnchor = item.querySelector(":scope > .md-nav__link[href]");
      const topLabel = item.querySelector(":scope > .md-nav__link");
      const title = textOf(topAnchor || topLabel);
      if (!title) return;

      const groups = [];
      const childItems = item.querySelectorAll(":scope > .md-nav > .md-nav__list > .md-nav__item");
      childItems.forEach((child) => {
        const childAnchor = child.querySelector(":scope > .md-nav__link[href]");
        const childLabel = child.querySelector(":scope > .md-nav__link");
        const childTitle = textOf(childLabel || childAnchor);
        const childHref = childAnchor?.getAttribute("href") || "";

        const links = [];
        const pushLink = (title, href) => {
          if (!title || !href || href.includes("#")) return;
          if (links.some((l) => l.href === href)) return;
          links.push({ title, href });
        };

        // Keep page-level entries.
        pushLink(childTitle, childHref);

        // Keep section children (and one extra nested level) but skip in-page anchors,
        // so we don't import full page TOCs into mega-menu.
        const grandItems = child.querySelectorAll(":scope > .md-nav > .md-nav__list > .md-nav__item");
        grandItems.forEach((grand) => {
          const grandAnchor = grand.querySelector(":scope > .md-nav__link[href]");
          const grandLabel = grand.querySelector(":scope > .md-nav__link");
          const grandTitle = textOf(grandLabel || grandAnchor);
          const grandHref = grandAnchor?.getAttribute("href") || "";
          pushLink(grandTitle, grandHref);

          const greatAnchors = grand.querySelectorAll(
            ":scope > .md-nav > .md-nav__list > .md-nav__item > .md-nav__link[href]"
          );
          greatAnchors.forEach((a) => {
            pushLink(textOf(a), a.getAttribute("href") || "");
          });
        });

        if (links.length > 0) {
          groups.push({
            heading: childTitle || links[0].title,
            links,
          });
        }
      });

      sectionsMap.set(normalize(title), {
        title,
        href: topAnchor?.getAttribute("href") || "",
        groups,
      });
    });

    let mega = document.getElementById("kb-mega-menu");
    if (!mega) {
      mega = document.createElement("section");
      mega.id = "kb-mega-menu";
      mega.className = "kb-mega-menu";
      mega.setAttribute("aria-label", "Section menu");
      mega.hidden = true;

      const inner = document.createElement("div");
      inner.className = "kb-mega-menu__inner md-grid";
      const title = document.createElement("div");
      title.className = "kb-mega-menu__title";
      const grid = document.createElement("div");
      grid.className = "kb-mega-menu__grid";

      inner.appendChild(title);
      inner.appendChild(grid);
      mega.appendChild(inner);
      tabs.insertAdjacentElement("afterend", mega);
    }

    const megaTitle = mega.querySelector(".kb-mega-menu__title");
    const megaGrid = mega.querySelector(".kb-mega-menu__grid");
    if (!megaTitle || !megaGrid) return;

    let openTab = null;

    const closeMega = () => {
      openTab?.classList.remove("kb-mega-tab--open");
      openTab = null;
      mega.hidden = true;
      mega.classList.remove("is-open");
    };

    const openMega = (tabItem, section) => {
      if (!section || section.groups.length === 0) return;

      if (openTab && openTab !== tabItem) {
        openTab.classList.remove("kb-mega-tab--open");
      }
      openTab = tabItem;
      openTab.classList.add("kb-mega-tab--open");

      megaTitle.textContent = section.title;
      megaGrid.replaceChildren();

      section.groups.forEach((group) => {
        const column = document.createElement("div");
        column.className = "kb-mega-menu__col";

        const heading = document.createElement("div");
        heading.className = "kb-mega-menu__heading";
        heading.textContent = group.heading;
        column.appendChild(heading);

        const headingDescription = resolveDescription(group.heading);
        if (headingDescription) {
          const p = document.createElement("p");
          p.className = "kb-mega-menu__desc";
          p.textContent = headingDescription;
          column.appendChild(p);
        }

        const list = document.createElement("ul");
        list.className = "kb-mega-menu__list";

        group.links.forEach((entry) => {
          const li = document.createElement("li");
          const a = document.createElement("a");
          a.className = "kb-mega-menu__link";
          a.href = entry.href;

          const label = document.createElement("span");
          label.className = "kb-mega-menu__link-label";
          label.textContent = entry.title;
          a.appendChild(label);

          li.appendChild(a);
          list.appendChild(li);
        });

        column.appendChild(list);
        megaGrid.appendChild(column);
      });

      mega.hidden = false;
      mega.classList.remove("is-open");
      window.requestAnimationFrame(() => {
        mega.classList.add("is-open");
      });
    };

    const isDesktop = () => window.matchMedia("(min-width: 76.25em)").matches;

    const tabItems = tabsList.querySelectorAll(":scope > .md-tabs__item");
    tabItems.forEach((tabItem) => {
      const tabLink = tabItem.querySelector(":scope > .md-tabs__link[href]");
      if (!tabLink) return;
      const label = normalize(tabLink.textContent || "");
      const section = sectionsMap.get(label);
      if (!section || section.groups.length === 0) return;

      tabItem.classList.add("kb-mega-tab");
      tabLink.setAttribute("aria-haspopup", "menu");

      tabLink.addEventListener("click", (event) => {
        if (!isDesktop()) return;
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        event.stopPropagation();

        if (openTab === tabItem) {
          closeMega();
          return;
        }
        openMega(tabItem, section);
      });
    });

    document.addEventListener("click", (event) => {
      if (!(event.target instanceof Element)) {
        closeMega();
        return;
      }
      if (tabs.contains(event.target) || mega.contains(event.target)) return;
      closeMega();
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") closeMega();
    });

    window.addEventListener("resize", () => {
      if (!isDesktop()) closeMega();
    });

    mega.addEventListener("click", (event) => {
      if (!(event.target instanceof Element)) return;
      if (event.target.closest("a.kb-mega-menu__link")) {
        closeMega();
      }
    });

    document.body.classList.add("kb-mega-enabled");
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
    document.addEventListener("DOMContentLoaded", setupMaterialMegaMenu, { once: true });
  } else {
    setupMaterialMegaMenu();
  }
})();
