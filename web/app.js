// Quant Career Intelligence v2: Live Client State & Hierarchical Company List View
let allOpenings = [];
let trackerMeta = {};
let expandedCompanies = new Set();
let isAllExpanded = false;

// ============================================================================
// EXCEL-STYLE MULTI-COLUMN FILTER ENGINE DEFINITIONS
// ============================================================================

const EXCEL_SECTORS = [
  "Quantitative Hedge Funds",
  "Proprietary Trading & Market Making",
  "FinTech, Financial Data & Tech",
  "Systematic Asset Management & Allocators",
  "Bulge Bracket & Global Investment Banks",
  "Commercial Banking & Consulting (Practice)",
  "Commodities & Energy Trading Desks",
  "Other"
];

const EXCEL_TIERS = [
  { key: "Tier A", label: "Tier A: Moonshots ($400k - $700k+)" },
  { key: "Tier B", label: "Tier B: Main Focus ($250k - $400k+)" },
  { key: "Tier C1", label: "Tier C1: Same or Above ($180k - $260k)" },
  { key: "Tier C2", label: "Tier C2: Same or Below ($130k - $180k)" },
  { key: "Tier D", label: "Tier D: Pure Practice (< $130k)" }
];

const EXCEL_ROLES = [
  { key: "QR_QT", label: "Quant Research & Trading (QR, QT, Alpha)", icon: "chart-line" },
  { key: "DATA_SCIENCE", label: "Data Science & Analytics (Causal, A/B Testing)", icon: "chart-pie" },
  { key: "ML_AI", label: "Machine Learning & AI (RecSys, LLM, Vision)", icon: "brain" },
  { key: "PRODUCT", label: "Product & Strategy (Product Manager, PM, Growth)", icon: "boxes-stacked" },
  { key: "ENGINEERING", label: "Engineering & Core Infra (SWE, Data Eng, MLOps)", icon: "code" },
  { key: "RISK_FINANCE", label: "Risk & Finance Analytics (Model Risk, Quant Dev)", icon: "shield-halved" }
];

const EXCEL_LOCATIONS = [
  { key: "NYC", label: "New York Metro / Tri-State", icon: "city" },
  { key: "BAY_AREA", label: "SF Bay Area / Silicon Valley", icon: "laptop-code" },
  { key: "CHICAGO", label: "Chicago", icon: "wind" },
  { key: "SEATTLE", label: "Seattle", icon: "cloud-rain" },
  { key: "EUROPE", label: "London & Europe", icon: "earth-europe" },
  { key: "OTHER_LOC", label: "Remote / Other Locations", icon: "globe" }
];

const excelState = {
  sectors: new Set(),
  tiers: new Set(),
  roles: new Set(),
  locations: new Set(),
  score: "60",
  status: "ALL",
  viewScope: "ALL_FIRMS",
  crawlMethod: "ALL",
  sort: "newest",
  search: "",
  activePreset: null
};

// Role Category Classifier
function getJobRoleCategory(title, department) {
  const text = `${title || ""} ${department || ""}`.toLowerCase();
  if (/\b(?:quant|quantitative|trader|trading|alpha|portfolio manager|strat|strats|pricing model)\b/.test(text)) {
    return "QR_QT";
  }
  if (/\b(?:data scientist|data science|causal|analytics|statistician|business intelligence|bi analyst)\b/.test(text)) {
    return "DATA_SCIENCE";
  }
  if (/\b(?:machine learning|mle|deep learning|nlp|computer vision|recsys|ai engineer|artificial intelligence)\b/.test(text)) {
    return "ML_AI";
  }
  if (/\b(?:product manager|product management|product lead|technical pm|product strategy|product ops)\b/.test(text)) {
    return "PRODUCT";
  }
  if (/\b(?:software|developer|swe|engineer|data engineer|systems|infrastructure|devops|mlops|backend)\b/.test(text)) {
    return "ENGINEERING";
  }
  return "RISK_FINANCE";
}

// Location Bucket Classifier
function getJobLocationBucket(location) {
  const loc = (location || "").toLowerCase();
  if (loc.includes("new york") || loc.includes("ny") || loc.includes("jersey") || loc.includes("greenwich") || loc.includes("stamford")) {
    return "NYC";
  }
  if (loc.includes("san jose") || loc.includes("san francisco") || loc.includes("bay area") || loc.includes("mountain view") || loc.includes("palo alto") || loc.includes("sunnyvale") || loc.includes("menlo park")) {
    return "BAY_AREA";
  }
  if (loc.includes("chicago") || loc.includes(" il")) {
    return "CHICAGO";
  }
  if (loc.includes("seattle") || loc.includes("bellevue") || loc.includes(" wa")) {
    return "SEATTLE";
  }
  if (loc.includes("london") || loc.includes("uk") || loc.includes("europe") || loc.includes("paris") || loc.includes("amsterdam") || loc.includes("dublin") || loc.includes("zurich")) {
    return "EUROPE";
  }
  return "OTHER_LOC";
}

document.addEventListener("DOMContentLoaded", () => {
  // Global click listener to close Excel dropdowns when clicking outside
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".excel-dropdown")) {
      document.querySelectorAll(".excel-dropdown.open").forEach(el => el.classList.remove("open"));
    }
  });

  loadData();
});

async function loadData() {
  try {
    const res = await fetch("/api/openings");
    if (res.ok) {
      const data = await res.json();
      allOpenings = data.openings || [];
      trackerMeta = data;
      initExcelFilters();
      updateStats();
      renderCards();
      return;
    }
  } catch (err) {
    console.warn("API /api/openings unavailable, falling back to static window.LIVE_OPENINGS_DATA.");
  }

  // Fallback to static window object if data.js is loaded
  if (window.LIVE_OPENINGS_DATA && window.LIVE_OPENINGS_DATA.openings) {
    allOpenings = window.LIVE_OPENINGS_DATA.openings;
    trackerMeta = window.LIVE_OPENINGS_DATA;
    initExcelFilters();
    updateStats();
    renderCards();
  } else {
    document.getElementById("jobs-container").innerHTML = `
      <div class="empty-state">
        <i class="fa-solid fa-triangle-exclamation fa-2x" style="color: #f59e0b;"></i>
        <p style="margin-top: 10px; font-weight: 600;">No live openings dataset found.</p>
        <p style="font-size: 0.85rem; color: #9ca3af; margin-top: 4px;">
          Click <strong>Run All Crawlers</strong> above or execute <code>python main.py crawl</code> to populate live jobs.
        </p>
      </div>
    `;
  }
}

// ============================================================================
// EXCEL DROPDOWNS INITIALIZATION & EVENT HANDLERS
// ============================================================================

function initExcelFilters() {
  renderSectorDropdownList();
  renderTierDropdownList();
  renderRoleDropdownList();
  renderLocationDropdownList();
  updateDropdownLabels();
  renderActiveChips();
}

function toggleExcelDropdown(type, event) {
  if (event) event.stopPropagation();
  const dropdownEl = document.getElementById(`dropdown-${type}`);
  const isOpen = dropdownEl.classList.contains("open");
  
  // Close any other open dropdowns
  document.querySelectorAll(".excel-dropdown.open").forEach(el => el.classList.remove("open"));

  if (!isOpen) {
    dropdownEl.classList.add("open");
    const searchInput = dropdownEl.querySelector(".excel-panel-search");
    if (searchInput) {
      searchInput.value = "";
      filterDropdownList(type, "");
      setTimeout(() => searchInput.focus(), 50);
    }
  }
}

function filterDropdownList(type, query) {
  const q = query.toLowerCase().trim();
  const listEl = document.getElementById(`list-filter-${type}`);
  if (!listEl) return;
  listEl.querySelectorAll(".excel-item").forEach(item => {
    const text = item.innerText.toLowerCase();
    item.style.display = (!q || text.includes(q)) ? "flex" : "none";
  });
}

function renderSectorDropdownList() {
  const listEl = document.getElementById("list-filter-sector");
  if (!listEl) return;

  // Compute live job count per sector
  const counts = {};
  EXCEL_SECTORS.forEach(s => counts[s] = 0);
  allOpenings.forEach(j => {
    const s = j.industry_sector;
    if (counts[s] !== undefined) counts[s]++;
  });

  listEl.innerHTML = EXCEL_SECTORS.map(sec => {
    const isChecked = excelState.sectors.has(sec);
    const count = counts[sec] || 0;
    return `
      <label class="excel-item">
        <input type="checkbox" value="${escapeHtml(sec)}" ${isChecked ? "checked" : ""} onchange="onCheckboxChange('sector', this.value, this.checked)">
        <span class="excel-item-label">${escapeHtml(sec)}</span>
        <span class="excel-item-count">${count}</span>
      </label>
    `;
  }).join("");
}

function renderTierDropdownList() {
  const listEl = document.getElementById("list-filter-tier");
  if (!listEl) return;

  const counts = {};
  EXCEL_TIERS.forEach(t => counts[t.key] = 0);
  allOpenings.forEach(j => {
    const pt = j.priority_tier || "";
    EXCEL_TIERS.forEach(t => {
      if (pt.includes(t.key)) counts[t.key]++;
    });
  });

  listEl.innerHTML = EXCEL_TIERS.map(tier => {
    const isChecked = excelState.tiers.has(tier.key);
    const count = counts[tier.key] || 0;
    return `
      <label class="excel-item">
        <input type="checkbox" value="${escapeHtml(tier.key)}" ${isChecked ? "checked" : ""} onchange="onCheckboxChange('tier', this.value, this.checked)">
        <span class="excel-item-label">${escapeHtml(tier.label)}</span>
        <span class="excel-item-count">${count}</span>
      </label>
    `;
  }).join("");
}

function renderRoleDropdownList() {
  const listEl = document.getElementById("list-filter-role");
  if (!listEl) return;

  const counts = {};
  EXCEL_ROLES.forEach(r => counts[r.key] = 0);
  allOpenings.forEach(j => {
    const cat = getJobRoleCategory(j.title, j.department);
    if (counts[cat] !== undefined) counts[cat]++;
  });

  listEl.innerHTML = EXCEL_ROLES.map(role => {
    const isChecked = excelState.roles.has(role.key);
    const count = counts[role.key] || 0;
    return `
      <label class="excel-item">
        <input type="checkbox" value="${escapeHtml(role.key)}" ${isChecked ? "checked" : ""} onchange="onCheckboxChange('role', this.value, this.checked)">
        <span class="excel-item-label"><i class="fa-solid fa-${role.icon}" style="width: 16px; opacity: 0.8; margin-right: 4px;"></i>${escapeHtml(role.label)}</span>
        <span class="excel-item-count">${count}</span>
      </label>
    `;
  }).join("");
}

function renderLocationDropdownList() {
  const listEl = document.getElementById("list-filter-location");
  if (!listEl) return;

  const counts = {};
  EXCEL_LOCATIONS.forEach(l => counts[l.key] = 0);
  allOpenings.forEach(j => {
    const loc = getJobLocationBucket(j.location);
    if (counts[loc] !== undefined) counts[loc]++;
  });

  listEl.innerHTML = EXCEL_LOCATIONS.map(loc => {
    const isChecked = excelState.locations.has(loc.key);
    const count = counts[loc.key] || 0;
    return `
      <label class="excel-item">
        <input type="checkbox" value="${escapeHtml(loc.key)}" ${isChecked ? "checked" : ""} onchange="onCheckboxChange('location', this.value, this.checked)">
        <span class="excel-item-label"><i class="fa-solid fa-${loc.icon}" style="width: 16px; opacity: 0.8; margin-right: 4px;"></i>${escapeHtml(loc.label)}</span>
        <span class="excel-item-count">${count}</span>
      </label>
    `;
  }).join("");
}

function onCheckboxChange(type, value, checked) {
  excelState.activePreset = null;
  updatePresetButtons();

  if (type === "sector") {
    if (checked) excelState.sectors.add(value);
    else excelState.sectors.delete(value);
  } else if (type === "tier") {
    if (checked) excelState.tiers.add(value);
    else excelState.tiers.delete(value);
  } else if (type === "role") {
    if (checked) excelState.roles.add(value);
    else excelState.roles.delete(value);
  } else if (type === "location") {
    if (checked) excelState.locations.add(value);
    else excelState.locations.delete(value);
  }

  updateDropdownLabels();
  renderActiveChips();
  renderCards();
}

function selectAllInDropdown(type) {
  excelState.activePreset = null;
  updatePresetButtons();

  if (type === "sector") {
    excelState.sectors.clear();
    EXCEL_SECTORS.forEach(s => excelState.sectors.add(s));
  } else if (type === "tier") {
    excelState.tiers.clear();
    EXCEL_TIERS.forEach(t => excelState.tiers.add(t.key));
  } else if (type === "role") {
    excelState.roles.clear();
    EXCEL_ROLES.forEach(r => excelState.roles.add(r.key));
  } else if (type === "location") {
    excelState.locations.clear();
    EXCEL_LOCATIONS.forEach(l => excelState.locations.add(l.key));
  }

  refreshCheckboxesInDOM(type);
  updateDropdownLabels();
  renderActiveChips();
  renderCards();
}

function clearAllInDropdown(type) {
  excelState.activePreset = null;
  updatePresetButtons();

  if (type === "sector") excelState.sectors.clear();
  else if (type === "tier") excelState.tiers.clear();
  else if (type === "role") excelState.roles.clear();
  else if (type === "location") excelState.locations.clear();

  refreshCheckboxesInDOM(type);
  updateDropdownLabels();
  renderActiveChips();
  renderCards();
}

function refreshCheckboxesInDOM(type) {
  const listEl = document.getElementById(`list-filter-${type}`);
  if (!listEl) return;
  listEl.querySelectorAll("input[type='checkbox']").forEach(cb => {
    let checked = false;
    if (type === "sector") checked = excelState.sectors.has(cb.value);
    else if (type === "tier") checked = excelState.tiers.has(cb.value);
    else if (type === "role") checked = excelState.roles.has(cb.value);
    else if (type === "location") checked = excelState.locations.has(cb.value);
    cb.checked = checked;
  });
}

function updateDropdownLabels() {
  // Sector label
  const btnSector = document.getElementById("btn-filter-sector");
  const lblSector = document.getElementById("label-filter-sector");
  if (btnSector && lblSector) {
    const total = EXCEL_SECTORS.length;
    const selected = excelState.sectors.size;
    if (selected === 0 || selected === total) {
      lblSector.innerText = `Sector: All (${total})`;
      btnSector.classList.remove("active-filter");
    } else if (selected === 1) {
      lblSector.innerText = `Sector: ${Array.from(excelState.sectors)[0]}`;
      btnSector.classList.add("active-filter");
    } else {
      lblSector.innerText = `Sectors: (${selected}/${total})`;
      btnSector.classList.add("active-filter");
    }
  }

  // Tier label
  const btnTier = document.getElementById("btn-filter-tier");
  const lblTier = document.getElementById("label-filter-tier");
  if (btnTier && lblTier) {
    const total = EXCEL_TIERS.length;
    const selected = excelState.tiers.size;
    if (selected === 0 || selected === total) {
      lblTier.innerText = `Tier: All (${total})`;
      btnTier.classList.remove("active-filter");
    } else if (selected === 1) {
      lblTier.innerText = `Tier: ${Array.from(excelState.tiers)[0]}`;
      btnTier.classList.add("active-filter");
    } else {
      lblTier.innerText = `Tiers: (${selected}/${total})`;
      btnTier.classList.add("active-filter");
    }
  }

  // Role label
  const btnRole = document.getElementById("btn-filter-role");
  const lblRole = document.getElementById("label-filter-role");
  if (btnRole && lblRole) {
    const total = EXCEL_ROLES.length;
    const selected = excelState.roles.size;
    if (selected === 0 || selected === total) {
      lblRole.innerText = `Role: All (${total})`;
      btnRole.classList.remove("active-filter");
    } else if (selected === 1) {
      const rObj = EXCEL_ROLES.find(r => r.key === Array.from(excelState.roles)[0]);
      lblRole.innerText = `Role: ${rObj ? rObj.label.split("(")[0].trim() : "Custom"}`;
      btnRole.classList.add("active-filter");
    } else {
      lblRole.innerText = `Roles: (${selected}/${total})`;
      btnRole.classList.add("active-filter");
    }
  }

  // Location label
  const btnLoc = document.getElementById("btn-filter-location");
  const lblLoc = document.getElementById("label-filter-location");
  if (btnLoc && lblLoc) {
    const total = EXCEL_LOCATIONS.length;
    const selected = excelState.locations.size;
    if (selected === 0 || selected === total) {
      lblLoc.innerText = `Location: All`;
      btnLoc.classList.remove("active-filter");
    } else if (selected === 1) {
      const lObj = EXCEL_LOCATIONS.find(l => l.key === Array.from(excelState.locations)[0]);
      lblLoc.innerText = `Location: ${lObj ? lObj.label.split("/")[0].trim() : "Custom"}`;
      btnLoc.classList.add("active-filter");
    } else {
      lblLoc.innerText = `Locations: (${selected}/${total})`;
      btnLoc.classList.add("active-filter");
    }
  }
}

function renderActiveChips() {
  const container = document.getElementById("active-filter-chips-container");
  const chipsList = document.getElementById("active-filter-chips");
  if (!container || !chipsList) return;

  const chips = [];

  // Search chip
  if (excelState.search) {
    chips.push({
      text: `Search: "${excelState.search}"`,
      clear: () => {
        excelState.search = "";
        document.getElementById("filter-search").value = "";
        renderCards();
      }
    });
  }

  // Sectors chips
  if (excelState.sectors.size > 0 && excelState.sectors.size < EXCEL_SECTORS.length) {
    excelState.sectors.forEach(sec => {
      chips.push({
        text: `Sector: ${sec}`,
        clear: () => onCheckboxChange("sector", sec, false)
      });
    });
  }

  // Tiers chips
  if (excelState.tiers.size > 0 && excelState.tiers.size < EXCEL_TIERS.length) {
    excelState.tiers.forEach(tierKey => {
      chips.push({
        text: `Tier: ${tierKey}`,
        clear: () => onCheckboxChange("tier", tierKey, false)
      });
    });
  }

  // Roles chips
  if (excelState.roles.size > 0 && excelState.roles.size < EXCEL_ROLES.length) {
    excelState.roles.forEach(roleKey => {
      const rObj = EXCEL_ROLES.find(r => r.key === roleKey);
      chips.push({
        text: `Role: ${rObj ? rObj.label.split("(")[0].trim() : roleKey}`,
        clear: () => onCheckboxChange("role", roleKey, false)
      });
    });
  }

  // Locations chips
  if (excelState.locations.size > 0 && excelState.locations.size < EXCEL_LOCATIONS.length) {
    excelState.locations.forEach(locKey => {
      const lObj = EXCEL_LOCATIONS.find(l => l.key === locKey);
      chips.push({
        text: `Loc: ${lObj ? lObj.label.split("/")[0].trim() : locKey}`,
        clear: () => onCheckboxChange("location", locKey, false)
      });
    });
  }

  // Score chip
  if (excelState.score && excelState.score !== "ALL") {
    chips.push({
      text: `Score ≥ ${excelState.score}`,
      clear: () => {
        excelState.score = "ALL";
        document.getElementById("filter-score").value = "ALL";
        renderCards();
      }
    });
  }

  // Status chip
  if (excelState.status && excelState.status !== "ALL") {
    chips.push({
      text: `Status: ${excelState.status === "ACTIVE_ONLY" ? "Active" : excelState.status}`,
      clear: () => {
        excelState.status = "ALL";
        document.getElementById("filter-status").value = "ALL";
        renderCards();
      }
    });
  }

  if (chips.length === 0) {
    container.style.display = "none";
    chipsList.innerHTML = "";
  } else {
    container.style.display = "flex";
    chipsList.innerHTML = chips.map((c, idx) => `
      <span class="filter-chip">
        <span>${escapeHtml(c.text)}</span>
        <i class="fa-solid fa-xmark filter-chip-remove" onclick="window.activeChipActions[${idx}]()"></i>
      </span>
    `).join("");
    window.activeChipActions = chips.map(c => c.clear);
  }
}

// Quick Preset Combinations
function applyPreset(presetKey) {
  excelState.sectors.clear();
  excelState.tiers.clear();
  excelState.roles.clear();
  excelState.locations.clear();
  excelState.search = "";
  document.getElementById("filter-search").value = "";

  if (presetKey === "buyside_quant") {
    // Top Buy-Side Quant: Tier A & B, Quant Hedge Funds & Prop Trading, Score >= 80
    excelState.tiers.add("Tier A");
    excelState.tiers.add("Tier B");
    excelState.sectors.add("Quantitative Hedge Funds");
    excelState.sectors.add("Proprietary Trading & Market Making");
    excelState.score = "80";
    document.getElementById("filter-score").value = "80";
    excelState.activePreset = "buyside_quant";
  } else if (presetKey === "tech_ds_ml") {
    // Tech & FinTech DS/ML: FinTech/Tech Sector, Data Science, ML & Product
    excelState.sectors.add("FinTech, Financial Data & Tech");
    excelState.roles.add("DATA_SCIENCE");
    excelState.roles.add("ML_AI");
    excelState.roles.add("PRODUCT");
    excelState.score = "60";
    document.getElementById("filter-score").value = "60";
    excelState.activePreset = "tech_ds_ml";
  } else if (presetKey === "product_data") {
    // Product & Analytics
    excelState.roles.add("PRODUCT");
    excelState.roles.add("DATA_SCIENCE");
    excelState.score = "60";
    document.getElementById("filter-score").value = "60";
    excelState.activePreset = "product_data";
  } else if (presetKey === "nyc_metro") {
    // New York Metro
    excelState.locations.add("NYC");
    excelState.activePreset = "nyc_metro";
  } else if (presetKey === "front_office") {
    // High-Comp Tier A & B ($250k+)
    excelState.tiers.add("Tier A");
    excelState.tiers.add("Tier B");
    excelState.activePreset = "front_office";
  }

  updatePresetButtons();
  refreshCheckboxesInDOM("sector");
  refreshCheckboxesInDOM("tier");
  refreshCheckboxesInDOM("role");
  refreshCheckboxesInDOM("location");
  updateDropdownLabels();
  renderActiveChips();
  renderCards();
}

function updatePresetButtons() {
  document.querySelectorAll(".btn-preset").forEach(btn => {
    btn.classList.remove("active");
  });
  if (excelState.activePreset) {
    const activeBtn = document.getElementById(`preset-${excelState.activePreset.replace(/_/g, "-")}`);
    if (activeBtn) activeBtn.classList.add("active");
  }
}

function resetAllFilters() {
  excelState.sectors.clear();
  excelState.tiers.clear();
  excelState.roles.clear();
  excelState.locations.clear();
  excelState.search = "";
  excelState.score = "ALL";
  excelState.status = "ALL";
  excelState.viewScope = "ALL_FIRMS";
  excelState.crawlMethod = "ALL";
  excelState.sort = "newest";
  excelState.activePreset = null;

  document.getElementById("filter-search").value = "";
  if (document.getElementById("filter-score")) document.getElementById("filter-score").value = "ALL";
  if (document.getElementById("filter-status")) document.getElementById("filter-status").value = "ALL";
  if (document.getElementById("filter-sort")) document.getElementById("filter-sort").value = "newest";
  if (document.getElementById("filter-view-scope")) document.getElementById("filter-view-scope").value = "ALL_FIRMS";
  if (document.getElementById("filter-crawlability")) document.getElementById("filter-crawlability").value = "ALL";

  updatePresetButtons();
  refreshCheckboxesInDOM("sector");
  refreshCheckboxesInDOM("tier");
  refreshCheckboxesInDOM("role");
  refreshCheckboxesInDOM("location");
  updateDropdownLabels();
  renderActiveChips();
  renderCards();
}

function onSearchInput() {
  excelState.search = document.getElementById("filter-search").value.toLowerCase().trim();
  excelState.activePreset = null;
  updatePresetButtons();
  renderActiveChips();
  renderCards();
}

function onScoreChange() {
  excelState.score = document.getElementById("filter-score").value;
  excelState.activePreset = null;
  updatePresetButtons();
  renderActiveChips();
  renderCards();
}

function onStatusChange() {
  excelState.status = document.getElementById("filter-status").value;
  excelState.activePreset = null;
  updatePresetButtons();
  renderActiveChips();
  renderCards();
}

function onCrawlabilityChange() {
  excelState.crawlMethod = document.getElementById("filter-crawlability").value;
  renderCards();
}

function onSortChange() {
  excelState.sort = document.getElementById("filter-sort").value;
  renderCards();
}

function onViewScopeChange() {
  excelState.viewScope = document.getElementById("filter-view-scope").value;
  renderCards();
}

function updateStats() {
  const activeCount = allOpenings.filter(j => j.status !== "INACTIVE").length;
  const high = allOpenings.filter(j => (j.suitability_score || 0) >= 80).length;
  const newlyDiscovered = allOpenings.filter(j => j.status === "NEW").length;
  const hiringFirms = new Set(allOpenings.filter(j => j.status !== "INACTIVE").map(j => j.firm_name)).size;
  const totalMonitoredFirms = (trackerMeta.firms_directory ? trackerMeta.firms_directory.length : (trackerMeta.stats ? trackerMeta.stats.total_monitored_firms : 296)) || 296;
  const directory = trackerMeta.firms_directory || [];
  const autoCount = directory.filter(f => f.crawl_status === "AUTOMATED_FEED").length;
  const portalCount = directory.length > 0 ? (directory.length - autoCount) : 213;

  if (document.getElementById("stat-total")) document.getElementById("stat-total").innerText = activeCount;
  if (document.getElementById("stat-high")) document.getElementById("stat-high").innerText = high;
  if (document.getElementById("stat-new")) document.getElementById("stat-new").innerText = newlyDiscovered;
  if (document.getElementById("stat-firms")) document.getElementById("stat-firms").innerText = totalMonitoredFirms;
  if (document.getElementById("stat-firms-sub") && autoCount > 0) {
    document.getElementById("stat-firms-sub").innerText = `${autoCount} Live Feeds • ${portalCount} Direct Portals`;
  }
  if (document.getElementById("stat-hiring-firms")) document.getElementById("stat-hiring-firms").innerText = hiringFirms;

  if (trackerMeta.last_updated && document.getElementById("last-updated-label")) {
    const d = new Date(trackerMeta.last_updated);
    document.getElementById("last-updated-label").innerText = `Last Agent Crawl: ${d.toLocaleString()}`;
  }
}

function toggleCompany(firmKey) {
  if (expandedCompanies.has(firmKey)) {
    expandedCompanies.delete(firmKey);
  } else {
    expandedCompanies.add(firmKey);
  }
  const el = document.getElementById(`company-card-${firmKey}`);
  if (el) {
    el.classList.toggle("expanded", expandedCompanies.has(firmKey));
  }
}

function toggleExpandAll() {
  const btnText = document.getElementById("toggle-all-text");
  if (!isAllExpanded) {
    document.querySelectorAll(".company-card").forEach(card => {
      const firmKey = card.getAttribute("data-firm-key");
      if (firmKey) expandedCompanies.add(firmKey);
      card.classList.add("expanded");
    });
    isAllExpanded = true;
    if (btnText) btnText.innerText = "Collapse All";
  } else {
    document.querySelectorAll(".company-card").forEach(card => {
      card.classList.remove("expanded");
    });
    expandedCompanies.clear();
    isAllExpanded = false;
    if (btnText) btnText.innerText = "Expand All";
  }
}

function getTierRank(tierStr) {
  if (!tierStr) return 99;
  if (tierStr.includes("Tier A")) return 1;
  if (tierStr.includes("Tier B")) return 2;
  if (tierStr.includes("Tier C1")) return 3;
  if (tierStr.includes("Tier C2")) return 4;
  if (tierStr.includes("Tier D")) return 5;
  return 90;
}

// ============================================================================
// MAIN RENDER ENGINE
// ============================================================================

function renderCards() {
  const container = document.getElementById("jobs-container");
  const search = excelState.search;
  const sortOption = excelState.sort;
  const viewScope = excelState.viewScope;
  const scoreFilter = excelState.score;
  const statusFilter = excelState.status;

  // 1. Filter individual openings using Excel combinations
  const filteredJobs = allOpenings.filter(job => {
    // Text search
    if (search) {
      const matchText = `${job.firm_name} ${job.title} ${job.location} ${job.department || ''} ${job.industry_sector || ''} ${job.posted_pay_range || ''}`.toLowerCase();
      if (!matchText.includes(search)) return false;
    }

    // Priority Tier (Multi-select)
    if (excelState.tiers.size > 0 && excelState.tiers.size < EXCEL_TIERS.length) {
      const jobTier = job.priority_tier || "";
      const matchesAnyTier = Array.from(excelState.tiers).some(t => jobTier.includes(t));
      if (!matchesAnyTier) return false;
    }

    // Industry Sector (Multi-select)
    if (excelState.sectors.size > 0 && excelState.sectors.size < EXCEL_SECTORS.length) {
      const jobSector = job.industry_sector || "";
      if (!excelState.sectors.has(jobSector)) return false;
    }

    // Role Category (Multi-select)
    if (excelState.roles.size > 0 && excelState.roles.size < EXCEL_ROLES.length) {
      const jobRoleCat = getJobRoleCategory(job.title, job.department);
      if (!excelState.roles.has(jobRoleCat)) return false;
    }

    // Location (Multi-select)
    if (excelState.locations.size > 0 && excelState.locations.size < EXCEL_LOCATIONS.length) {
      const jobLocBucket = getJobLocationBucket(job.location);
      if (!excelState.locations.has(jobLocBucket)) return false;
    }

    // Suitability Score
    if (scoreFilter !== "ALL") {
      const minScore = parseInt(scoreFilter, 10);
      if ((job.suitability_score || 0) < minScore) return false;
    }

    // Listing Status
    if (statusFilter === "ACTIVE_ONLY") {
      if (job.status === "INACTIVE") return false;
    } else if (statusFilter !== "ALL") {
      if (job.status !== statusFilter) return false;
    }

    return true;
  });

  // 2. Build Company Map
  const companyMap = new Map();

  // Populate from firms_directory if viewScope allows all firms
  const directory = trackerMeta.firms_directory || [];
  if (viewScope === "ALL_FIRMS" && directory.length > 0) {
    for (const f of directory) {
      companyMap.set(f.firm_name, {
        firm_name: f.firm_name,
        priority_tier: f.priority_tier || "Tier B: Main Focus",
        priority_tag: f.priority_tag || "Main Focus",
        industry_sector: f.industry_sector || "Quantitative Hedge Funds",
        estimated_comp: f.estimated_comp || "$250,000 - $400,000+",
        comp_benchmark_delta: f.comp_benchmark_delta || "Significantly Above Benchmark",
        official_careers_url: f.official_careers_url || "",
        crawl_status: f.crawl_status || "UNCRAWLABLE_PORTAL_ONLY",
        crawl_method: f.crawl_method || "Direct Portal Monitored",
        uncrawlable_reason: f.uncrawlable_reason || null,
        has_new: false,
        max_score: 0,
        latest_date: null,
        jobs: []
      });
    }
  }

  // Populate active jobs
  for (const job of filteredJobs) {
    const firm = job.firm_name || "Unknown Firm";
    let sector = job.industry_sector;
    if (!sector || sector === "Quantitative Finance") {
      sector = "Quantitative Hedge Funds";
      job.industry_sector = sector;
    }

    if (!companyMap.has(firm)) {
      companyMap.set(firm, {
        firm_name: firm,
        priority_tier: job.priority_tier || "Tier B: Main Focus",
        priority_tag: job.priority_tag || "Main Focus",
        industry_sector: sector,
        estimated_comp: job.estimated_comp || "$250,000 - $400,000+",
        comp_benchmark_delta: job.comp_benchmark_delta || "Significantly Above Benchmark",
        official_careers_url: job.official_careers_url || "",
        crawl_status: "AUTOMATED_FEED",
        crawl_method: "Automated Live Feed",
        uncrawlable_reason: null,
        has_new: false,
        max_score: 0,
        latest_date: null,
        jobs: []
      });
    }

    const group = companyMap.get(firm);
    group.jobs.push(job);
    group.crawl_status = "AUTOMATED_FEED";
    if (job.official_careers_url && !group.official_careers_url) {
      group.official_careers_url = job.official_careers_url;
    }
    if (job.status === "NEW") group.has_new = true;
    if ((job.suitability_score || 0) > group.max_score) {
      group.max_score = job.suitability_score || 0;
    }
    if (job.last_seen) {
      const d = new Date(job.last_seen);
      if (!group.latest_date || d > group.latest_date) group.latest_date = d;
    }
  }

  let companies = Array.from(companyMap.values());

  // Apply filters to company metadata
  const crawlFilter = excelState.crawlMethod;
  if (crawlFilter === "AUTOMATED") {
    companies = companies.filter(c => c.crawl_status === "AUTOMATED_FEED");
  } else if (crawlFilter === "PORTAL_ONLY") {
    companies = companies.filter(c => c.crawl_status !== "AUTOMATED_FEED");
  }

  // Sector filter for companies
  if (excelState.sectors.size > 0 && excelState.sectors.size < EXCEL_SECTORS.length) {
    companies = companies.filter(c => excelState.sectors.has(c.industry_sector));
  }

  // Tier filter for companies
  if (excelState.tiers.size > 0 && excelState.tiers.size < EXCEL_TIERS.length) {
    companies = companies.filter(c => Array.from(excelState.tiers).some(t => (c.priority_tier || "").includes(t)));
  }

  // View Scope
  if (viewScope === "ACTIVE_ONLY") {
    companies = companies.filter(c => c.jobs.length > 0);
  }

  // Search filter across company metadata
  if (search) {
    companies = companies.filter(c => {
      const cText = `${c.firm_name} ${c.industry_sector} ${c.priority_tier}`.toLowerCase();
      const hasJobMatch = c.jobs.some(j => `${j.title} ${j.location}`.toLowerCase().includes(search));
      return cText.includes(search) || hasJobMatch;
    });
  }

  // 3. Sort companies according to selected order
  companies.sort((a, b) => {
    if (sortOption === "newest") {
      if (a.has_new !== b.has_new) return b.has_new ? 1 : -1;
      if (a.jobs.length > 0 && b.jobs.length === 0) return -1;
      if (b.jobs.length > 0 && a.jobs.length === 0) return 1;
      if (a.latest_date && b.latest_date && a.latest_date.getTime() !== b.latest_date.getTime()) {
        return b.latest_date.getTime() - a.latest_date.getTime();
      }
      return b.max_score - a.max_score;
    } else if (sortOption === "name_asc") {
      return a.firm_name.localeCompare(b.firm_name);
    } else if (sortOption === "tier") {
      const rankA = getTierRank(a.priority_tier);
      const rankB = getTierRank(b.priority_tier);
      if (rankA !== rankB) return rankA - rankB;
      return b.max_score - a.max_score;
    } else if (sortOption === "openings") {
      return b.jobs.length - a.jobs.length;
    } else if (sortOption === "score") {
      return b.max_score - a.max_score;
    }
    return 0;
  });

  // Count summary
  const activeRolesInView = companies.reduce((acc, c) => acc + c.jobs.length, 0);
  document.getElementById("feed-count-label").innerText = `Showing ${companies.length} Employers (${activeRolesInView} Active Postings)`;

  if (companies.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <i class="fa-solid fa-folder-open fa-2x"></i>
        <p style="margin-top: 10px; font-weight: 600;">No postings or firms matched your filter combination.</p>
        <p style="font-size: 0.85rem; color: #9ca3af; margin-top: 4px;">
          Try adjusting the filter combination or clicking <button class="btn-clear-chips" onclick="resetAllFilters()" style="display:inline; margin:0; padding:0; text-decoration:underline;">Reset All</button>.
        </p>
      </div>
    `;
    return;
  }

  // 4. Render Company List View with Expandable 2nd Layer
  container.innerHTML = companies.map(comp => {
    const firmKey = encodeURIComponent(comp.firm_name.replace(/\\s+/g, "_"));
    const isExpanded = expandedCompanies.has(firmKey);

    // Tier badge class
    let tierBadgeClass = "pill-tier-b";
    const pTier = comp.priority_tier || "";
    if (pTier.includes("Tier A")) tierBadgeClass = "pill-tier-a";
    else if (pTier.includes("Tier B")) tierBadgeClass = "pill-tier-b";
    else if (pTier.includes("Tier C1")) tierBadgeClass = "pill-tier-c1";
    else if (pTier.includes("Tier C2")) tierBadgeClass = "pill-tier-c2";
    else if (pTier.includes("Tier D")) tierBadgeClass = "pill-tier-d";

    // Score badge for company
    let topScoreClass = "score-low";
    if (comp.max_score >= 80) topScoreClass = "score-high";
    else if (comp.max_score >= 60) topScoreClass = "score-mid";

    // Render inner jobs
    const jobsHtml = comp.jobs.map(j => {
      const isNew = j.status === "NEW";
      const isInactive = j.status === "INACTIVE";
      const score = j.suitability_score || 0;
      let scoreClass = "score-low";
      if (score >= 80) scoreClass = "score-high";
      else if (score >= 60) scoreClass = "score-mid";

      const roleCat = getJobRoleCategory(j.title, j.department);
      let roleIcon = "fa-briefcase";
      if (roleCat === "QR_QT") roleIcon = "fa-chart-line";
      else if (roleCat === "DATA_SCIENCE") roleIcon = "fa-chart-pie";
      else if (roleCat === "ML_AI") roleIcon = "fa-brain";
      else if (roleCat === "PRODUCT") roleIcon = "fa-boxes-stacked";
      else if (roleCat === "ENGINEERING") roleIcon = "fa-code";

      return `
        <div class="job-item ${isNew ? 'job-item-new' : ''}">
          <div class="job-item-left">
            <div class="job-item-title">
              <i class="fa-solid ${roleIcon}" style="color: #60a5fa; width: 14px;"></i>
              <a href="${escapeHtml(j.url || '#')}" target="_blank" rel="noopener noreferrer">
                ${escapeHtml(j.title || 'Untitled Quantitative Role')}
              </a>
              ${isNew ? `<span class="badge-pill pill-status-new">NEW</span>` : ''}
              ${isInactive ? `<span class="badge-pill pill-status-inactive">CLOSED</span>` : ''}
            </div>

            <div class="job-item-sub">
              ${j.location ? `<span><i class="fa-solid fa-location-dot"></i> ${escapeHtml(j.location)}</span>` : ''}
              ${j.department ? `<span>&bull;</span><span>${escapeHtml(j.department)}</span>` : ''}
              ${j.posted_pay_range ? `<span>&bull;</span><span class="job-salary"><i class="fa-solid fa-dollar-sign"></i> ${escapeHtml(j.posted_pay_range)}</span>` : ''}
              ${j.first_seen ? `<span>&bull;</span><span style="color: #64748b;">Discovered ${new Date(j.first_seen).toLocaleDateString()}</span>` : ''}
            </div>
          </div>

          <div class="job-item-right">
            <div class="score-badge ${scoreClass}" title="${escapeHtml(j.recommendation || 'Scored via Quantitative Relevance Engine')}">
              <i class="fa-solid fa-crosshairs"></i>
              <span>${score}% Fit</span>
            </div>

            ${isInactive ? `
              <span class="btn-apply-disabled" title="${escapeHtml(j.inactive_reason || 'Page unlisted or closed')}">
                <span>Closed</span>
                <i class="fa-solid fa-ban"></i>
              </span>
            ` : `
              <a href="${escapeHtml(j.url || '#')}" target="_blank" rel="noopener noreferrer" class="btn-apply">
                <span>Apply Now</span>
                <i class="fa-solid fa-arrow-up-right-from-square"></i>
              </a>
            `}
          </div>
        </div>
      `;
    }).join("");

    let crawlBadge = "";
    if (comp.crawl_status === "AUTOMATED_FEED") {
      crawlBadge = `<span class="badge-pill pill-crawl-auto" title="Automated live feed: ${escapeHtml(comp.crawl_method || 'ATS API')}"><i class="fa-solid fa-bolt"></i> Live Feed</span>`;
    } else {
      const reasonTitle = comp.uncrawlable_reason ? `Crawling restricted: ${comp.uncrawlable_reason}` : "Direct Portal Monitored";
      crawlBadge = `<span class="badge-pill pill-crawl-portal" title="${escapeHtml(reasonTitle)}"><i class="fa-solid fa-lock"></i> Portal Monitored</span>`;
    }

    return `
      <div class="company-card ${isExpanded ? 'expanded' : ''}" id="company-card-${firmKey}" data-firm-key="${firmKey}">
        <div class="company-header-row" onclick="toggleCompany('${firmKey}')">
          <div class="company-meta-left">
            <div class="company-title-wrap">
              <div class="company-name">
                <i class="fa-solid fa-building" style="color: #3b82f6; font-size: 1.05rem;"></i>
                <span>${escapeHtml(comp.firm_name)}</span>
              </div>
              <div class="company-badges">
                <span class="badge-pill ${tierBadgeClass}">${escapeHtml(pTier ? pTier.split(':')[0] : comp.priority_tag)}</span>
                <span class="badge-pill pill-industry"><i class="fa-solid fa-building-columns"></i> ${escapeHtml(comp.industry_sector)}</span>
                ${crawlBadge}
                ${comp.has_new ? `<span class="badge-pill pill-status-new"><i class="fa-solid fa-sparkles"></i> NEW ROLES</span>` : ''}
                ${comp.official_careers_url ? `
                  <a href="${escapeHtml(comp.official_careers_url)}" target="_blank" rel="noopener noreferrer" class="btn-official-career" onclick="event.stopPropagation()">
                    <i class="fa-solid fa-arrow-up-right-from-square"></i> Official Careers Page
                  </a>
                ` : ''}
              </div>
            </div>

            <div class="company-comp-summary">
              <span>Benchmark Comp: <strong>${escapeHtml(comp.estimated_comp)}</strong></span>
              <span style="color: #4b5563;">&bull;</span>
              <span style="color: #34d399;">${escapeHtml(comp.comp_benchmark_delta)}</span>
            </div>
          </div>

          <div class="company-meta-right">
            ${comp.jobs.length > 0 ? `
              <div class="score-badge ${topScoreClass}" title="Top Role Fit Score">
                <i class="fa-solid fa-crosshairs"></i>
                <span>${comp.max_score}% Top Match</span>
              </div>

              <div class="openings-count-pill">
                <i class="fa-solid fa-briefcase"></i>
                <span>${comp.jobs.length} ${comp.jobs.length === 1 ? 'Role' : 'Roles'}</span>
              </div>
            ` : `
              <div class="openings-count-pill zero-roles" title="${comp.crawl_status === 'AUTOMATED_FEED' ? 'Automated Feeds Monitored' : (comp.uncrawlable_reason || 'Direct Portal Monitored')}">
                <i class="${comp.crawl_status === 'AUTOMATED_FEED' ? 'fa-solid fa-clock-rotate-left' : 'fa-solid fa-shield-halved'}"></i>
                <span>${comp.crawl_status === 'AUTOMATED_FEED' ? '0 Active Roles Monitored' : 'Direct Portal Monitored'}</span>
              </div>
            `}

            <div class="chevron-toggle">
              <i class="fa-solid fa-chevron-down"></i>
            </div>
          </div>
        </div>

        <div class="company-jobs-drawer">
          ${comp.jobs.length > 0 ? `
            <div class="drawer-header">
              <span>Available Full-Time Entry-Level / Junior Postings (${comp.jobs.length})</span>
              <span style="font-size: 0.72rem; color: #64748b;">Click to apply directly on verified portal</span>
            </div>
            <div class="drawer-jobs-list">
              ${jobsHtml}
            </div>
          ` : (comp.crawl_status !== "AUTOMATED_FEED" ? `
            <div class="drawer-empty-msg drawer-uncrawlable-msg">
              <div style="display: flex; align-items: center; justify-content: center; gap: 8px; color: #fbbf24; font-weight: 700; margin-bottom: 6px;">
                <i class="fa-solid fa-shield-halved fa-lg"></i>
                <span>Automated Public Crawling Restricted &bull; ${escapeHtml(comp.uncrawlable_reason || 'Enterprise Security / Custom Portal')}</span>
              </div>
              <p style="margin: 0 auto; font-size: 0.82rem; color: #cbd5e1; max-width: 640px; line-height: 1.5;">
                This employer utilizes enterprise session security, internal Workday/Taleo authentication, or custom portal architecture that restricts automated public API scraping. Browse off-cycle and campus opportunities directly on their verified portal:
              </p>
              ${comp.official_careers_url ? `
                <div style="margin-top: 14px;">
                  <a href="${escapeHtml(comp.official_careers_url)}" target="_blank" rel="noopener noreferrer" class="btn-official-career" style="padding: 8px 18px; font-size: 0.85rem; font-weight: 700; background: #2563eb; color: #fff; border-color: #2563eb;">
                    <i class="fa-solid fa-arrow-up-right-from-square"></i> Open ${escapeHtml(comp.firm_name)} Official Careers Portal
                  </a>
                </div>
              ` : ''}
            </div>
          ` : `
            <div class="drawer-empty-msg">
              <i class="fa-solid fa-radar fa-lg" style="color: #60a5fa; margin-bottom: 8px; display: block;"></i>
              <strong>Automated ATS &amp; Web Feeds Active for ${escapeHtml(comp.firm_name)}</strong>
              <p style="margin-top: 6px; font-size: 0.82rem;">Public ATS feed (${escapeHtml(comp.crawl_method || 'API')}) is actively monitored. Currently 0 entry-level or junior quantitative positions are listed. Check their portal directly for off-cycle updates:</p>
              ${comp.official_careers_url ? `
                <div style="margin-top: 12px;">
                  <a href="${escapeHtml(comp.official_careers_url)}" target="_blank" rel="noopener noreferrer" class="btn-official-career">
                    <i class="fa-solid fa-arrow-up-right-from-square"></i> Visit ${escapeHtml(comp.firm_name)} Official Careers Page
                  </a>
                </div>
              ` : ''}
            </div>
          `)}
        </div>
      </div>
    `;
  }).join("");
}

async function triggerFirmCrawl() {
  const select = document.getElementById("select-firm-crawl");
  const firm = select.value;
  if (!firm) {
    alert("Please select a firm from the dropdown first.");
    return;
  }

  const toast = document.getElementById("crawl-toast");
  const toastText = document.getElementById("toast-text");
  const btn = document.getElementById("btn-run-firm-crawl");

  toastText.innerText = `Dispatching tailored subagent for ${firm}...`;
  toast.style.display = "inline-flex";
  btn.disabled = true;

  try {
    const res = await fetch(`/api/crawl?firm=${encodeURIComponent(firm)}`, { method: "POST" });
    if (res.ok) {
      const data = await res.json();
      await loadData();
      alert(`Tailored crawl complete for ${firm}! Processed ${data.jobs_count || data.openings?.length || 0} openings.`);
    } else {
      alert(`Note: On static GitHub Pages, live background scraping is managed automatically by GitHub Actions. To run a real-time local crawl on demand, run 'python main.py web' on your computer.`);
    }
  } catch (err) {
    alert(`Note: On static GitHub Pages, live background scraping is managed automatically by GitHub Actions. To run a real-time local crawl on demand, run 'python main.py web' on your computer.`);
  } finally {
    toast.style.display = "none";
    btn.disabled = false;
  }
}

async function triggerCrawl() {
  const toast = document.getElementById("crawl-toast");
  const toastText = document.getElementById("toast-text");
  const btn = document.getElementById("btn-run-crawl");
  
  toastText.innerText = "Executing crawl agents across target boards & tailored subagents...";
  toast.style.display = "inline-flex";
  btn.disabled = true;

  try {
    const res = await fetch("/api/crawl", { method: "POST" });
    if (res.ok) {
      const data = await res.json();
      allOpenings = data.openings || [];
      trackerMeta = data;
      updateStats();
      renderCards();
      alert(`Crawl completed! Discovered ${data.stats.total_live_openings} openings (${data.stats.new_openings_this_crawl} new).`);
    } else {
      alert(`Note: On static GitHub Pages, live background scraping is managed automatically by GitHub Actions. To run a real-time local crawl on demand, run 'python main.py web' on your computer.`);
    }
  } catch (err) {
    alert(`Note: On static GitHub Pages, live background scraping is managed automatically by GitHub Actions. To run a real-time local crawl on demand, run 'python main.py web' on your computer.`);
  } finally {
    toast.style.display = "none";
    btn.disabled = false;
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
