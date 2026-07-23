(() => {
  const root = document.querySelector(
    "[data-deployment-verification]"
  );

  if (!root) return;

  const displayId = root.dataset.displayId;

  const render = (data) => {
    const state = data.state || "idle";
    root.dataset.state = state;

    const status = root.querySelector(
      "[data-verification-status]"
    );
    const detail = root.querySelector(
      "[data-verification-detail]"
    );

    if (status) {
      const labels = {
        idle: "No recent deployment",
        deploying: "Deployment in progress",
        verified: "Version verified",
        verification_failed: "Verification failed",
        failed: "Deployment failed",
      };

      status.textContent = labels[state] || state;
    }

    if (detail) {
      detail.textContent = data.message || "";
    }
  };

  const refresh = async () => {
    try {
      const response = await fetch(
        `/display/${encodeURIComponent(displayId)}/deployment-verification`,
        {
          credentials: "same-origin",
          cache: "no-store",
        }
      );

      if (!response.ok) return;
      render(await response.json());
    } catch (_) {
      // Keep the last successful state.
    }
  };

  refresh();
  window.setInterval(refresh, 15000);
})();
