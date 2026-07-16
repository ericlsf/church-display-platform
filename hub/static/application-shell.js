(() => {
  const shell = document.querySelector("[data-app-shell]");
  if (!shell) return;
  const body = document.body;
  const path = window.location.pathname.replace(/\/+$/, "") || "/";
  const collapseKey = "church-display-shell-collapsed";
  const routes = [
    ["/fleet-dashboard","dashboard",["Dashboard","Overview"]], ["/fleet-map","dashboard",["Dashboard","Fleet Map"]],
    ["/display/","fleet",["Fleet","Displays","Display Details"]], ["/displays","fleet",["Fleet","Displays"]],
    ["/groups","fleet",["Fleet","Groups"]], ["/display-profiles","fleet",["Fleet","Profiles"]],
    ["/content","media",["Media","Content Library"]], ["/media","media",["Media","Media"]],
    ["/bulk-operations","operations",["Operations","Bulk Operations"]], ["/fleet-operations","operations",["Operations","Fleet Operations"]],
    ["/jobs","operations",["Operations","Jobs"]], ["/alerts/rules","administration",["Administration","Alert Rules"]],
    ["/alerts","operations",["Operations","Alert Center"]], ["/history","operations",["Operations","History"]],
    ["/users","administration",["Administration","Users"]], ["/releases","administration",["Administration","Releases"]],
    ["/system","administration",["Administration","System"]], ["/setup","administration",["Administration","Settings"]]
  ];
  const route = routes.find(([prefix]) => path === prefix || path.startsWith(`${prefix}/`) || (prefix.endsWith("/") && path.startsWith(prefix))) || ["/fleet-dashboard","dashboard",["Dashboard"]];

  const removeLegacyChrome = () => {
    document.querySelectorAll(".v7-shell,.v7-breadcrumbs,.v8-shell,.v8-breadcrumbs,[data-v7-shell],[data-v8-shell]").forEach((node) => node.remove());
    Array.from(document.body.children).forEach((node) => {
      if (node === shell || node.matches("script,style")) return;
      if (node.matches("header,nav")) { node.remove(); return; }
      const cls = String(node.className || "");
      if (/legacy|top-nav|main-nav|site-header|app-header|global-header/i.test(cls)) node.remove();
    });
    document.querySelectorAll("header,nav").forEach((node) => {
      if (node.closest("[data-app-shell]")) return;
      const text = (node.textContent || "").replace(/\s+/g," ").trim();
      if (text.includes("Fleet Operations") || text.includes("Operations Center") || text.includes("Display Profiles") || text.includes("Church Display")) node.remove();
    });
  };

  const locateMain = () => {
    for (const selector of ["main","[role='main']","#content",".main-content",".page-content",".content",".v8-main-content",".v7-main-content"]) {
      const node = document.querySelector(selector);
      if (node && !node.closest("[data-app-shell]")) {
        node.classList.remove("v7-main-content","v8-main-content");
        node.classList.add("app-main");
        return node;
      }
    }
    const node = Array.from(body.children).find((el) => el !== shell && !el.matches("script,style") && el.querySelector("h1,h2,section,form,table"));
    if (node) node.classList.add("app-main");
    return node || null;
  };

  const openSection = (name) => {
    shell.querySelectorAll("[data-shell-section-links]").forEach((links) => links.hidden = links.dataset.shellSectionLinks !== name);
    shell.querySelectorAll("[data-shell-section-toggle]").forEach((button) => {
      const active = button.dataset.shellSectionToggle === name;
      button.setAttribute("aria-expanded", active ? "true" : "false");
      button.closest(".app-nav-section")?.classList.toggle("open", active);
    });
  };

  const markRoute = () => shell.querySelectorAll("[data-shell-route]").forEach((link) => {
    const target = (link.dataset.shellRoute || "").replace(/\/+$/, "");
    link.classList.toggle("active", path === target || path.startsWith(`${target}/`));
  });

  const buildBreadcrumbs = (main) => {
    const container = shell.querySelector("[data-shell-breadcrumbs]");
    const pageLabel = shell.querySelector("[data-shell-page-label]");
    const labels = [...route[2]];
    const heading = main?.querySelector("h1") || document.querySelector("h1:not([data-app-shell] h1)");
    const headingText = heading?.textContent?.trim() || "";
    if (headingText && labels.at(-1) !== headingText) labels.push(headingText);
    if (pageLabel) pageLabel.textContent = headingText || labels.at(-1) || "";
    if (container) container.innerHTML = labels.map((label,index) => `<span class="${index===labels.length-1?"current":""}">${label.replace(/[&<>"']/g,"")}</span>${index===labels.length-1?"":'<span class="separator">›</span>'}`).join("");
  };

  const setCollapsed = (collapsed) => {
    body.classList.toggle("app-sidebar-collapsed", collapsed);
    localStorage.setItem(collapseKey, collapsed ? "true" : "false");
    const button = shell.querySelector("[data-shell-collapse]");
    if (button) button.textContent = collapsed ? "›" : "‹";
  };

  const closeMobile = () => {
    body.classList.remove("app-mobile-nav-open");
    const scrim = shell.querySelector("[data-shell-mobile-scrim]");
    if (scrim) scrim.hidden = true;
  };

  removeLegacyChrome();
  const main = locateMain();
  openSection(route[1]);
  markRoute();
  buildBreadcrumbs(main);
  setCollapsed(localStorage.getItem(collapseKey) === "true");

  shell.querySelectorAll("[data-shell-section-toggle]").forEach((button) => button.addEventListener("click", () => {
    const name = button.dataset.shellSectionToggle;
    const expanded = button.getAttribute("aria-expanded") === "true";
    if (expanded) {
      button.setAttribute("aria-expanded","false");
      const links = shell.querySelector(`[data-shell-section-links="${name}"]`);
      if (links) links.hidden = true;
      button.closest(".app-nav-section")?.classList.remove("open");
    } else openSection(name);
  }));

  shell.querySelector("[data-shell-collapse]")?.addEventListener("click", () => setCollapsed(!body.classList.contains("app-sidebar-collapsed")));
  shell.querySelector("[data-shell-mobile-menu]")?.addEventListener("click", () => {
    body.classList.toggle("app-mobile-nav-open");
    const scrim = shell.querySelector("[data-shell-mobile-scrim]");
    if (scrim) scrim.hidden = !body.classList.contains("app-mobile-nav-open");
  });
  shell.querySelector("[data-shell-mobile-scrim]")?.addEventListener("click", closeMobile);
  shell.querySelectorAll("a").forEach((link) => link.addEventListener("click", closeMobile));

  const userToggle = shell.querySelector("[data-shell-user-toggle]");
  const userMenu = shell.querySelector("[data-shell-user-menu]");
  userToggle?.addEventListener("click", (event) => { event.stopPropagation(); userMenu.hidden = !userMenu.hidden; userToggle.setAttribute("aria-expanded", userMenu.hidden ? "false" : "true"); });
  document.addEventListener("click", (event) => { if (!event.target.closest(".app-user-menu") && userMenu) { userMenu.hidden = true; userToggle?.setAttribute("aria-expanded","false"); } });
  shell.querySelector("[data-shell-command]")?.addEventListener("click", () => document.dispatchEvent(new KeyboardEvent("keydown", {key:"k",code:"KeyK",ctrlKey:true,bubbles:true})));

  const loadCount = async () => {
    const badge = shell.querySelector("[data-shell-notification-count]");
    if (!badge) return;
    try {
      const response = await fetch("/notifications/summary", {credentials:"same-origin",cache:"no-store"});
      if (!response.ok) return;
      const data = await response.json();
      const count = Number(data.unread ?? data.count ?? data.total ?? data.notifications ?? 0);
      badge.hidden = count <= 0;
      badge.textContent = count > 99 ? "99+" : String(count);
    } catch (_) {}
  };
  loadCount();
  window.setInterval(loadCount,30000);
  new MutationObserver(removeLegacyChrome).observe(body,{childList:true,subtree:true});
})();
