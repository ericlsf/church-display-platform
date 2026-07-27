(() => {
  const editor = document.querySelector("[data-operator-editor]");
  if (!editor) return;
  const folderSelect = editor.querySelector("[data-folder-select]");
  const refreshFolder = editor.querySelector("[data-refresh-folder]");

  folderSelect?.addEventListener("change", () => {
    if (refreshFolder) refreshFolder.value = folderSelect.value;
    const url = new URL(window.location.href);
    url.searchParams.set("folder", folderSelect.value);
    window.location.href = url.toString();
  });


  const overlay = editor.querySelector('[name="overlay_text"]');
  const takeover = editor.querySelector('[name="takeover_text"]');
  overlay?.addEventListener("input", () => {
    editor.querySelector("[data-preview-overlay]").textContent =
      overlay.value || " ";
  });
  takeover?.addEventListener("input", () => {
    editor.querySelector("[data-preview-takeover]").textContent =
      takeover.value || "Find your seat";
  });

  const serviceList = editor.querySelector("[data-service-list]");
  editor.querySelector("[data-add-service]")?.addEventListener("click", () => {
    const row = document.createElement("div");
    row.className = "service-row";
    row.innerHTML = `<select name="service_day">${["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"].map(day => `<option>${day}</option>`).join("")}</select><input type="time" name="service_time" required><button type="button" data-remove-service>Remove</button>`;
    serviceList.appendChild(row);
  });
  serviceList?.addEventListener("click", event => {
    const remove = event.target.closest("[data-remove-service]");
    if (remove) remove.closest(".service-row")?.remove();
  });
})();
