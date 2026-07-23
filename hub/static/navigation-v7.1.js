(() => {
  const sidebar = document.querySelector(".v7-sidebar");
  const nav = document.querySelector(".v7-sidebar .v7-nav");

  if (!sidebar || !nav) return;

  const enforceVerticalLayout = () => {
    nav.style.setProperty(
      "display",
      "flex",
      "important"
    );
    nav.style.setProperty(
      "flex-direction",
      "column",
      "important"
    );
    nav.style.setProperty(
      "width",
      "100%",
      "important"
    );
    nav.style.setProperty(
      "overflow-x",
      "hidden",
      "important"
    );

    nav.querySelectorAll(
      ".v7-nav-group"
    ).forEach((group) => {
      group.style.setProperty(
        "display",
        "block",
        "important"
      );
      group.style.setProperty(
        "width",
        "100%",
        "important"
      );
    });

    nav.querySelectorAll(
      ".v7-nav-group-links"
    ).forEach((links) => {
      if (links.hidden) return;

      links.style.setProperty(
        "display",
        "grid",
        "important"
      );
      links.style.setProperty(
        "grid-template-columns",
        "minmax(0, 1fr)",
        "important"
      );
      links.style.setProperty(
        "width",
        "100%",
        "important"
      );
    });
  };

  enforceVerticalLayout();

  const observer = new MutationObserver(
    enforceVerticalLayout
  );

  observer.observe(nav, {
    attributes: true,
    subtree: true,
    attributeFilter: [
      "class",
      "style",
      "hidden",
    ],
  });

  window.addEventListener(
    "resize",
    enforceVerticalLayout
  );
})();
