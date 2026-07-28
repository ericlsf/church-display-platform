(() => {
  const terminalOutput = document.querySelector("[data-terminal-output]");
  let hubTimer = null;
  let displayTimer = null;

  const post = async (url, form) => {
    const response = await fetch(url, {method: "POST", body: new FormData(form)});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "The command could not be started.");
    return data;
  };

  const pollHub = async id => {
    clearTimeout(hubTimer);
    try {
      const response = await fetch(`/maintenance/hub/session/${encodeURIComponent(id)}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Session unavailable");
      const item = data.session;
      terminalOutput.textContent = item.output || "Waiting for output…";
      terminalOutput.scrollTop = terminalOutput.scrollHeight;
      document.querySelector("[data-terminal-target]").textContent = `${item.target_name} · ${item.cwd}`;
      document.querySelector("[data-terminal-status]").textContent = item.status;
      if (["queued", "running"].includes(item.status)) hubTimer = setTimeout(() => pollHub(id), 900);
    } catch (error) {
      terminalOutput.textContent += `\n${error.message}`;
    }
  };

  const pollDisplay = async id => {
    clearTimeout(displayTimer);
    try {
      const response = await fetch("/api/v1/jobs?type=remote_command&days=30");
      const data = await response.json();
      const item = (data.jobs || []).find(job => job.id === id);
      if (!item) throw new Error("Display session unavailable");
      document.querySelector("[data-display-output]").textContent = item.message || "Waiting for the display to check in…";
      document.querySelector("[data-display-status]").textContent = `${item.status} · ${item.progress || 0}%`;
      document.querySelector("[data-display-target]").textContent = item.display_id;
      if (["queued", "running"].includes(item.status)) displayTimer = setTimeout(() => pollDisplay(id), 1200);
    } catch (error) {
      document.querySelector("[data-display-output]").textContent += `\n${error.message}`;
    }
  };

  document.querySelectorAll("[data-terminal-tab]").forEach(button => button.addEventListener("click", () => {
    document.querySelectorAll("[data-terminal-tab]").forEach(item => item.classList.toggle("is-active", item === button));
    document.querySelectorAll("[data-terminal-panel]").forEach(panel => {
      panel.hidden = panel.dataset.terminalPanel !== button.dataset.terminalTab;
    });
  }));

  const hubForm = document.querySelector("[data-hub-terminal-form]");
  hubForm?.addEventListener("submit", async event => {
    event.preventDefault();
    const command = hubForm.querySelector("[name='command']")?.value || "";
    if (!confirm(`Run this command on the HUB?\n\n${command}`)) return;
    terminalOutput.textContent = "Starting command…";
    try {
      const data = await post("/maintenance/hub/run", hubForm);
      pollHub(data.session.id);
    } catch (error) {
      terminalOutput.textContent = error.message;
    }
  });

  document.querySelector("[data-hub-update]")?.addEventListener("click", async () => {
    if (!confirm("Pull the latest main branch, install dependencies, run a smoke test, and restart the Hub?")) return;
    terminalOutput.textContent = "Starting Hub update…";
    try {
      const response = await fetch("/maintenance/hub/update", {method: "POST"});
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Update could not start.");
      pollHub(data.session.id);
    } catch (error) {
      terminalOutput.textContent = error.message;
    }
  });

  const displayForm = document.querySelector("[data-display-terminal-form]");
  displayForm?.addEventListener("submit", async event => {
    event.preventDefault();
    const target = displayForm.querySelector("[name='display_id']")?.selectedOptions?.[0]?.textContent || "display";
    const command = displayForm.querySelector("[name='command']")?.value || "";
    if (!confirm(`Run this command on ${target}?\n\n${command}`)) return;
    document.querySelector("[data-display-output]").textContent = "Queueing command…";
    try {
      const data = await post("/maintenance/display/run", displayForm);
      pollDisplay(data.job.id);
    } catch (error) {
      document.querySelector("[data-display-output]").textContent = error.message;
    }
  });

  document.querySelectorAll("[data-session-id]").forEach(button => button.addEventListener("click", () => pollHub(button.dataset.sessionId)));
  document.querySelectorAll("[data-job-id]").forEach(button => button.addEventListener("click", () => {
    document.querySelector("[data-terminal-tab='display']")?.click();
    pollDisplay(button.dataset.jobId);
  }));
})();
