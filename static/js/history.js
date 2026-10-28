/**
 * Resume Analyzer - History & Report Export Controller
 */

const AppHistory = {
  STORAGE_KEY: 'resume_analyzer_history',

  init() {
    this.updateBadge();
    this.bindEvents();
  },

  bindEvents() {
    const openBtn = document.getElementById('open-history-btn');
    const closeBtn = document.getElementById('close-history-btn');
    const modal = document.getElementById('history-modal');
    const clearBtn = document.getElementById('clear-history-btn');
    const printBtn = document.getElementById('print-report-btn');
    const exportJsonBtn = document.getElementById('export-json-btn');
    const saveHistoryBtn = document.getElementById('save-history-btn');

    if (openBtn) {
      openBtn.addEventListener('click', () => {
        this.renderHistoryList();
        modal.classList.remove('hidden');
      });
    }

    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        modal.classList.add('hidden');
      });
    }

    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.classList.add('hidden');
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        if (confirm('Are you sure you want to clear your saved analysis history?')) {
          localStorage.removeItem(this.STORAGE_KEY);
          this.renderHistoryList();
          this.updateBadge();
        }
      });
    }

    if (printBtn) {
      printBtn.addEventListener('click', () => {
        window.print();
      });
    }

    if (exportJsonBtn) {
      exportJsonBtn.addEventListener('click', () => {
        if (!window.currentAnalysisResult) {
          alert('No active analysis to export.');
          return;
        }
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(window.currentAnalysisResult, null, 2));
        const downloadAnchor = document.createElement('a');
        downloadAnchor.setAttribute("href", dataStr);
        const candidate = window.currentAnalysisResult.candidate_profile?.contact?.name || "resume";
        downloadAnchor.setAttribute("download", `resume_analysis_${candidate.toLowerCase().replace(/\s+/g, '_')}.json`);
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        downloadAnchor.remove();
      });
    }

    if (saveHistoryBtn) {
      saveHistoryBtn.addEventListener('click', () => {
        if (!window.currentAnalysisResult) return;
        this.saveAnalysis(window.currentAnalysisResult);
        alert('Analysis successfully saved to your local history!');
      });
    }
  },

  getAll() {
    try {
      const data = localStorage.getItem(this.STORAGE_KEY);
      return data ? JSON.parse(data) : [];
    } catch (e) {
      return [];
    }
  },

  saveAnalysis(resultData) {
    const list = this.getAll();
    const candidateName = resultData.candidate_profile?.contact?.name || resultData.filename || 'Candidate Resume';
    
    const entry = {
      id: 'res_' + Date.now(),
      timestamp: new Date().toLocaleString(),
      candidateName: candidateName,
      filename: resultData.filename,
      overallScore: resultData.analysis?.overall_match_percentage || 0,
      atsScore: resultData.analysis?.ats_audit?.score || 0,
      matchedCount: resultData.analysis?.matched_skills?.length || 0,
      missingCount: resultData.analysis?.missing_skills?.length || 0,
      data: resultData
    };

    // Prepend to top and keep up to 15 entries
    list.unshift(entry);
    if (list.length > 15) list.pop();

    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(list));
    this.updateBadge();
  },

  updateBadge() {
    const badge = document.getElementById('history-count-badge');
    if (badge) {
      const count = this.getAll().length;
      badge.textContent = count;
      badge.style.display = count > 0 ? 'inline-block' : 'none';
    }
  },

  renderHistoryList() {
    const container = document.getElementById('history-list');
    if (!container) return;

    const list = this.getAll();
    if (list.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 2rem 1rem; color: var(--text-muted);">
          <p>No saved analyses found.</p>
          <p style="font-size: 0.8rem; margin-top: 0.4rem;">Run an analysis and click "Save to History" to review it later.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = list.map(item => {
      let scoreBadgeClass = 'badge-pill-success';
      if (item.overallScore < 50) scoreBadgeClass = 'badge-pill-warning';
      else if (item.overallScore < 75) scoreBadgeClass = 'badge-pill-info';

      return `
        <div class="history-item">
          <div class="history-info">
            <span class="history-filename">${escapeHtml(item.candidateName)}</span>
            <span class="history-meta">${escapeHtml(item.filename)} • ${escapeHtml(item.timestamp)}</span>
            <span class="history-meta" style="color: var(--text-secondary);">
              Matched: ${item.matchedCount} • Missing: ${item.missingCount} • ATS: ${item.atsScore}/100
            </span>
          </div>
          <div class="history-scores">
            <span class="${scoreBadgeClass}">${item.overallScore}%</span>
            <button class="btn-action-outline btn-load-history" data-id="${item.id}" title="Load this analysis">
              Load
            </button>
          </div>
        </div>
      `;
    }).join('');

    // Attach load handlers
    container.querySelectorAll('.btn-load-history').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const id = e.currentTarget.getAttribute('data-id');
        this.loadEntry(id);
      });
    });
  },

  loadEntry(id) {
    const list = this.getAll();
    const entry = list.find(item => item.id === id);
    if (entry && entry.data) {
      window.currentAnalysisResult = entry.data;
      if (typeof window.renderAnalysisResults === 'function') {
        window.renderAnalysisResults(entry.data);
      }
      const modal = document.getElementById('history-modal');
      if (modal) modal.classList.add('hidden');
      const resultsSection = document.getElementById('results-dashboard');
      if (resultsSection) {
        resultsSection.scrollIntoView({ behavior: 'smooth' });
      }
    }
  }
};

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

