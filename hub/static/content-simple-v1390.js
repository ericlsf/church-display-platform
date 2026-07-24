(() => {
  const page = document.querySelector("[data-simple-content]");
  const playlist = page?.querySelector("[data-simple-playlist]");
  const orderField = page?.querySelector("[data-simple-order]");
  if (!playlist || !orderField) return;

  const syncOrder = () => {
    const cards = [...playlist.querySelectorAll("[data-path]")];
    cards.forEach((card, index) => {
      const number = card.querySelector(".simple-order-number");
      if (number) number.textContent = String(index + 1);
    });
    orderField.value = cards.map(card => card.dataset.path).join("\n");
  };

  playlist.addEventListener("click", event => {
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
})();
