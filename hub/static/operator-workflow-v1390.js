(() => {
  const editor = document.querySelector("[data-operator-editor]");
  if (!editor) return;
  const playlist = editor.querySelector("[data-playlist]");
  const orderField = editor.querySelector("[data-order-field]");
  const excludedField = editor.querySelector("[data-excluded-field]");
  const hiddenMedia = editor.querySelector("[data-hidden-media]");
  const hiddenList = editor.querySelector("[data-hidden-list]");
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

  const syncExcluded = () => {
    if (!excludedField) return;
    const rows = [...editor.querySelectorAll("[data-hidden-path]")];
    excludedField.value = rows.map(row => row.dataset.hiddenPath).join("\n");
    if (hiddenMedia) hiddenMedia.hidden = rows.length === 0;
  };

  folderSelect?.addEventListener("change", () => {
    if (refreshFolder) refreshFolder.value = folderSelect.value;
    const url = new URL(window.location.href);
    url.searchParams.set("folder", folderSelect.value);
    window.location.href = url.toString();
  });

  playlist?.addEventListener("click", event => {
    const hide = event.target.closest("[data-hide-media]");
    if (hide) {
      const card = hide.closest("[data-path]");
      const path = card?.dataset.path;
      if (!card || !path || !hiddenList) return;
      const row = document.createElement("article");
      row.dataset.hiddenPath = path;
      row.innerHTML = `<span></span><button type="button" data-restore-media>Restore</button>`;
      row.querySelector("span").textContent =
        card.querySelector("strong")?.textContent || path;
      hiddenList.appendChild(row);
      card.remove();
      syncOrder();
      syncExcluded();
      return;
    }
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

  hiddenList?.addEventListener("click", event => {
    const restore = event.target.closest("[data-restore-media]");
    if (!restore || !playlist) return;
    const row = restore.closest("[data-hidden-path]");
    if (!row) return;
    const path = row.dataset.hiddenPath;
    const name = row.querySelector("span")?.textContent || path;
    const card = document.createElement("article");
    card.className = "operator-media-card";
    card.draggable = true;
    card.dataset.path = path;
    card.innerHTML = `<span class="order-number"></span><div class="operator-thumb"><span class="operator-thumb-fallback">Restored</span></div><strong></strong><div class="order-controls"><button type="button" data-move="-1" aria-label="Move earlier">&uarr;</button><button type="button" data-move="1" aria-label="Move later">&darr;</button><button type="button" data-hide-media aria-label="Hide from playback">Hide</button></div>`;
    card.querySelector("strong").textContent = name;
    playlist.appendChild(card);
    row.remove();
    syncOrder();
    syncExcluded();
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
  syncExcluded();
})();
