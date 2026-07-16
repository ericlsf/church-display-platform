(() => {
  const form = document.querySelector("[data-bulk-operations-form]");
  if (!form) return;

  const selectAll = form.querySelector("[data-select-all]");
  const displayChecks = Array.from(
    form.querySelectorAll('input[name="display_ids"]')
  );
  const operation = form.querySelector("[data-operation]");
  const count = form.querySelector("[data-selected-count]");
  const optionPanels = Array.from(
    form.querySelectorAll("[data-option]")
  );

  const refreshCount = () => {
    const selected = displayChecks.filter(
      (checkbox) => checkbox.checked
    ).length;

    if (count) count.textContent = String(selected);

    if (selectAll) {
      selectAll.checked =
        selected > 0 &&
        selected === displayChecks.length;

      selectAll.indeterminate =
        selected > 0 &&
        selected < displayChecks.length;
    }
  };

  const refreshOptions = () => {
    const value = operation?.value || "";

    optionPanels.forEach((panel) => {
      panel.hidden = panel.dataset.option !== value;
    });
  };

  selectAll?.addEventListener("change", () => {
    displayChecks.forEach((checkbox) => {
      checkbox.checked = selectAll.checked;
    });
    refreshCount();
  });

  displayChecks.forEach((checkbox) => {
    checkbox.addEventListener("change", refreshCount);
  });

  operation?.addEventListener("change", refreshOptions);

  form.addEventListener("submit", (event) => {
    const selected = displayChecks.filter(
      (checkbox) => checkbox.checked
    ).length;

    if (!selected) {
      event.preventDefault();
      window.alert("Select at least one display.");
    }
  });

  refreshCount();
  refreshOptions();
})();
