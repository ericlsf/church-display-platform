(() => {
  const list = document.querySelector("[data-alert-list]");
  const buttons = Array.from(document.querySelectorAll("[data-alert-filter]"));
  if (!list || !buttons.length) return;

  const applyFilter = (filter) => {
    list.querySelectorAll("[data-alert-severity]").forEach((row) => {
      row.hidden = filter !== "all" && row.dataset.alertSeverity !== filter;
    });
    buttons.forEach((button) => {
      button.classList.toggle("active", button.dataset.alertFilter === filter);
    });
  };

  buttons.forEach((button) => {
    button.addEventListener("click", () => applyFilter(button.dataset.alertFilter || "all"));
  });
})();
