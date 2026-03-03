const GROUPS = ["subject", "domain", "form", "theme"];

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initTagGroupsPage);
} else {
  initTagGroupsPage();
}

async function initTagGroupsPage() {
  const mount = document.getElementById("tag-groups");
  if (!mount) return;

  try {
    const data = await fetchJson("/assets/data/tag_groups.json");
    const groups = normalizeGroups(data);
    renderGroups(mount, groups);
  } catch (error) {
    mount.innerHTML = '<div class="tagStudioError">Failed to load group descriptions from /assets/data/tag_groups.json.</div>';
  }
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "default" });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

function normalizeGroups(data) {
  const rows = Array.isArray(data && data.groups) ? data.groups : [];
  const byId = new Map();
  for (const raw of rows) {
    if (!raw || typeof raw !== "object") continue;
    const groupId = normalize(raw.group_id);
    if (!GROUPS.includes(groupId)) continue;
    byId.set(groupId, {
      groupId,
      description: String(raw.description || "").trim(),
      descriptionLong: String(raw.description_long || "").trim()
    });
  }
  return GROUPS.map((groupId) => byId.get(groupId)).filter(Boolean);
}

function renderGroups(mount, groups) {
  if (!groups.length) {
    mount.innerHTML = '<p class="tagStudio__empty">No group descriptions available.</p>';
    return;
  }

  mount.innerHTML = `
    <div class="tagStudio__panel">
      <h2 class="tagStudio__heading">Tag Group Descriptions</h2>
      <div class="tagGroups__sections">
        ${groups.map((group) => `
          <section class="tagStudio__groupInfoSection tagGroups__section">
            <p class="tagStudio__groupInfoHead">
              <span class="tagStudio__keyPill tagStudio__chip--${escapeHtml(group.groupId)}">${escapeHtml(group.groupId)}</span>
            </p>
            ${group.description ? `<p class="tagGroups__short">${escapeHtml(group.description)}</p>` : ""}
            <p class="tagStudio__groupInfoText">${escapeHtml(group.descriptionLong || "No long description available.")}</p>
          </section>
        `).join("")}
      </div>
    </div>
  `;
}

function normalize(value) {
  return String(value || "").trim().toLowerCase();
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
