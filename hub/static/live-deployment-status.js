(() => {
  const page = document.querySelector("[data-live-display]");
  if (!page) return;

  const displayId = page.dataset.liveDisplay;
  if (!displayId) return;

  const card = document.querySelector(".update-stat-card");
  const verificationCard = document.querySelector(
    "[data-deployment-verification]"
  );
  const timeline = document.querySelector(
    "[data-deployment-timeline]"
  );

  const escapeHtml = (value) => {
    const element = document.createElement("div");
    element.textContent = value == null ? "" : String(value);
    return element.innerHTML;
  };

  const updateVerificationCard = (verification) => {
    if (!verificationCard) return;

    const labels = {
      idle: "No recent deployment",
      deploying: "Deployment in progress",
      verified: "Version verified",
      verification_failed: "Verification failed",
      failed: "Deployment failed",
    };

    const state = verification.state || "idle";
    verificationCard.dataset.state = state;

    const status = verificationCard.querySelector(
      "[data-verification-status]"
    );
    const detail = verificationCard.querySelector(
      "[data-verification-detail]"
    );

    if (status) {
      status.textContent = labels[state] || state;
    }

    if (detail) {
      detail.textContent = verification.message || "";
    }
  };

  const renderUpgradeCard = (verification) => {
    if (!card) return;

    const state = verification.state || "idle";
    const reported =
      verification.reported_version ||
      verification.current_version ||
      "unknown";
    const target = verification.target_version || "";
    const job = verification.job || {};
    const progress = Number(job.progress || 0);

    card.dataset.deploymentState = state;

    let eyebrow = "Software";
    let value = reported;
    let detail = "Software Current";
    let retry = "";

    if (state === "deploying") {
      eyebrow = "Upgrade in progress";
      value = `${progress}%`;
      detail = target
        ? `Installing ${target}`
        : "Installing selected release";
    } else if (state === "verified") {
      eyebrow = "Version verified";
      value = reported;
      detail = target
        ? `Heartbeat confirmed ${target}`
        : "Heartbeat confirmed installed version";
    } else if (state === "verification_failed") {
      eyebrow = "Verification failed";
      value = target
        ? `${reported} → ${target}`
        : reported;
      detail =
        verification.message ||
        "The heartbeat does not match the deployment target";
      retry = `
        <a class="button danger compact-upgrade-button"
           href="#software-upgrade">
          Review Upgrade
        </a>
      `;
    } else if (state === "failed") {
      eyebrow = "Deployment failed";
      value = reported;
      detail =
        verification.message ||
        "Review the failed deployment";
      retry = `
        <a class="button danger compact-upgrade-button"
           href="#software-upgrade">
          Review Failure
        </a>
      `;
    }

    card.innerHTML = `
      <span class="update-available-label">
        ${escapeHtml(eyebrow)}
      </span>
      <strong>${escapeHtml(value)}</strong>
      <span class="update-card-detail">
        ${escapeHtml(detail)}
      </span>
      ${retry}
      <a class="button compact-upgrade-button"
         href="#software-upgrade">
        Manage Versions
      </a>
    `;
  };

  const renderTimeline = (data) => {
    if (!timeline || !Array.isArray(data.stages)) return;

    timeline.innerHTML = data.stages.map((stage) => `
      <div class="deployment-stage ${escapeHtml(stage.state)}">
        <span class="deployment-stage-dot"></span>
        <span>${escapeHtml(stage.label)}</span>
      </div>
    `).join("");
  };

  const refresh = async () => {
    const stamp = Date.now();

    try {
      const [verificationResponse, timelineResponse] =
        await Promise.all([
          fetch(
            `/display/${encodeURIComponent(displayId)}` +
            `/deployment-verification?t=${stamp}`,
            {
              credentials: "same-origin",
              cache: "no-store",
            }
          ),
          fetch(
            `/display/${encodeURIComponent(displayId)}` +
            `/deployment-timeline?t=${stamp}`,
            {
              credentials: "same-origin",
              cache: "no-store",
            }
          ),
        ]);

      if (verificationResponse.ok) {
        const verification =
          await verificationResponse.json();

        if (verification.ok) {
          updateVerificationCard(verification);
          renderUpgradeCard(verification);

          const liveVersion = document.querySelector(
            "[data-live-version]"
          );

          if (
            liveVersion &&
            verification.reported_version
          ) {
            liveVersion.textContent =
              verification.reported_version;
          }
        }
      }

      if (timelineResponse.ok) {
        const timelineData =
          await timelineResponse.json();

        if (timelineData.ok) {
          renderTimeline(timelineData);
        }
      }
    } catch (_) {
      // Preserve the last successfully rendered state.
    }
  };

  // Prevent older deployment scripts from racing this controller.
  window.__churchDisplayLiveDeploymentController = true;

  refresh();
  window.setInterval(refresh, 5000);

  document.addEventListener(
    "visibilitychange",
    () => {
      if (!document.hidden) refresh();
    }
  );

  window.addEventListener("focus", refresh);
})();
