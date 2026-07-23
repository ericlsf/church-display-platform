(() => {
  const editor = document.querySelector(
    "[data-content-overlay-editor]"
  );
  if (!editor) return;

  const form = editor.querySelector("form");
  if (!form) return;

  const preview = editor.querySelector(
    "[data-overlay-preview]"
  );
  const previewText = editor.querySelector(
    "[data-preview-text]"
  );
  const previewClock = editor.querySelector(
    "[data-preview-clock]"
  );
  const previewCountdown = editor.querySelector(
    "[data-preview-countdown]"
  );
  const saveState = editor.querySelector(
    "[data-save-state]"
  );

  const textInput = editor.querySelector(
    '[name="overlay_text"]'
  );
  const overlayEnabled = editor.querySelector(
    '[name="overlay_enabled"]'
  );
  const clockEnabled = editor.querySelector(
    '[name="clock_enabled"]'
  );
  const countdownEnabled = editor.querySelector(
    '[name="countdown_enabled"]'
  );
  const countdownText = editor.querySelector(
    '[name="countdown_text"]'
  );

  let initial = "";

  const snapshot = () => {
    const data = new FormData(form);

    // Unchecked checkboxes do not appear in FormData, so include them
    // explicitly to make dirty-state tracking reliable.
    return JSON.stringify({
      folder: data.get("folder") || "",
      overlay_enabled: Boolean(
        overlayEnabled && overlayEnabled.checked
      ),
      overlay_text: textInput?.value || "",
      clock_enabled: Boolean(
        clockEnabled && clockEnabled.checked
      ),
      countdown_enabled: Boolean(
        countdownEnabled && countdownEnabled.checked
      ),
      countdown_text: countdownText?.value || "",
    });
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

  const fitText = (element, value, maxLength) => {
    if (!element) return;

    const normalized = String(value || "")
      .replace(/\s+/g, " ")
      .trim();

    element.textContent =
      normalized.length > maxLength
        ? `${normalized.slice(0, maxLength - 1)}…`
        : normalized;

    element.hidden = !normalized;
    element.title = normalized;
  };

  const updatePreview = () => {
    const overlayOn =
      overlayEnabled?.checked ?? true;
    const clockOn =
      clockEnabled?.checked ?? false;
    const countdownOn =
      countdownEnabled?.checked ?? false;

    if (preview) {
      preview.dataset.overlayEnabled =
        overlayOn ? "true" : "false";
      preview.dataset.clockEnabled =
        clockOn ? "true" : "false";
      preview.dataset.countdownEnabled =
        countdownOn ? "true" : "false";
    }

    if (previewText) {
      fitText(
        previewText,
        overlayOn ? textInput?.value : "",
        70
      );
    }

    if (previewClock) {
      previewClock.hidden = !clockOn;
    }

    if (previewCountdown) {
      fitText(
        previewCountdown,
        countdownOn
          ? countdownText?.value || "Countdown"
          : "",
        32
      );
    }

    markState();
  };

  form.addEventListener("input", updatePreview);
  form.addEventListener("change", updatePreview);

  form.addEventListener("submit", () => {
    editor.dataset.dirty = "false";

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
