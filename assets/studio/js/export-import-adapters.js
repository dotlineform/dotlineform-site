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
      domains.push({
        key: domainKey,
        label: normalizeText(domain.label) || domainKey,
        fallback: normalizeText(domain.label) || domainKey,
        status: capabilityStatus(adapter, domain, capability),
        message: capability.message
      });
    });
  });
  return domains.length ? domains : fallbackDomains;
}

export function workflowDomainFromUrl(domains, defaultDomain) {
  const params = new URLSearchParams(window.location.search);
  const requested = normalizeId(params.get("scope"));
  const items = Array.isArray(domains) ? domains : [];
  if (items.some((item) => item.key === requested)) return requested;
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
