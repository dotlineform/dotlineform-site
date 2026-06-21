function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function normalizeId(value) {
  return normalizeText(value).toLowerCase();
}

function capabilityRecord(item) {
  if (typeof item === "string") {
    const operation = normalizeId(item);
    return operation ? { operation, status: "active", message: "" } : null;
  }
  if (!item || typeof item !== "object") return null;
  const operation = normalizeId(item.operation);
  if (!operation) return null;
  return {
    ...item,
    operation,
    status: normalizeId(item.status) || "active",
    message: normalizeText(item.message)
  };
}

function adapterStatus(adapter) {
  return normalizeId(adapter && adapter.status) || "active";
}

function domainStatus(adapter, domain) {
  return normalizeId(domain && domain.status) || adapterStatus(adapter);
}

function capabilityStatus(adapter, domain, capability) {
  const capStatus = normalizeId(capability && capability.status);
  if (capStatus && capStatus !== "active") return capStatus;
  const scopedStatus = domainStatus(adapter, domain);
  if (scopedStatus && scopedStatus !== "active") return scopedStatus;
  return adapterStatus(adapter);
}

export function dataSharingDomainsForOperation(registry, operation, fallbackDomains) {
  const targetOperation = normalizeId(operation);
  const domains = (Array.isArray(fallbackDomains) ? fallbackDomains : []).map((item) => ({
    ...item,
    key: normalizeId(item && item.key),
    app: normalizeId(item && item.app),
    status: normalizeId(item && item.status) || "planned",
    message: normalizeText(item && item.message)
  })).filter((item) => item.key && item.app);
  const adapters = Array.isArray(registry && registry.adapters) ? registry.adapters : [];
  adapters.forEach((adapter) => {
    if (!adapter || typeof adapter !== "object") return;
    const capabilities = Array.isArray(adapter.capabilities) ? adapter.capabilities.map(capabilityRecord).filter(Boolean) : [];
    const capability = capabilities.find((item) => item.operation === targetOperation);
    if (!capability) return;
    const dataDomains = adapter.data_domains && typeof adapter.data_domains === "object" ? adapter.data_domains : {};
    Object.entries(dataDomains).forEach(([key, domain]) => {
      if (!domain || typeof domain !== "object") return;
      const domainKey = normalizeId(key);
      if (!domainKey) return;
      const projected = {
        key: domainKey,
        app: normalizeId(domain.app),
        recordSelectors: domain.record_selectors && typeof domain.record_selectors === "object"
          ? domain.record_selectors
          : {},
        label: normalizeText(domain.label) || domainKey,
        fallback: normalizeText(domain.label) || domainKey,
        status: capabilityStatus(adapter, domain, capability),
        message: capability.message
      };
      const existingIndex = domains.findIndex((item) => item.key === domainKey);
      if (existingIndex >= 0) {
        domains[existingIndex] = { ...domains[existingIndex], ...projected };
      } else {
        domains.push(projected);
      }
    });
  });
  return domains;
}

export function dataSharingCapabilityForOperation(registry, operation, domainKey) {
  const targetOperation = normalizeId(operation);
  const targetDomain = normalizeId(domainKey);
  const adapters = Array.isArray(registry && registry.adapters) ? registry.adapters : [];
  for (const adapter of adapters) {
    if (!adapter || typeof adapter !== "object") continue;
    const capabilities = Array.isArray(adapter.capabilities) ? adapter.capabilities.map(capabilityRecord).filter(Boolean) : [];
    const capability = capabilities.find((item) => item.operation === targetOperation);
    if (!capability) continue;
    const dataDomains = adapter.data_domains && typeof adapter.data_domains === "object" ? adapter.data_domains : {};
    const domain = dataDomains[targetDomain];
    if (!domain || typeof domain !== "object") continue;
    return {
      adapter,
      adapterId: normalizeText(adapter.id),
      adapterLabel: normalizeText(adapter.label),
      capability,
      dataDomain: targetDomain,
      domain,
      status: capabilityStatus(adapter, domain, capability),
      message: normalizeText(capability.message)
    };
  }
  return null;
}

export function dataSharingDomainFromUrl(domains, defaultDomain) {
  const params = new URLSearchParams(window.location.search);
  const requested = normalizeId(params.get("data_domain"));
  const items = Array.isArray(domains) ? domains : [];
  const match = items.find((item) => item.key === requested);
  if (match) return match.key;
  return defaultDomain;
}

export function dataSharingDomainForKey(domains, key) {
  const domainKey = normalizeId(key);
  const items = Array.isArray(domains) ? domains : [];
  return items.find((item) => item.key === domainKey) || items[0] || null;
}

export function dataSharingDomainIsActive(domains, key) {
  const domain = dataSharingDomainForKey(domains, key);
  return normalizeId(domain && domain.status) === "active";
}

export function dataSharingAppsForDomains(domains, fallbackApps) {
  const apps = (Array.isArray(fallbackApps) ? fallbackApps : []).map((item) => ({
    ...item,
    key: normalizeId(item && item.key)
  })).filter((item) => item.key);
  const items = Array.isArray(domains) ? domains : [];
  items.forEach((domain) => {
    const app = normalizeId(domain && domain.app);
    if (!app || apps.some((item) => item.key === app)) return;
    apps.push({ key: app });
  });
  return apps.length ? apps : fallbackApps;
}

export function dataSharingDomainsForApp(domains, app) {
  const appKey = normalizeId(app);
  return (Array.isArray(domains) ? domains : []).filter((domain) => normalizeId(domain && domain.app) === appKey);
}

export function dataSharingAppFromUrl(apps, defaultApp) {
  const params = new URLSearchParams(window.location.search);
  const requested = normalizeId(params.get("app"));
  const items = Array.isArray(apps) ? apps : [];
  const match = items.find((item) => item.key === requested);
  return match ? match.key : defaultApp;
}

export function dataSharingAppForDomain(domains, domainKey, defaultApp) {
  const domain = dataSharingDomainForKey(domains, domainKey);
  return normalizeId(domain && domain.app) || normalizeId(defaultApp);
}
