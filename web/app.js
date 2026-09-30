// State
let allOpenings = [];
let trackerMeta = {};

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
      updateStats();
      renderCards();
      return;
    }
  } catch (err) {
    console.warn("API /api/openings unavailable, falling back to static window.LIVE_OPENINGS_DATA if available.");
  }

  // Fallback to static window object if data.js is loaded
  if (window.LIVE_OPENINGS_DATA && window.LIVE_OPENINGS_DATA.openings) {
    allOpenings = window.LIVE_OPENINGS_DATA.openings;
    trackerMeta = window.LIVE_OPENINGS_DATA;
    updateStats();
    renderCards();
  } else {
    document.getElementById("jobs-container").innerHTML = `
      <div class="empty-state">
        <i class="fa-solid fa-triangle-exclamation fa-2x" style="color: #f59e0b;"></i>
        <p style="margin-top: 10px; font-weight: 600;">No live openings dataset found.</p>
        <p style="font-size: 0.85rem; color: #9ca3af; margin-top: 4px;">
          Click <strong>Run Crawl Agent</strong> above or run <code>python main.py crawl</code> to populate live jobs.
        </p>
      </div>
    `;
  }
}

function updateStats() {
  const total = allOpenings.length;
  const high = allOpenings.filter(j => (j.suitability_score || 0) >= 80).length;
  const newlyDiscovered = allOpenings.filter(j => j.status === "NEW").length;
  const uniqueFirms = new Set(allOpenings.map(j => j.firm_name)).size;

  document.getElementById("stat-total").innerText = total;
  document.getElementById("stat-high").innerText = high;
  document.getElementById("stat-new").innerText = newlyDiscovered;
  document.getElementById("stat-firms").innerText = uniqueFirms;

  if (trackerMeta.last_updated) {
    const d = new Date(trackerMeta.last_updated);
    document.getElementById("last-updated-label").innerText = `Last Agent Crawl: ${d.toLocaleString()}`;
  }
}

function renderCards() {
  const container = document.getElementById("jobs-container");
  const search = document.getElementById("filter-search").value.toLowerCase().trim();
  const tierFilter = document.getElementById("filter-tier").value;
  const scoreFilter = document.getElementById("filter-score").value;
  const statusFilter = document.getElementById("filter-status").value;

  const filtered = allOpenings.filter(job => {
    // Text search
    if (search) {
      const matchText = `${job.firm_name} ${job.title} ${job.location} ${job.department || ''}`.toLowerCase();
      if (!matchText.includes(search)) return false;
    }

    // Tier
    if (tierFilter !== "ALL") {
      const jobTier = job.priority_tier || "";
      if (!jobTier.includes(tierFilter)) return false;
    }

    // Score
    if (scoreFilter !== "ALL") {
      const minScore = parseInt(scoreFilter, 10);
      if ((job.suitability_score || 0) < minScore) return false;
    }

    // Status
    if (statusFilter !== "ALL") {
      if (job.status !== statusFilter) return false;
    }

    return true;
  });

  document.getElementById("feed-count-label").innerText = `Showing ${filtered.length} of ${allOpenings.length} Positions`;

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <i class="fa-solid fa-folder-open fa-2x"></i>
        <p style="margin-top: 10px;">No postings matched your filter criteria.</p>
        <p style="font-size: 0.85rem; color: #9ca3af;">Try adjusting the priority tier or lowering the suitability threshold.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(j => {
    const score = j.suitability_score || 0;
    let scoreClass = "score-low";
    if (score >= 80) scoreClass = "score-high";
    else if (score >= 60) scoreClass = "score-med";

    let tierBadgeClass = "pill-tier-b";
    if ((j.priority_tier || "").includes("Tier A")) tierBadgeClass = "pill-tier-a";
    else if ((j.priority_tier || "").includes("Tier C")) tierBadgeClass = "pill-tier-c1";

    const isNew = j.status === "NEW";
    const statusBadge = isNew
      ? `<span class="badge-pill pill-status-new"><i class="fa-solid fa-sparkles"></i> NEW</span>`
      : `<span class="badge-pill pill-status-active"><i class="fa-solid fa-circle-check"></i> ACTIVE</span>`;

    const signalsList = (j.matched_signals || []).slice(0, 3).map(s => `<li>${escapeHtml(s)}</li>`).join("");

    return `
      <div class="job-card">
        <div class="job-card-top">
          <div>
            <div class="firm-name">
              <span>${escapeHtml(j.firm_name)}</span>
              ${statusBadge}
            </div>
            <div class="job-title">${escapeHtml(j.title)}</div>
          </div>
          <div class="score-badge ${scoreClass}">
            <i class="fa-solid fa-crosshairs"></i>
            <span>${score}% Fit</span>
          </div>
        </div>

        <div class="job-meta-row">
          <span class="meta-item"><i class="fa-solid fa-location-dot"></i> ${escapeHtml(j.location || 'NYC / US')}</span>
          ${j.department ? `<span class="meta-item"><i class="fa-solid fa-layer-group"></i> ${escapeHtml(j.department)}</span>` : ''}
          <span class="meta-item"><i class="fa-solid fa-cube"></i> ${escapeHtml(j.source_ats || 'Official Portal')}</span>
        </div>

        <div class="badges-row">
          <span class="badge-pill ${tierBadgeClass}">${escapeHtml(j.priority_tag || 'Main Focus')}</span>
          <span class="badge-pill" style="background: rgba(255,255,255,0.06); color: #cbd5e1;">${escapeHtml(j.verdict || 'Target Match')}</span>
        </div>

        <div class="comp-box">
          <div>
            <div style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase;">Benchmark First-Year Comp</div>
            <div class="comp-val">${escapeHtml(j.estimated_comp || '$220,000 - $380,000+')}</div>
          </div>
          <div class="comp-delta">${escapeHtml(j.comp_delta_vs_c1 || 'Premier Quant Band')}</div>
        </div>

        ${signalsList ? `
          <div style="font-size: 0.76rem; color: #94a3b8; background: rgba(0,0,0,0.2); padding: 8px 12px; border-radius: 6px;">
            <div style="font-weight: 600; color: #cbd5e1; margin-bottom: 2px;">Key Match Heuristics:</div>
            <ul style="padding-left: 14px; margin: 0;">${signalsList}</ul>
          </div>
        ` : ''}

        <div class="job-footer">
          <span style="font-size: 0.72rem; color: #6b7280;">ID: ${escapeHtml(j.job_id || 'ext')}</span>
          <a href="${escapeHtml(j.url || '#')}" target="_blank" rel="noopener noreferrer" class="btn-apply">
            <span>Apply Now</span>
            <i class="fa-solid fa-arrow-up-right-from-square"></i>
          </a>
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
