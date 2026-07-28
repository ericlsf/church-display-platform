(() => {
  const page = document.querySelector("[data-simple-content]");
  const playlist = page?.querySelector("[data-simple-playlist]");
  const orderField = page?.querySelector("[data-simple-order]");
  const excludedField = page?.querySelector("[data-simple-excluded]");
  const hiddenTray = page?.querySelector("[data-hidden-tray]");
  const hiddenList = page?.querySelector("[data-hidden-list]");
  const expirationField = page?.querySelector("[data-simple-expirations]");
  const changeSummary = page?.querySelector("[data-change-summary]");
  const searchInput = page?.querySelector("[data-playlist-search]");
  const hideSelected = page?.querySelector("[data-hide-selected]");
  if (!playlist || !orderField || !excludedField) return;

  let masterOrder = orderField.value.split(/\r?\n/).map(value => value.trim()).filter(Boolean);
  const hidden = new Map();
  const expirations = new Map();
  let changeCount = 0;
  let lastRemoved = [];

  const markChanged = (message = "Unpublished playlist changes") => {
    changeCount += 1;
    if (changeSummary) {
      changeSummary.innerHTML = `<strong>${changeCount}</strong> change${changeCount === 1 ? "" : "s"} ready to publish. ${message}.`;
      changeSummary.classList.add("has-changes");
    }
  };

  const syncExpirations = () => {
    if (expirationField) {
      expirationField.value = JSON.stringify(Object.fromEntries(expirations));
    }
  };

  const metadataFromCard = card => ({
    name: card.dataset.name || card.querySelector("strong")?.textContent?.trim() || card.dataset.path,
    type: card.dataset.type || "image",
    preview: card.dataset.preview || card.querySelector("img")?.src || "",
    position: Number(card.dataset.position || masterOrder.indexOf(card.dataset.path)),
    expires: card.dataset.expires || card.querySelector("[data-expiry]")?.value || "",
  });

  [...hiddenList?.querySelectorAll("[data-restore-card]") || []].forEach(card => {
    hidden.set(card.dataset.path, metadataFromCard(card));
    if (card.dataset.expires) expirations.set(card.dataset.path, card.dataset.expires);
  });

  const createPlaylistCard = (path, item) => {
    const card = document.createElement("article");
    card.className = "simple-image-card";
    card.draggable = true;
    card.dataset.path = path;
    card.dataset.position = String(item.position);
    card.dataset.name = item.name;
    card.dataset.type = item.type;
    card.dataset.preview = item.preview;
    card.dataset.expires = item.expires || "";

    const select = document.createElement("label");
    select.className = "simple-card-select";
    select.innerHTML = `<input type="checkbox" data-media-select><span>Select ${item.name}</span>`;

    const number = document.createElement("span");
    number.className = "simple-order-number";

    const preview = document.createElement("div");
    preview.className = "simple-image-preview";
    if (item.type === "image" && item.preview) {
      const image = document.createElement("img");
      image.loading = "lazy";
      image.src = item.preview;
      image.alt = `Preview of ${item.name}`;
      preview.append(image);
    } else {
      const fallback = document.createElement("span");
      fallback.textContent = item.type === "image" ? "Preview unavailable" : item.type;
      preview.append(fallback);
    }

    const name = document.createElement("strong");
    name.title = item.name;
    name.textContent = item.name;

    const controls = document.createElement("div");
    controls.className = "simple-order-buttons";
    [
      ["-1", "\u2191", `Move ${item.name} earlier`],
      ["1", "\u2193", `Move ${item.name} later`],
    ].forEach(([direction, label, ariaLabel]) => {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.move = direction;
      button.ariaLabel = ariaLabel;
      button.textContent = label;
      controls.append(button);
    });
    const remove = document.createElement("button");
    remove.type = "button";
    remove.dataset.hide = "";
    remove.ariaLabel = `Remove ${item.name} from playlist`;
    remove.textContent = "Remove";
    controls.append(remove);

    const expiry = document.createElement("label");
    expiry.className = "simple-expiry";
    expiry.innerHTML = `Hide after <input type="date" data-expiry value="${item.expires || ""}">`;

    card.append(number, select, preview, name, controls, expiry);
    return card;
  };

  const insertRestoredCard = (path, item) => {
    const card = createPlaylistCard(path, item);
    const position = masterOrder.indexOf(path);
    const laterPath = masterOrder.slice(position + 1).find(candidate =>
      playlist.querySelector(`[data-path="${CSS.escape(candidate)}"]`)
    );
    const laterCard = laterPath
      ? playlist.querySelector(`[data-path="${CSS.escape(laterPath)}"]`)
      : null;
    playlist.insertBefore(card, laterCard);
  };

  const renderHidden = () => {
    excludedField.value = [...hidden.keys()].join("\n");
    if (!hiddenTray || !hiddenList) return;
    hiddenTray.hidden = hidden.size === 0;
    const count = hiddenTray.querySelector("[data-hidden-count]");
    if (count) count.textContent = String(hidden.size);
    hiddenList.replaceChildren();

    [...hidden.entries()]
      .sort(([, left], [, right]) => left.position - right.position)
      .forEach(([path, item]) => {
        const card = document.createElement("article");
        card.className = "simple-hidden-card";
        card.dataset.restoreCard = "";
        card.dataset.path = path;

        const preview = document.createElement("div");
        preview.className = "simple-hidden-preview";
        if (item.type === "image" && item.preview) {
          const image = document.createElement("img");
          image.loading = "lazy";
          image.src = item.preview;
          image.alt = `Preview of ${item.name}`;
          preview.append(image);
        } else {
          const fallback = document.createElement("span");
          fallback.textContent = item.type === "image" ? "Preview unavailable" : item.type;
          preview.append(fallback);
        }

        const name = document.createElement("strong");
        name.title = item.name;
        name.textContent = item.name;
        const restore = document.createElement("button");
        restore.type = "button";
        restore.dataset.restore = path;
        restore.textContent = "Restore";
        card.append(preview, name, restore);
        hiddenList.append(card);
      });
  };

  const syncOrder = () => {
    const cards = [...playlist.querySelectorAll("[data-path]")];
    const visiblePaths = cards.map(card => card.dataset.path);
    let visibleIndex = 0;
    masterOrder = masterOrder.map(path =>
      hidden.has(path) ? path : (visiblePaths[visibleIndex++] || path)
    );
    masterOrder.push(...visiblePaths.slice(visibleIndex).filter(path => !masterOrder.includes(path)));
    [...hidden.keys()].forEach(path => {
      if (!masterOrder.includes(path)) masterOrder.push(path);
    });
    cards.forEach((card, index) => {
      const number = card.querySelector(".simple-order-number");
      if (number) number.textContent = String(index + 1);
    });
    orderField.value = masterOrder.join("\n");
    const selectedCount = playlist.querySelectorAll("[data-media-select]:checked").length;
    if (hideSelected) hideSelected.disabled = selectedCount === 0;
  };

  playlist.querySelectorAll("[data-expiry]").forEach(input => {
    if (input.value) expirations.set(input.closest("[data-path]").dataset.path, input.value);
  });
  syncExpirations();

  playlist.addEventListener("click", event => {
    const hideButton = event.target.closest("[data-hide]");
    if (hideButton) {
      const card = hideButton.closest("[data-path]");
      const item = metadataFromCard(card);
      item.position = masterOrder.indexOf(card.dataset.path);
      hidden.set(card.dataset.path, item);
      card.remove();
      syncOrder();
      renderHidden();
      lastRemoved = [[card.dataset.path, item]];
      markChanged(`${item.name} removed`);
      return;
    }
    const button = event.target.closest("[data-move]");
    if (!button) return;
    const card = button.closest("[data-path]");
    const direction = Number(button.dataset.move);
    if (direction < 0 && card.previousElementSibling) {
      playlist.insertBefore(card, card.previousElementSibling);
    }
    if (direction > 0 && card.nextElementSibling) {
      playlist.insertBefore(card.nextElementSibling, card);
    }
    syncOrder();
    markChanged(`${card.dataset.name || "Image"} moved`);
  });

  playlist.addEventListener("change", event => {
    if (event.target.matches("[data-media-select]")) {
      syncOrder();
      return;
    }
    if (event.target.matches("[data-expiry]")) {
      const path = event.target.closest("[data-path]").dataset.path;
      if (event.target.value) expirations.set(path, event.target.value);
      else expirations.delete(path);
      syncExpirations();
      markChanged("automatic hide date updated");
    }
  });

  hiddenTray?.addEventListener("click", event => {
    const restore = event.target.closest("[data-restore]");
    if (restore) {
      const path = restore.dataset.restore;
      const item = hidden.get(path);
      if (!item) return;
      insertRestoredCard(path, item);
      hidden.delete(path);
      syncOrder();
      renderHidden();
      markChanged(`${item.name} restored to its original position`);
      return;
    }
    if (event.target.closest("[data-restore-all]")) {
      [...hidden.entries()]
        .sort(([, left], [, right]) => left.position - right.position)
        .forEach(([path, item]) => insertRestoredCard(path, item));
      hidden.clear();
      syncOrder();
      renderHidden();
      markChanged("all hidden images restored");
    }
  });

  let dragged = null;
  let dropTarget = null;

  const clearDropTarget = () => {
    dropTarget?.classList.remove("drop-before", "drop-after");
    dropTarget = null;
  };

  playlist.addEventListener("dragstart", event => {
    dragged = event.target.closest("[data-path]");
    dragged?.classList.add("is-dragging");
    if (event.dataTransfer) {
      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("text/plain", dragged?.dataset.path || "");
    }
  });
  playlist.addEventListener("dragend", () => {
    dragged?.classList.remove("is-dragging");
    dragged = null;
    clearDropTarget();
    syncOrder();
    markChanged("playback order updated");
  });

  searchInput?.addEventListener("input", () => {
    const query = searchInput.value.trim().toLowerCase();
    playlist.querySelectorAll("[data-path]").forEach(card => {
      card.hidden = Boolean(query) && !(card.dataset.name || "").toLowerCase().includes(query);
    });
  });

  page.querySelector("[data-view-toggle]")?.addEventListener("click", event => {
    const compact = playlist.classList.toggle("is-list-view");
    event.currentTarget.ariaPressed = String(compact);
    event.currentTarget.textContent = compact ? "Card view" : "Compact list";
  });

  page.querySelector("[data-select-all]")?.addEventListener("click", () => {
    playlist.querySelectorAll("[data-path]:not([hidden]) [data-media-select]").forEach(input => {
      input.checked = true;
    });
    syncOrder();
  });

  hideSelected?.addEventListener("click", () => {
    lastRemoved = [];
    playlist.querySelectorAll("[data-media-select]:checked").forEach(input => {
      const card = input.closest("[data-path]");
      const item = metadataFromCard(card);
      item.position = masterOrder.indexOf(card.dataset.path);
      lastRemoved.push([card.dataset.path, item]);
      hidden.set(card.dataset.path, item);
      card.remove();
    });
    syncOrder();
    renderHidden();
    markChanged(`${lastRemoved.length} selected image${lastRemoved.length === 1 ? "" : "s"} removed`);
    if (changeSummary && lastRemoved.length) {
      const undo = document.createElement("button");
      undo.type = "button";
      undo.dataset.undoRemove = "";
      undo.textContent = "Undo";
      changeSummary.append(" ", undo);
    }
  });

  changeSummary?.addEventListener("click", event => {
    if (!event.target.closest("[data-undo-remove]")) return;
    lastRemoved
      .sort(([, left], [, right]) => left.position - right.position)
      .forEach(([path, item]) => {
        insertRestoredCard(path, item);
        hidden.delete(path);
      });
    lastRemoved = [];
    syncOrder();
    renderHidden();
    markChanged("last removal undone");
  });

  const form = page.querySelector("#simple-order-form");
  form?.addEventListener("submit", event => {
    const visible = playlist.querySelectorAll("[data-path]").length;
    const affected = page.querySelector(".simple-save-panel p")?.textContent?.trim() || "";
    if (!window.confirm(`Publish ${visible} visible image${visible === 1 ? "" : "s"}?\n\n${affected}`)) {
      event.preventDefault();
      return;
    }
    changeCount = 0;
  });

  window.addEventListener("beforeunload", event => {
    if (!changeCount) return;
    event.preventDefault();
    event.returnValue = "";
  });
  playlist.addEventListener("dragover", event => {
    if (!dragged) return;
    event.preventDefault();
    if (event.dataTransfer) event.dataTransfer.dropEffect = "move";

    const target = event.target.closest("[data-path]");
    if (!target || target === dragged || !playlist.contains(target)) {
      clearDropTarget();
      return;
    }

    const box = target.getBoundingClientRect();
    const placeAfter = event.clientX >= box.left + box.width / 2;
    clearDropTarget();
    dropTarget = target;
    target.classList.add(placeAfter ? "drop-after" : "drop-before");
  });
  playlist.addEventListener("drop", event => {
    if (!dragged) return;
    event.preventDefault();
    const target = dropTarget;
    if (target && target !== dragged) {
      playlist.insertBefore(
        dragged,
        target.classList.contains("drop-after") ? target.nextElementSibling : target
      );
    }
    clearDropTarget();
    syncOrder();
  });

  syncOrder();
  renderHidden();
})();
