(() => {
  const editor = document.querySelector("[data-operator-editor]");
  if (!editor) return;
  const playlist = editor.querySelector("[data-playlist]");
  const orderField = editor.querySelector("[data-order-field]");
  const folderSelect = editor.querySelector("[data-folder-select]");
  const refreshFolder = editor.querySelector("[data-refresh-folder]");

  const syncOrder = () => {
    if (!playlist || !orderField) return;
    const cards = [...playlist.querySelectorAll("[data-path]")];
    orderField.value = cards.map(card => card.dataset.path).join("\n");
    cards.forEach((card, index) => {
      const number = card.querySelector(".order-number");
      if (number) number.textContent = String(index + 1);
    });
  };

  folderSelect?.addEventListener("change", () => {
    if (refreshFolder) refreshFolder.value = folderSelect.value;
    const url = new URL(window.location.href);
    url.searchParams.set("folder", folderSelect.value);
    window.location.href = url.toString();
  });

  playlist?.addEventListener("click", event => {
    const button = event.target.closest("[data-move]");
    if (!button) return;
    const card = button.closest("[data-path]");
    const direction = Number(button.dataset.move);
    if (direction < 0 && card.previousElementSibling) {
      playlist.insertBefore(card, card.previousElementSibling);
    } else if (direction > 0 && card.nextElementSibling) {
      playlist.insertBefore(card.nextElementSibling, card);
    }
    syncOrder();
  });

  let dragging = null;
  playlist?.addEventListener("dragstart", event => {
    dragging = event.target.closest("[data-path]");
    dragging?.classList.add("is-dragging");
  });
  playlist?.addEventListener("dragover", event => {
    event.preventDefault();
    const target = event.target.closest("[data-path]");
    if (!dragging || !target || target === dragging) return;
    const rect = target.getBoundingClientRect();
    playlist.insertBefore(
      dragging,
      event.clientY < rect.top + rect.height / 2
        ? target
        : target.nextElementSibling
    );
  });
  playlist?.addEventListener("dragend", () => {
    dragging?.classList.remove("is-dragging");
    dragging = null;
    syncOrder();
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
  syncOrder();
})();
