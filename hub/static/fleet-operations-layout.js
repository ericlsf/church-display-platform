(() => {
  const forms = Array.from(
    document.querySelectorAll(
      'form[action*="fleet-operations"], .fleet-operations-form'
    )
  );

  if (!forms.length) return;

  const normalize = (value) =>
    String(value || "")
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase();

  const labelText = (label) => {
    if (!label) return "";

    const clone = label.cloneNode(true);

    clone.querySelectorAll(
      "input, select, textarea, button"
    ).forEach((element) => element.remove());

    return normalize(clone.textContent);
  };

  const findControl = (form, expected) => {
    const wanted = normalize(expected);

    return Array.from(
      form.querySelectorAll("label")
    ).find((label) => {
      const text = labelText(label);

      return (
        text === wanted ||
        text.startsWith(`${wanted} `)
      );
    }) || null;
  };

  const createGroup = (className) => {
    const group = document.createElement("div");
    group.className = className;
    return group;
  };

  const moveInto = (group, controls) => {
    const valid = controls.filter(Boolean);

    if (!valid.length) return false;

    const first = valid[0];
    first.parentNode.insertBefore(group, first);

    valid.forEach((control) => {
      group.appendChild(control);
    });

    return true;
  };

  forms.forEach((form) => {
    if (form.dataset.layoutV642 === "true") return;

    const action = findControl(form, "Bulk Action");
    const version = findControl(form, "Version");
    const mode = findControl(form, "Mode");
    const overlayEnabled = findControl(
      form,
      "Overlay enabled"
    );
    const overlayText = findControl(
      form,
      "Overlay text"
    );
    const clockEnabled = findControl(
      form,
      "Clock enabled"
    );
    const countdownEnabled = findControl(
      form,
      "Countdown enabled"
    );
    const countdownWindow = findControl(
      form,
      "Countdown window"
    );
    const imageDuration = findControl(
      form,
      "Image duration"
    );
    const maintenance = findControl(
      form,
      "Override maintenance protection"
    );

    if (action) {
      action.classList.add(
        "fleet-control-full-row"
      );
    }

    const versionMode = createGroup(
      "fleet-control-row fleet-version-mode-row"
    );
    moveInto(versionMode, [version, mode]);

    const overlayRow = createGroup(
      "fleet-control-row fleet-overlay-row"
    );
    moveInto(
      overlayRow,
      [overlayEnabled, overlayText]
    );

    if (clockEnabled) {
      clockEnabled.classList.add(
        "fleet-control-full-row",
        "fleet-checkbox-line"
      );
    }

    if (countdownEnabled) {
      countdownEnabled.classList.add(
        "fleet-control-full-row",
        "fleet-checkbox-line"
      );
    }

    if (countdownWindow) {
      countdownWindow.classList.add(
        "fleet-control-full-row"
      );
    }

    if (imageDuration) {
      imageDuration.classList.add(
        "fleet-control-full-row"
      );
    }

    const submit = form.querySelector(
      'button[type="submit"], input[type="submit"]'
    );

    if (maintenance && submit) {
      const actions = createGroup(
        "fleet-operations-actions"
      );

      maintenance.parentNode.insertBefore(
        actions,
        maintenance
      );

      actions.appendChild(maintenance);
      actions.appendChild(submit);
    }

    form.dataset.layoutV642 = "true";
  });
})();
