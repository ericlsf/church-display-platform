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
  playlist.addEventListener("dragstart", event => {
    dragged = event.target.closest("[data-path]");
    dragged?.classList.add("is-dragging");
  });
  playlist.addEventListener("dragend", () => {
    dragged?.classList.remove("is-dragging");
    dragged = null;
    syncOrder();
  });
  playlist.addEventListener("dragover", event => {
    if (!dragged) return;
    event.preventDefault();
    const cards = [...playlist.querySelectorAll("[data-path]:not(.is-dragging)")];
    const after = cards.reduce((closest, card) => {
      const box = card.getBoundingClientRect();
      const offset = event.clientY - box.top - box.height / 2;
      return offset < 0 && offset > closest.offset
        ? {offset, card}
        : closest;
    }, {offset: Number.NEGATIVE_INFINITY, card: null}).card;
    after ? playlist.insertBefore(dragged, after) : playlist.appendChild(dragged);
  });

  syncOrder();
})();
