(() => {
  const editor = document.querySelector("[data-content-overlay-editor]");
  if (!editor) return;

  const preview = editor.querySelector("[data-overlay-preview]");
  const previewText = editor.querySelector("[data-preview-text]");
  const previewClock = editor.querySelector("[data-preview-clock]");
  const previewCountdown = editor.querySelector("[data-preview-countdown]");
  const saveState = editor.querySelector("[data-save-state]");
  const form = editor.querySelector("form");

  const textInput = editor.querySelector('[name="overlay_text"]');
  const overlayEnabled = editor.querySelector('[name="overlay_enabled"]');
  const clockEnabled = editor.querySelector('[name="clock_enabled"]');
  const countdownEnabled = editor.querySelector('[name="countdown_enabled"]');
  const countdownText = editor.querySelector('[name="countdown_text"]');

  let initial = "";

  const snapshot = () => {
    const data = new FormData(form);
    return JSON.stringify(
      Array.from(data.entries()).sort(([a], [b]) => a.localeCompare(b))
    );
  };

  const markState = () => {
    const changed = snapshot() !== initial;
    editor.dataset.dirty = changed ? "true" : "false";

    if (saveState) {
      saveState.textContent = changed
        ? "Unsaved changes"
        : "All changes saved";
    }
  };

  const updatePreview = () => {
    const overlayOn = overlayEnabled?.checked ?? true;
    const clockOn = clockEnabled?.checked ?? false;
    const countdownOn = countdownEnabled?.checked ?? false;

    if (preview) {
      preview.dataset.overlayEnabled = overlayOn ? "true" : "false";
    }

    if (previewText) {
      previewText.textContent =
        overlayOn && textInput?.value.trim()
          ? textInput.value.trim()
          : "";
      previewText.hidden = !previewText.textContent;
    }

    if (previewClock) {
      previewClock.hidden = !clockOn;
    }

    if (previewCountdown) {
      previewCountdown.textContent =
        countdownOn
          ? (countdownText?.value.trim() || "Countdown")
          : "";
      previewCountdown.hidden = !countdownOn;
    }

    markState();
  };

  form?.addEventListener("input", updatePreview);
  form?.addEventListener("change", updatePreview);

  form?.addEventListener("submit", () => {
    if (saveState) {
      saveState.textContent = "Saving…";
    }
  });

  window.addEventListener("beforeunload", (event) => {
    if (editor.dataset.dirty === "true") {
      event.preventDefault();
      event.returnValue = "";
    }
  });

  initial = snapshot();
  updatePreview();
})();
