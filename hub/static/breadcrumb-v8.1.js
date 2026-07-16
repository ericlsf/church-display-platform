(() => {
  const breadcrumbs = document.querySelector(
    "[data-v8-breadcrumbs]"
  );

  if (!breadcrumbs) return;

  const enforceBreadcrumbLayout = () => {
    breadcrumbs.style.setProperty(
      "height",
      "36px",
      "important"
    );
    breadcrumbs.style.setProperty(
      "min-height",
      "36px",
      "important"
    );
    breadcrumbs.style.setProperty(
      "display",
      "flex",
      "important"
    );
    breadcrumbs.style.setProperty(
      "align-items",
      "center",
      "important"
    );
    breadcrumbs.style.setProperty(
      "overflow",
      "visible",
      "important"
    );
    breadcrumbs.style.setProperty(
      "line-height",
      "1.2",
      "important"
    );
  };

  enforceBreadcrumbLayout();

  const observer = new MutationObserver(
    enforceBreadcrumbLayout
  );

  observer.observe(breadcrumbs, {
    attributes: true,
    childList: true,
    subtree: true,
  });
})();
