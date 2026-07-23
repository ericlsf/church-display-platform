(() => {
  const shell = document.querySelector("[data-v7-shell]");
  if (!shell) return;

  document.documentElement.classList.add("v7-navigation-active");

  const body = document.body;
  const sidebar = shell.querySelector(".v7-sidebar");
  const collapseButton = shell.querySelector("[data-sidebar-collapse]");
  const mobileButton = shell.querySelector("[data-mobile-menu]");
  const mobileScrim = shell.querySelector("[data-mobile-scrim]");
  const userToggle = shell.querySelector("[data-user-menu-toggle]");
  const userMenu = shell.querySelector("[data-user-menu]");
  const commandButton = shell.querySelector("[data-command-button]");
  const breadcrumbs = document.querySelector("[data-v7-breadcrumbs]");

  const storageKey = "church-display-v7-sidebar-collapsed";

  const hideLegacyNavigation = () => {
    const candidates = Array.from(
      document.querySelectorAll("body > header, body > nav, header, nav")
    );

    candidates.forEach((element) => {
      if (element.closest("[data-v7-shell]")) return;

      const text = (element.textContent || "").replace(/\s+/g, " ").trim();
      const linkCount = element.querySelectorAll("a").length;

      if (
        text.includes("Church Display") ||
        (
          linkCount >= 5 &&
          (
            text.includes("Fleet Operations") ||
            text.includes("Operations Center") ||
            text.includes("Display Profiles")
          )
        )
      ) {
        element.classList.add("v7-legacy-navigation-hidden");
      }
    });
  };

  const locateMainContent = () => {
    const selectors = [
      "main",
      ".content",
      ".page-content",
      ".main-content",
      "#content",
      "[role='main']",
    ];

    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (
        element &&
        !element.closest("[data-v7-shell]") &&
        !element.closest(".v7-sidebar")
      ) {
        element.classList.add("v7-main-content");
        return element;
      }
    }

    const directChildren = Array.from(body.children).filter((element) => {
      return (
        !element.matches("[data-v7-shell], script, style") &&
        !element.classList.contains("v7-breadcrumbs") &&
        !element.classList.contains("v7-legacy-navigation-hidden")
      );
    });

    const fallback = directChildren.find((element) => {
      return (
        element.querySelectorAll("h1, h2, section, table, form").length > 0
      );
    });

    if (fallback) fallback.classList.add("v7-main-content");
    return fallback || null;
  };

  const setCollapsed = (collapsed) => {
    body.classList.toggle("v7-sidebar-collapsed", collapsed);
    localStorage.setItem(storageKey, collapsed ? "true" : "false");

    if (collapseButton) {
      collapseButton.textContent = collapsed ? "›" : "‹";
      collapseButton.setAttribute(
        "aria-label",
        collapsed ? "Expand navigation" : "Collapse navigation"
      );
    }
  };

  const closeMobile = () => {
    body.classList.remove("v7-mobile-nav-open");
    if (mobileScrim) mobileScrim.hidden = true;
  };

  const routeLabels = [
    ["/fleet-dashboard", ["Dashboard", "Overview"]],
    ["/fleet-map", ["Dashboard", "Fleet Map"]],
    ["/display/", ["Fleet", "Displays", "Display Details"]],
    ["/displays", ["Fleet", "Displays"]],
    ["/groups", ["Fleet", "Groups"]],
    ["/display-profiles", ["Fleet", "Profiles"]],
    ["/content", ["Media", "Content Library"]],
    ["/media", ["Media", "Media"]],
    ["/bulk-operations", ["Operations", "Bulk Operations"]],
    ["/fleet-operations", ["Operations", "Fleet Operations"]],
    ["/jobs", ["Operations", "Jobs"]],
    ["/alerts/rules", ["Administration", "Alert Rules"]],
    ["/alerts", ["Operations", "Alert Center"]],
    ["/history", ["Operations", "History"]],
    ["/users", ["Administration", "Users"]],
    ["/releases", ["Administration", "Releases"]],
    ["/system", ["Administration", "System"]],
    ["/setup", ["Administration", "Settings"]],
  ];

  const currentPath = window.location.pathname.replace(/\/+$/, "") || "/";

  const markActiveRoute = () => {
    const links = Array.from(shell.querySelectorAll("[data-v7-route]"));

    links.forEach((link) => {
      const route = (link.dataset.v7Route || "").replace(/\/+$/, "");
      const active =
        route &&
        (
          currentPath === route ||
          currentPath.startsWith(`${route}/`)
        );

      link.classList.toggle("active", Boolean(active));

      if (active) {
        const group = link.closest("[data-nav-group]");
        if (group) group.hidden = false;
      }
    });
  };

  const buildBreadcrumbs = () => {
    if (!breadcrumbs) return;

    let labels = ["Dashboard"];

    for (const [prefix, values] of routeLabels) {
      if (
        currentPath === prefix ||
        currentPath.startsWith(`${prefix}/`)
      ) {
        labels = values;
        break;
      }
    }

    const pageHeading = document.querySelector(
      ".v7-main-content h1, main h1, .content h1, h1"
    );

    if (
      pageHeading &&
      labels[labels.length - 1] !== pageHeading.textContent.trim()
    ) {
      const heading = pageHeading.textContent.trim();
      if (heading) labels.push(heading);
    }

    breadcrumbs.innerHTML = labels.map((label, index) => {
      const last = index === labels.length - 1;
      return `
        <span class="${last ? "current" : ""}">
          ${label.replace(/[&<>"']/g, "")}
        </span>
        ${last ? "" : '<span class="separator">›</span>'}
      `;
    }).join("");
  };

  const setupGroups = () => {
    shell.querySelectorAll("[data-nav-group-toggle]").forEach((button) => {
      const name = button.dataset.navGroupToggle;
      const group = shell.querySelector(`[data-nav-group="${name}"]`);
      if (!group) return;

      button.addEventListener("click", () => {
        const expanded = button.getAttribute("aria-expanded") !== "false";
        button.setAttribute("aria-expanded", expanded ? "false" : "true");
        group.hidden = expanded;
      });
    });
  };

  const loadNotificationCount = async () => {
    const badge = shell.querySelector("[data-notification-count]");
    if (!badge) return;

    try {
      const response = await fetch("/notifications/summary", {
        credentials: "same-origin",
        cache: "no-store",
      });

      if (!response.ok) return;
      const data = await response.json();

      const count = Number(
        data.unread ??
        data.count ??
        data.total ??
        data.notifications ??
        0
      );

      badge.hidden = count <= 0;
      badge.textContent = count > 99 ? "99+" : String(count);
    } catch (_) {
      // Notification count is optional.
    }
  };

  hideLegacyNavigation();
  locateMainContent();
  setupGroups();
  markActiveRoute();
  buildBreadcrumbs();

  setCollapsed(
    localStorage.getItem(storageKey) === "true"
  );

  collapseButton?.addEventListener("click", () => {
    setCollapsed(!body.classList.contains("v7-sidebar-collapsed"));
  });

  mobileButton?.addEventListener("click", () => {
    body.classList.toggle("v7-mobile-nav-open");
    if (mobileScrim) {
      mobileScrim.hidden = !body.classList.contains("v7-mobile-nav-open");
    }
  });

  mobileScrim?.addEventListener("click", closeMobile);

  sidebar?.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", closeMobile);
  });

  userToggle?.addEventListener("click", (event) => {
    event.stopPropagation();
    const open = !userMenu.hidden;
    userMenu.hidden = open;
    userToggle.setAttribute("aria-expanded", open ? "false" : "true");
  });

  document.addEventListener("click", (event) => {
    if (
      userMenu &&
      !userMenu.hidden &&
      !event.target.closest(".v7-user-menu")
    ) {
      userMenu.hidden = true;
      userToggle?.setAttribute("aria-expanded", "false");
    }
  });

  commandButton?.addEventListener("click", () => {
    document.dispatchEvent(
      new KeyboardEvent("keydown", {
        key: "k",
        code: "KeyK",
        ctrlKey: true,
        bubbles: true,
      })
    );
  });

  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeMobile();

      if (userMenu) {
        userMenu.hidden = true;
        userToggle?.setAttribute("aria-expanded", "false");
      }
    }
  });

  loadNotificationCount();
  window.setInterval(loadNotificationCount, 30000);
})();
