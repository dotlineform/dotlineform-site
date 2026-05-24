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

export function workflowDomainsForOperation(registry, operation, fallbackDomains) {
  const targetOperation = normalizeId(operation);
  const domains = [];
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
      if (!domainKey || domains.some((item) => item.key === domainKey)) return;
      const scopeKey = normalizeId(domain.scope) || domainKey;
      domains.push({
        key: domainKey,
        scope: scopeKey,
        label: normalizeText(domain.label) || domainKey,
        fallback: normalizeText(domain.label) || domainKey,
        status: capabilityStatus(adapter, domain, capability),
        message: capability.message
      });
    });
  });
  return domains.length ? domains : fallbackDomains;
}

export function workflowCapabilityForOperation(registry, operation, domainKey) {
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

export function workflowDomainFromUrl(domains, defaultDomain) {
  const params = new URLSearchParams(window.location.search);
  const requested = normalizeId(params.get("scope"));
  const items = Array.isArray(domains) ? domains : [];
  const match = items.find((item) => item.key === requested || normalizeId(item.scope) === requested);
  if (match) return match.key;
  return defaultDomain;
}

export function workflowDomainForKey(domains, key) {
  const domainKey = normalizeId(key);
  const items = Array.isArray(domains) ? domains : [];
  return items.find((item) => item.key === domainKey) || items[0] || null;
}

export function workflowDomainIsActive(domains, key) {
  const domain = workflowDomainForKey(domains, key);
  return normalizeId(domain && domain.status) === "active";
}

export function workflowScopeParamForKey(domains, key) {
  const domain = workflowDomainForKey(domains, key);
  return normalizeId(domain && domain.scope) || normalizeId(domain && domain.key) || normalizeId(key);
}
