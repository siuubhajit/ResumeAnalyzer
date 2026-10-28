/**
 * Resume Analyzer - Interactive Improvement Assistant Controller
 */

const AppAssistant = {
  init() {
    this.bindEvents();
  },

  bindEvents() {
    const rephraseBtn = document.getElementById('rephrase-bullet-btn');
    const bulletInput = document.getElementById('bullet-input');

    if (rephraseBtn && bulletInput) {
      rephraseBtn.addEventListener('click', async () => {
        const text = bulletInput.value.trim();
        if (!text) {
          alert('Please enter a resume bullet point or accomplishment statement first.');
          bulletInput.focus();
          return;
        }

        rephraseBtn.disabled = true;
        rephraseBtn.innerHTML = `<span>Rewriting...</span>`;

        try {
          const res = await fetch('/api/improve-bullet', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ bullet: text })
          });

          const data = await res.json();
          if (data.success) {
            this.renderRewrites(data.rewrites);
          } else {
            alert(data.error || 'Failed to rewrite bullet.');
          }
        } catch (err) {
          alert('Error contacting improvement service: ' + err.message);
        } finally {
          rephraseBtn.disabled = false;
          rephraseBtn.innerHTML = `
            <img src="/static/icons/zap.svg" alt="Zap" class="svg-icon-sm">
            <span>Rephrase with Metrics & Action Verbs</span>
          `;
        }
      });
    }

    // Copy Tailored Summary button
    const copySummaryBtn = document.getElementById('copy-summary-btn');
    if (copySummaryBtn) {
      copySummaryBtn.addEventListener('click', () => {
        const summaryText = document.getElementById('ai-tailored-summary')?.innerText;
        if (summaryText) {
          navigator.clipboard.writeText(summaryText).then(() => {
            copySummaryBtn.innerHTML = `
              <img src="/static/icons/check-circle.svg" alt="Copied" class="svg-icon-xs">
              <span>Copied!</span>
            `;
            setTimeout(() => {
              copySummaryBtn.innerHTML = `
                <img src="/static/icons/copy.svg" alt="Copy" class="svg-icon-xs">
                <span>Copy</span>
              `;
            }, 2000);
          });
        }
      });
    }
  },

  renderRewrites(rewrites) {
    const container = document.getElementById('bullet-results-box');
    if (!container) return;

    if (!rewrites || rewrites.length === 0) {
      container.innerHTML = `<p style="color: var(--text-muted);">No rewrites generated.</p>`;
      return;
    }

    container.innerHTML = rewrites.map(rw => `
      <div class="rewrite-card">
        <div style="display: flex; align-items: center; justify-content: space-between;">
          <span class="rewrite-card-badge">${escapeHtml(rw.version)} (${escapeHtml(rw.focus)})</span>
          <button class="btn-copy btn-copy-bullet" data-text="${escapeHtml(rw.text)}" title="Copy text">
            <img src="/static/icons/copy.svg" alt="Copy" class="svg-icon-xs">
            <span>Copy</span>
          </button>
        </div>
        <p class="rewrite-card-text">${escapeHtml(rw.text)}</p>
      </div>
    `).join('');

    container.querySelectorAll('.btn-copy-bullet').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const text = e.currentTarget.getAttribute('data-text');
        navigator.clipboard.writeText(text).then(() => {
          btn.innerHTML = `<span>Copied!</span>`;
          setTimeout(() => {
            btn.innerHTML = `
              <img src="/static/icons/copy.svg" alt="Copy" class="svg-icon-xs">
              <span>Copy</span>
            `;
          }, 1500);
        });
      });
    });
  }
};

