const AUDIT_API_ENDPOINTS = Object.freeze({
  health: "/admin/api/audits/health",
  audits: "/admin/api/audits/audits",
  run: "/admin/api/audits/audits/run"
});

const RISK_API_ENDPOINTS = Object.freeze({
  health: "/admin/api/risk/health",
  producers: "/admin/api/risk/producers",
  runs: "/admin/api/risk/runs",
  run: (runId) => `/admin/api/risk/runs/${encodeURIComponent(String(runId || ""))}`,
  runSummary: (runId) => `${RISK_API_ENDPOINTS.run(runId)}/summary`
});

const ACTIVITY_API_ENDPOINTS = Object.freeze({
  feed: "/admin/api/activity/feed"
});

export {
  ACTIVITY_API_ENDPOINTS,
  AUDIT_API_ENDPOINTS,
  RISK_API_ENDPOINTS
};

export async function probeAuditApiHealth(timeoutMs = 500) {
  return probeHealth(AUDIT_API_ENDPOINTS.health, timeoutMs);
}

export async function probeRiskApiHealth(timeoutMs = 500) {
  return probeHealth(RISK_API_ENDPOINTS.health, timeoutMs);
}

async function probeHealth(url, timeoutMs = 500) {
  if (!url) return false;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {
      cache: "no-store",
      signal: controller.signal
    });
    if (!response.ok) return false;
    const payload = await response.json();
    return Boolean(payload && payload.ok);
  } catch (_error) {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

export async function postJson(url, payload, options = {}) {
  if (!url) throw new Error("Missing service endpoint");
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: options.signal
  });
  return responseJsonOrThrow(response, options);
}

export async function getJson(url, options = {}) {
  if (!url) throw new Error("Missing service endpoint");
  const response = await fetch(url, {
    cache: "no-store",
    signal: options.signal
  });
  return responseJsonOrThrow(response, options);
}

export async function deleteJson(url, options = {}) {
  if (!url) throw new Error("Missing service endpoint");
  const response = await fetch(url, {
    method: "DELETE",
    cache: "no-store",
    signal: options.signal
  });
  return responseJsonOrThrow(response, options);
}

async function responseJsonOrThrow(response, options = {}) {
  let payload = null;
  try {
    payload = await response.json();
  } catch (_error) {
    throw new Error(`HTTP ${response.status}`);
  }
  if (response.ok && options.allowApiFailure) {
    return payload;
  }
  if (!response.ok || !payload || !payload.ok) {
    const message = payload && payload.error ? payload.error : `HTTP ${response.status}`;
    const error = new Error(message);
    error.status = response.status;
    error.payload = payload;
    throw error;
  }
  return payload;
}
