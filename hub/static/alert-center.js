(() => {
  const viewButtons = Array.from(
    document.querySelectorAll("[data-alert-view]")
  );
  const filterButtons = Array.from(
    document.querySelectorAll("[data-alert-filter]")
  );
  const panels = Array.from(
    document.querySelectorAll("[data-alert-panel]")
  );

  if (!panels.length) return;

  let currentView = "active";
  let currentFilter = "all";

  const render = () => {
    panels.forEach((panel) => {
      const visible =
        panel.dataset.alertPanel === currentView;

      panel.hidden = !visible;

      if (!visible) return;

      panel.querySelectorAll(
        "[data-alert-severity]"
      ).forEach((row) => {
        row.hidden =
          currentFilter !== "all" &&
          row.dataset.alertSeverity !== currentFilter;
      });
    });

    viewButtons.forEach((button) => {
      button.classList.toggle(
        "active",
        button.dataset.alertView === currentView
      );
    });

    filterButtons.forEach((button) => {
      button.classList.toggle(
        "active",
        button.dataset.alertFilter === currentFilter
      );
    });
  };

  viewButtons.forEach((button) => {
    button.addEventListener("click", () => {
      currentView =
        button.dataset.alertView || "active";
      render();
    });
  });

  filterButtons.forEach((button) => {
    button.addEventListener("click", () => {
      currentFilter =
        button.dataset.alertFilter || "all";
      render();
    });
  });

  render();
})();
