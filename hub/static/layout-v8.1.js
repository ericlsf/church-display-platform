(() => {
  const shell = document.querySelector("[data-v8-shell]");
  if (!shell) return;
  const topbar = shell.querySelector(".v8-topbar");
  const context = shell.querySelector("[data-v8-page-context]");
  const crumbs = document.querySelector("[data-v8-breadcrumbs]");

  const enforce = () => {
    document.documentElement.style.setProperty("--v8-topbar-height", "58px");
    document.documentElement.style.setProperty("--v8-breadcrumb-height", "34px");
    if (topbar) {
      topbar.style.setProperty("top", "0", "important");
      topbar.style.setProperty("height", "58px", "important");
      topbar.style.setProperty("min-height", "58px", "important");
    }
    if (crumbs) {
      crumbs.style.setProperty("top", "58px", "important");
      crumbs.style.setProperty("height", "34px", "important");
      crumbs.style.setProperty("min-height", "34px", "important");
      crumbs.style.setProperty("z-index", "1995", "important");
    }
    document.querySelectorAll(".v8-main-content").forEach((main) => {
      main.style.setProperty("padding-top", "92px", "important");
    });
  };

  const simplifyTopbar = () => {
    if (!context) return;
    const heading = document.querySelector(".v8-main-content h1, main h1, h1");
    context.innerHTML = '<span class="v8-topbar-page-label"></span>';
    context.querySelector("span").textContent = heading?.textContent?.trim() || "";
  };

  const improveDisplayRows = () => {
    document.querySelectorAll('.v8-main-content label:has(input[type="checkbox"])')
      .forEach((label) => {
        if (label.dataset.v81DisplayRow === "true") return;
        const text = Array.from(label.childNodes)
          .filter((node) => node.nodeType === Node.TEXT_NODE)
          .map((node) => node.textContent)
          .join(" ").replace(/\s+/g, " ").trim();
        if (!text.includes("—")) return;
        const [name, ...rest] = text.split("—");
        const host = rest.join("—").trim();
        if (!name.trim() || !host) return;
        Array.from(label.childNodes).forEach((node) => {
          if (node.nodeType === Node.TEXT_NODE) node.remove();
        });
        const copy = document.createElement("span");
        copy.className = "v81-display-row-copy";
        const title = document.createElement("strong");
        title.textContent = name.trim();
        const sub = document.createElement("small");
        sub.textContent = host;
        copy.append(title, sub);
        label.append(copy);
        label.classList.add("v81-display-row");
        label.dataset.v81DisplayRow = "true";
      });
  };

  enforce();
  simplifyTopbar();
  improveDisplayRows();

  new MutationObserver(() => {
    enforce();
    improveDisplayRows();
  }).observe(document.body, {attributes: true, childList: true, subtree: true});

  window.addEventListener("resize", enforce);
})();