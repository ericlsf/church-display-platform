(() => {
  const shell = document.querySelector("[data-v8-shell]");
  if (!shell) return;

  document.documentElement.classList.add("v8-navigation-active");

  const body = document.body;
  const sidebar = shell.querySelector(".v8-sidebar");
  const collapseButton = shell.querySelector("[data-sidebar-collapse]");
  const mobileButton = shell.querySelector("[data-mobile-menu]");
  const mobileScrim = shell.querySelector("[data-mobile-scrim]");
  const userToggle = shell.querySelector("[data-user-menu-toggle]");
  const userMenu = shell.querySelector("[data-user-menu]");
  const commandButton = shell.querySelector("[data-command-button]");
  const breadcrumbs = document.querySelector("[data-v8-breadcrumbs]");
  const pageContext = shell.querySelector("[data-v8-page-context]");

  const collapseKey = "church-display-v8-sidebar-collapsed";
  const groupKey = "church-display-v8-open-group";

  const currentPath =
    window.location.pathname.replace(/\/+$/, "") || "/";

  const routeMap = [
    {prefix: "/fleet-dashboard", section: "dashboard", crumbs: ["Dashboard", "Overview"]},
    {prefix: "/fleet-map", section: "dashboard", crumbs: ["Dashboard", "Fleet Map"]},
    {prefix: "/display/", section: "fleet", crumbs: ["Fleet", "Displays", "Display Details"]},
    {prefix: "/displays", section: "fleet", crumbs: ["Fleet", "Displays"]},
    {prefix: "/groups", section: "fleet", crumbs: ["Fleet", "Groups"]},
    {prefix: "/display-profiles", section: "fleet", crumbs: ["Fleet", "Profiles"]},
    {prefix: "/content", section: "media", crumbs: ["Media", "Content Library"]},
    {prefix: "/media", section: "media", crumbs: ["Media", "Media"]},
    {prefix: "/bulk-operations", section: "operations", crumbs: ["Operations", "Bulk Operations"]},
    {prefix: "/fleet-operations", section: "operations", crumbs: ["Operations", "Fleet Operations"]},
    {prefix: "/jobs", section: "operations", crumbs: ["Operations", "Jobs"]},
    {prefix: "/alerts/rules", section: "administration", crumbs: ["Administration", "Alert Rules"]},
    {prefix: "/alerts", section: "operations", crumbs: ["Operations", "Alert Center"]},
    {prefix: "/history", section: "operations", crumbs: ["Operations", "History"]},
    {prefix: "/users", section: "administration", crumbs: ["Administration", "Users"]},
    {prefix: "/releases", section: "administration", crumbs: ["Administration", "Releases"]},
    {prefix: "/system", section: "administration", crumbs: ["Administration", "System"]},
    {prefix: "/setup", section: "administration", crumbs: ["Administration", "Settings"]},
  ];

  const route = routeMap.find((item) => {
    return (
      currentPath === item.prefix ||
      currentPath.startsWith(`${item.prefix}/`) ||
      (
        item.prefix.endsWith("/") &&
        currentPath.startsWith(item.prefix)
      )
    );
  }) || {
    section: "dashboard",
    crumbs: ["Dashboard"],
  };

  const hideLegacyNavigation = () => {
    document.querySelectorAll(
      ".v7-shell, .v7-breadcrumbs"
    ).forEach((element) => {
      element.classList.add("v8-old-shell-hidden");
    });

    const candidates = Array.from(
      document.querySelectorAll("body > header, body > nav, header, nav")
    );

    candidates.forEach((element) => {
      if (element.closest("[data-v8-shell]")) return;

      const text = (element.textContent || "")
        .replace(/\s+/g, " ")
        .trim();

      const linkCount = element.querySelectorAll("a").length;

      if (
        text.includes("Church Display") ||
        (
          linkCount >= 5 &&
          (
            text.includes("Fleet Operations") ||
            text.includes("Display Profiles")
          )
        )
      ) {
        element.classList.add("v8-legacy-navigation-hidden");
      }
    });
  };

  const locateMainContent = () => {
    const selectors = [
      ".v7-main-content",
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
        !element.closest("[data-v8-shell]") &&
        !element.closest(".v8-sidebar")
      ) {
        element.classList.remove("v7-main-content");
        element.classList.add("v8-main-content");
        return element;
      }
    }

    const fallback = Array.from(body.children).find((element) => {
      return (
        !element.matches(
          "[data-v8-shell], .v8-breadcrumbs, script, style"
        ) &&
        element.querySelectorAll(
          "h1, h2, section, table, form"
        ).length > 0
      );
    });

    if (fallback) {
      fallback.classList.add("v8-main-content");
    }

    return fallback || null;
  };

  const openGroup = (name, remember = true) => {
    shell.querySelectorAll("[data-nav-group]").forEach((group) => {
      const active = group.dataset.navGroup === name;
      group.hidden = !active;
    });

    shell.querySelectorAll("[data-nav-group-toggle]").forEach((button) => {
      const active =
        button.dataset.navGroupToggle === name;

      button.setAttribute(
        "aria-expanded",
        active ? "true" : "false"
      );

      button.closest(".v8-nav-group")
        ?.classList.toggle("open", active);
    });

    if (remember) {
      localStorage.setItem(groupKey, name);
    }
  };

  const setupGroups = () => {
    const remembered =
      localStorage.getItem(groupKey);

    const initial =
      route.section ||
      remembered ||
      "dashboard";

    openGroup(initial, false);

    shell.querySelectorAll(
      "[data-nav-group-toggle]"
    ).forEach((button) => {
      button.addEventListener("click", () => {
        const name =
          button.dataset.navGroupToggle;

        const expanded =
          button.getAttribute("aria-expanded") === "true";

        if (expanded) {
          button.setAttribute(
            "aria-expanded",
            "false"
          );

          const group = shell.querySelector(
            `[data-nav-group="${name}"]`
          );

          if (group) group.hidden = true;

          button.closest(".v8-nav-group")
            ?.classList.remove("open");

          return;
        }

        openGroup(name);
      });
    });
  };

  const markActiveRoute = () => {
    shell.querySelectorAll("[data-v8-route]").forEach((link) => {
      const target =
        (link.dataset.v8Route || "")
          .replace(/\/+$/, "");

      const active =
        currentPath === target ||
        currentPath.startsWith(`${target}/`);

      link.classList.toggle(
        "active",
        Boolean(active)
      );
    });
  };

  const buildBreadcrumbs = () => {
    if (!breadcrumbs) return;

    let labels = [...route.crumbs];

    const heading = document.querySelector(
      ".v8-main-content h1, main h1, .content h1, h1"
    );

    if (heading) {
      const title = heading.textContent.trim();

      if (
        title &&
        labels[labels.length - 1] !== title
      ) {
        labels.push(title);
      }

      if (pageContext) {
        pageContext.querySelector("strong").textContent =
          title || labels[labels.length - 1];

        pageContext.querySelector("span").textContent =
          labels.slice(0, -1).join(" / ");
      }
    }

    breadcrumbs.innerHTML = labels
      .map((label, index) => {
        const last =
          index === labels.length - 1;

        return `
          <span class="${last ? "current" : ""}">
            ${label.replace(/[&<>"']/g, "")}
          </span>
          ${
            last
              ? ""
              : '<span class="separator">›</span>'
          }
        `;
      })
      .join("");
  };

  const setCollapsed = (collapsed) => {
    body.classList.toggle(
      "v8-sidebar-collapsed",
      collapsed
    );

    localStorage.setItem(
      collapseKey,
      collapsed ? "true" : "false"
    );

    if (collapseButton) {
      collapseButton.textContent =
        collapsed ? "›" : "‹";

      collapseButton.setAttribute(
        "aria-label",
        collapsed
          ? "Expand navigation"
          : "Collapse navigation"
      );
    }
  };

  const closeMobile = () => {
    body.classList.remove(
      "v8-mobile-nav-open"
    );

    if (mobileScrim) {
      mobileScrim.hidden = true;
    }
  };

  const loadNotificationCount = async () => {
    const badge = shell.querySelector(
      "[data-notification-count]"
    );

    if (!badge) return;

    try {
      const response = await fetch(
        "/notifications/summary",
        {
          credentials: "same-origin",
          cache: "no-store",
        }
      );

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
      badge.textContent =
        count > 99 ? "99+" : String(count);
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
    localStorage.getItem(collapseKey) === "true"
  );

  collapseButton?.addEventListener(
    "click",
    () => {
      setCollapsed(
        !body.classList.contains(
          "v8-sidebar-collapsed"
        )
      );
    }
  );

  mobileButton?.addEventListener(
    "click",
    () => {
      body.classList.toggle(
        "v8-mobile-nav-open"
      );

      if (mobileScrim) {
        mobileScrim.hidden =
          !body.classList.contains(
            "v8-mobile-nav-open"
          );
      }
    }
  );

  mobileScrim?.addEventListener(
    "click",
    closeMobile
  );

  sidebar?.querySelectorAll("a").forEach((link) => {
    link.addEventListener(
      "click",
      closeMobile
    );
  });

  userToggle?.addEventListener(
    "click",
    (event) => {
      event.stopPropagation();

      const open = !userMenu.hidden;
      userMenu.hidden = open;

      userToggle.setAttribute(
        "aria-expanded",
        open ? "false" : "true"
      );
    }
  );

  document.addEventListener(
    "click",
    (event) => {
      if (
        userMenu &&
        !userMenu.hidden &&
        !event.target.closest(".v8-user-menu")
      ) {
        userMenu.hidden = true;

        userToggle?.setAttribute(
          "aria-expanded",
          "false"
        );
      }
    }
  );

  commandButton?.addEventListener(
    "click",
    () => {
      document.dispatchEvent(
        new KeyboardEvent(
          "keydown",
          {
            key: "k",
            code: "KeyK",
            ctrlKey: true,
            bubbles: true,
          }
        )
      );
    }
  );

  window.addEventListener(
    "keydown",
    (event) => {
      if (event.key === "Escape") {
        closeMobile();

        if (userMenu) {
          userMenu.hidden = true;

          userToggle?.setAttribute(
            "aria-expanded",
            "false"
          );
        }
      }
    }
  );

  loadNotificationCount();

  window.setInterval(
    loadNotificationCount,
    30000
  );
})();
