(() => {
  const page = document.querySelector("[data-simple-content]");
  const playlist = page?.querySelector("[data-simple-playlist]");
  const orderField = page?.querySelector("[data-simple-order]");
  const excludedField = page?.querySelector("[data-simple-excluded]");
  const hiddenTray = page?.querySelector("[data-hidden-tray]");
  const hiddenList = page?.querySelector("[data-hidden-list]");
  if (!playlist || !orderField || !excludedField) return;

  const hidden = new Map();
  [...hiddenList?.querySelectorAll("[data-restore]") || []].forEach(button => {
    hidden.set(button.dataset.restore, button.firstChild?.textContent.trim() || button.dataset.restore);
  });

  const renderHidden = () => {
    excludedField.value = [...hidden.keys()].join("\n");
    if (!hiddenTray || !hiddenList) return;
    hiddenTray.hidden = hidden.size === 0;
    const count = hiddenTray.querySelector("[data-hidden-count]");
    if (count) count.textContent = String(hidden.size);
    hiddenList.innerHTML = [...hidden].map(([path, name]) =>
      `<button type="button" data-restore="${path.replaceAll("&", "&amp;").replaceAll('"', "&quot;")}">${name.replaceAll("&", "&amp;").replaceAll("<", "&lt;")} <span>Restore</span></button>`
    ).join("");
  };

  const syncOrder = () => {
    const cards = [...playlist.querySelectorAll("[data-path]")];
    cards.forEach((card, index) => {
      const number = card.querySelector(".simple-order-number");
      if (number) number.textContent = String(index + 1);
    });
    orderField.value = cards.map(card => card.dataset.path).join("\n");
  };

  playlist.addEventListener("click", event => {
    const hideButton = event.target.closest("[data-hide]");
    if (hideButton) {
      const card = hideButton.closest("[data-path]");
      hidden.set(card.dataset.path, card.querySelector("strong")?.textContent || card.dataset.path);
      card.remove();
      syncOrder();
      renderHidden();
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
  });

  hiddenTray?.addEventListener("click", event => {
    const restore = event.target.closest("[data-restore]");
    if (restore) {
      const path = restore.dataset.restore;
      hidden.delete(path);
      renderHidden();
      page.querySelector("#simple-order-form")?.requestSubmit();
    }
    if (event.target.closest("[data-restore-all]")) {
      hidden.clear();
      renderHidden();
      page.querySelector("#simple-order-form")?.requestSubmit();
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
      if (target.classList.contains("drop-after")) {
        playlist.insertBefore(dragged, target.nextElementSibling);
      } else {
        playlist.insertBefore(dragged, target);
      }
    }
    clearDropTarget();
    syncOrder();
  });

  syncOrder();
  renderHidden();
})();
