// Quant Career Intelligence v2: Live Client State & Hierarchical Company List View
let allOpenings = [];
let trackerMeta = {};
let expandedCompanies = new Set();
let isAllExpanded = false;

document.addEventListener("DOMContentLoaded", () => {
  loadData();
});

async function loadData() {
  try {
    const res = await fetch("/api/openings");
    if (res.ok) {
      const data = await res.json();
      allOpenings = data.openings || [];
      trackerMeta = data;
      populateIndustryFilter();
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
    populateIndustryFilter();
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

const SECTOR_DEFINITIONS = [
  { key: "FinTech & Elite Tech", label: "FinTech & Elite Tech (Coinbase, Robinhood, Stripe, Databricks, etc.)" },
  { key: "Proprietary Trading & Market Making", label: "Proprietary Trading & Market Making (Jane Street, Jump, SIG, DRW, etc.)" },
  { key: "Quantitative Hedge Funds", label: "Quantitative Hedge Funds (Two Sigma, Millennium, Point72, AQR, etc.)" },
  { key: "Bulge Bracket & Global Investment Banks", label: "Bulge Bracket & Global Investment Banks (Goldman Sachs, Morgan Stanley, JPM, etc.)" },
  { key: "Systematic Asset Management & Allocators", label: "Systematic Asset Management & Allocators (BlackRock, PIMCO, etc.)" },
  { key: "Commodities & Energy Trading Desks", label: "Commodities & Energy Trading Desks (Trafigura, Mercuria, Castleton, etc.)" },
  { key: "Financial Data & Market Utilities", label: "Financial Data & Market Utilities (Bloomberg, CME Group, FactSet, etc.)" },
  { key: "Commercial Banking & Consulting (Practice)", label: "Commercial Banking & Consulting (Practice) (Accenture, Big 4, etc.)" }
];

function populateIndustryFilter() {
  const select = document.getElementById("filter-industry");
  if (!select) return;
  const currentVal = select.value;

  select.innerHTML = '<option value="ALL" selected>All Industry Sectors</option>' +
    SECTOR_DEFINITIONS.map(s => `<option value="${escapeHtml(s.key)}">${escapeHtml(s.label)}</option>`).join('');

  if (currentVal && (currentVal === "ALL" || SECTOR_DEFINITIONS.some(s => s.key === currentVal))) {
    select.value = currentVal;
  }
}

function updateStats() {
  const activeCount = allOpenings.filter(j => j.status !== "INACTIVE").length;
  const high = allOpenings.filter(j => (j.suitability_score || 0) >= 80).length;
  const newlyDiscovered = allOpenings.filter(j => j.status === "NEW").length;
  const hiringFirms = new Set(allOpenings.filter(j => j.status !== "INACTIVE").map(j => j.firm_name)).size;
  const totalMonitoredFirms = (trackerMeta.firms_directory ? trackerMeta.firms_directory.length : (trackerMeta.stats ? trackerMeta.stats.total_monitored_firms : 296)) || 296;

  if (document.getElementById("stat-total")) document.getElementById("stat-total").innerText = activeCount;
  if (document.getElementById("stat-high")) document.getElementById("stat-high").innerText = high;
  if (document.getElementById("stat-new")) document.getElementById("stat-new").innerText = newlyDiscovered;
  if (document.getElementById("stat-firms")) document.getElementById("stat-firms").innerText = totalMonitoredFirms;
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

function renderCards() {
  const container = document.getElementById("jobs-container");
  const search = document.getElementById("filter-search").value.toLowerCase().trim();
  const sortOption = document.getElementById("filter-sort") ? document.getElementById("filter-sort").value : "newest";
  const viewScope = document.getElementById("filter-view-scope") ? document.getElementById("filter-view-scope").value : "ALL_FIRMS";
  const tierFilter = document.getElementById("filter-tier").value;
  const industryFilter = document.getElementById("filter-industry") ? document.getElementById("filter-industry").value : "ALL";
  const scoreFilter = document.getElementById("filter-score").value;
  const statusFilter = document.getElementById("filter-status").value;

  // 1. Filter individual openings
  const filteredJobs = allOpenings.filter(job => {
    // Text search
    if (search) {
      const matchText = `${job.firm_name} ${job.title} ${job.location} ${job.department || ''} ${job.industry_sector || ''} ${job.posted_pay_range || ''}`.toLowerCase();
      if (!matchText.includes(search)) return false;
    }

    // Priority Tier
    if (tierFilter !== "ALL") {
      const jobTier = job.priority_tier || "";
      if (!jobTier.includes(tierFilter)) return false;
    }

    // Industry Sector
    if (industryFilter !== "ALL") {
      const jobSector = job.industry_sector || "";
      if (jobSector !== industryFilter && !jobSector.toLowerCase().includes(industryFilter.toLowerCase())) return false;
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
        has_new: false,
        max_score: 0,
        latest_date: null,
        jobs: []
      });
    }

    const group = companyMap.get(firm);
    group.jobs.push(job);
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

  // Apply filters to companies when in ALL_FIRMS mode
  if (tierFilter !== "ALL") {
    companies = companies.filter(c => (c.priority_tier || "").includes(tierFilter));
  }
  if (industryFilter !== "ALL") {
    companies = companies.filter(c => {
      const sec = c.industry_sector || "";
      return sec === industryFilter || sec.toLowerCase().includes(industryFilter.toLowerCase());
    });
  }
  if (viewScope === "ACTIVE_ONLY") {
    companies = companies.filter(c => c.jobs.length > 0);
  }
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
        <p style="margin-top: 10px; font-weight: 600;">No postings or firms matched your filter criteria.</p>
        <p style="font-size: 0.85rem; color: #9ca3af; margin-top: 4px;">
          Try adjusting the filter options or clearing the search query.
        </p>
      </div>
    `;
    return;
  }

  // 4. Render Company List View with Expandable 2nd Layer
  container.innerHTML = companies.map(comp => {
    const firmKey = encodeURIComponent(comp.firm_name.replace(/\s+/g, "_"));
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
    else if (comp.max_score >= 60) topScoreClass = "score-med";

    // Sort company jobs: highest score first, then NEW status
    const sortedJobs = comp.jobs.slice().sort((j1, j2) => {
      if (j1.status === "NEW" && j2.status !== "NEW") return -1;
      if (j2.status === "NEW" && j1.status !== "NEW") return 1;
      return (j2.suitability_score || 0) - (j1.suitability_score || 0);
    });

    const jobsHtml = sortedJobs.map(j => {
      const score = j.suitability_score || 0;
      let jScoreClass = "score-low";
      if (score >= 80) jScoreClass = "score-high";
      else if (score >= 60) jScoreClass = "score-med";

      const isInactive = j.status === "INACTIVE";
      const isNew = j.status === "NEW";

      let statusBadge = `<span class="badge-pill pill-status-active"><i class="fa-solid fa-circle-check"></i> ACTIVE</span>`;
      if (isInactive) {
        statusBadge = `<span class="badge-pill pill-status-inactive" title="${escapeHtml(j.inactive_reason || 'Page closed')}"><i class="fa-solid fa-circle-xmark"></i> INACTIVE</span>`;
      } else if (isNew) {
        statusBadge = `<span class="badge-pill pill-status-new"><i class="fa-solid fa-sparkles"></i> NEW</span>`;
      }

      let payRangeBadge = "";
      if (j.posted_pay_range) {
        payRangeBadge = `<span class="pill-pay-posted" title="Stated compensation disclosure from employer posting"><i class="fa-solid fa-money-bill-wave"></i> Stated Base: ${escapeHtml(j.posted_pay_range)}</span>`;
      }

      const signalsList = (j.matched_signals || []).slice(0, 2).map(s => `<li>${escapeHtml(s)}</li>`).join("");

      return `
        <div class="job-subcard ${isInactive ? 'inactive-posting' : ''}">
          <div class="job-main-info">
            <div class="job-main-title">
              <span>${escapeHtml(j.title)}</span>
              ${statusBadge}
              ${payRangeBadge}
            </div>

            <div class="job-main-meta">
              <span class="meta-item"><i class="fa-solid fa-location-dot"></i> ${escapeHtml(j.location || 'NYC / US')}</span>
              ${j.department ? `<span class="meta-item"><i class="fa-solid fa-layer-group"></i> ${escapeHtml(j.department)}</span>` : ''}
              <span class="meta-item"><i class="fa-solid fa-cube"></i> ${escapeHtml(j.source_ats || 'Official Portal')}</span>
              <span class="meta-item" style="color: #60a5fa;"><i class="fa-solid fa-bullseye"></i> ${escapeHtml(j.verdict || 'Target Match')}</span>
            </div>

            ${signalsList ? `
              <div style="font-size: 0.74rem; color: #94a3b8; margin-top: 4px;">
                <ul style="padding-left: 14px; margin: 0; display: flex; gap: 16px; flex-wrap: wrap;">${signalsList}</ul>
              </div>
            ` : ''}
          </div>

          <div class="job-action-right">
            <div class="score-badge ${jScoreClass}">
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
              <div class="openings-count-pill zero-roles" title="Monitored ATS Endpoints">
                <i class="fa-solid fa-clock-rotate-left"></i>
                <span>0 Active Roles Monitored</span>
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
          ` : `
            <div class="drawer-empty-msg">
              <i class="fa-solid fa-radar fa-lg" style="color: #60a5fa; margin-bottom: 8px; display: block;"></i>
              <strong>Currently Monitoring Public ATS & Web Feeds for ${escapeHtml(comp.firm_name)}</strong>
              <p style="margin-top: 6px; font-size: 0.82rem;">No active full-time junior or new-grad quantitative roles currently detected on public boards. Check their official careers portal directly:</p>
              ${comp.official_careers_url ? `
                <div style="margin-top: 12px;">
                  <a href="${escapeHtml(comp.official_careers_url)}" target="_blank" rel="noopener noreferrer" class="btn-official-career">
                    <i class="fa-solid fa-arrow-up-right-from-square"></i> Visit ${escapeHtml(comp.firm_name)} Official Careers Page
                  </a>
                </div>
              ` : ''}
            </div>
          `}
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
      alert(`Note: On static GitHub Pages, live background scraping is managed automatically by GitHub Actions (runs every 12h or manually in the Actions tab). To run an instant local crawl on demand, run 'python main.py web' on your computer.`);
    }
  } catch (err) {
    alert(`Note: On static GitHub Pages, live background scraping is executed automatically by GitHub Actions. To run a real-time local crawl on demand, run 'python main.py web' on your computer.`);
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
      alert(`Note: On static GitHub Pages, live background scraping is managed automatically by GitHub Actions (runs every 12h or manually in the Actions tab). To run an instant local crawl on demand, run 'python main.py web' on your computer.`);
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
