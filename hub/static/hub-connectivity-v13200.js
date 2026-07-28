(() => {
  const panel = document.querySelector("[data-connectivity-endpoint]");
  if (!panel) return;

  const endpoint = panel.dataset.connectivityEndpoint;
  const buttons = [...panel.querySelectorAll("[data-test-connectivity]")];

  function setStatus(target, state, text) {
    const status = panel.querySelector(
      `[data-connectivity-status="${target}"]`
    );
    if (!status) return;
    status.className = `hub-connectivity-status is-${state}`;
    status.textContent = text;
  }

  function describe(result) {
    if (!result.ok) return result.message || "Not reachable";
    const latency = result.latency_ms ? ` · ${result.latency_ms} ms` : "";
    return `Reachable${latency}`;
  }

  async function runTest(target) {
    const testedTargets = target === "all" ? ["local", "public"] : [target];
    testedTargets.forEach((name) => setStatus(name, "testing", "Testing…"));
    buttons.forEach((button) => { button.disabled = true; });

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        credentials: "same-origin",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({target}),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "Test failed");

      Object.entries(payload.results || {}).forEach(([name, result]) => {
        setStatus(name, result.ok ? "reachable" : "unreachable", describe(result));
      });
    } catch (error) {
      testedTargets.forEach((name) => {
        setStatus(name, "unreachable", error.message || "Test failed");
      });
    } finally {
      buttons.forEach((button) => { button.disabled = false; });
    }
  }

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      runTest(button.dataset.testConnectivity);
    });
  });
})();
