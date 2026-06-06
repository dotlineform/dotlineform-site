const root = document.querySelector("#adminTestingRoot");
const statusEl = document.querySelector("#adminTestingStatus");
const runsEl = document.querySelector("#adminTestingRuns");

function setStatus(message, state = "") {
  if (!statusEl) {
    return;
  }
  statusEl.textContent = message;
  if (state) {
    statusEl.dataset.state = state;
  } else {
    delete statusEl.dataset.state;
  }
}

function renderRuns(runs) {
  if (!runsEl) {
    return;
  }
  runsEl.textContent = "";
  if (!Array.isArray(runs) || runs.length === 0) {
    runsEl.textContent = "No Admin test runs yet.";
    return;
  }
  const fragment = document.createDocumentFragment();
  for (const run of runs) {
    const article = document.createElement("article");
    article.className = "adminTestingRun tagStudio__panel tagStudio__panel--compact";
    article.dataset.testRunId = String(run.run_id || "");

    const title = document.createElement("h3");
    title.textContent = String(run.run_id || "test run");
    article.append(title);

    const meta = document.createElement("p");
    meta.className = "adminTestingRun__meta";
    const profiles = Array.isArray(run.profiles) ? run.profiles.join(", ") : "";
    meta.textContent = [
      run.status ? `status: ${run.status}` : "",
      profiles ? `profiles: ${profiles}` : "",
      Number.isFinite(run.result_count) ? `results: ${run.result_count}` : "",
      Number.isFinite(run.failed_count) ? `failed: ${run.failed_count}` : "",
    ].filter(Boolean).join(" | ");
    article.append(meta);

    if (run.summary_path) {
      const path = document.createElement("p");
      path.className = "adminTestingRun__path";
      path.textContent = String(run.summary_path);
      article.append(path);
    }
    fragment.append(article);
  }
  runsEl.append(fragment);
}

async function boot() {
  if (!root) {
    return;
  }
  root.dataset.adminBusy = "true";
  try {
    const response = await fetch("/admin/api/testing/runs", { headers: { Accept: "application/json" } });
    if (!response.ok) {
      throw new Error(`testing API returned ${response.status}`);
    }
    const payload = await response.json();
    renderRuns(payload.runs);
    setStatus(`Admin test runs: ${Array.isArray(payload.runs) ? payload.runs.length : 0}`, "success");
    root.dataset.adminReady = "true";
  } catch (error) {
    setStatus(error instanceof Error ? error.message : "Could not load Admin test runs.", "error");
  } finally {
    root.dataset.adminBusy = "false";
  }
}

boot();
