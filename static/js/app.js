/**
 * Resume Analyzer - Main Application Controller
 */

// Global state
window.currentAnalysisResult = null;
let selectedFile = null;
let activeSampleId = null;

document.addEventListener('DOMContentLoaded', () => {
  AppTheme.init();
  AppHistory.init();
  AppAssistant.init();
  AppCore.init();
});

/* --------------------------------------------------------------------------
   Theme Controller
   -------------------------------------------------------------------------- */
const AppTheme = {
  init() {
    const savedTheme = localStorage.getItem('resume_analyzer_theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const initialTheme = savedTheme || (prefersDark ? 'dark' : 'light');

    this.setTheme(initialTheme);

    const toggleBtn = document.getElementById('theme-toggle-btn');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
      });
    }
  },

  setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('resume_analyzer_theme', theme);

    // Refresh charts if rendered
    if (window.currentAnalysisResult) {
      const score = window.currentAnalysisResult.analysis?.overall_match_percentage;
      const cats = window.currentAnalysisResult.analysis?.category_breakdown;
      AppCharts.refreshTheme(score, cats);
    }
  }
};

/* --------------------------------------------------------------------------
   Core Application Controller
   -------------------------------------------------------------------------- */
const AppCore = {
  sampleJobs: [],

  init() {
    this.bindDropzone();
    this.bindJobTextarea();
    this.bindSampleButtons();
    this.loadSampleJobs();
    this.bindTabs();
    this.bindForm();
    this.bindAlert();
  },

  /* Dropzone and File Upload */
  bindDropzone() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('resume-file-input');
    const removeFileBtn = document.getElementById('remove-file-btn');

    if (!dropzone || !fileInput) return;

    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.classList.add('drag-over');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.classList.remove('drag-over');
      });
    });

    dropzone.addEventListener('drop', (e) => {
      const files = e.dataTransfer.files;
      if (files && files.length > 0) {
        this.handleFileSelection(files[0]);
      }
    });

    fileInput.addEventListener('change', (e) => {
      if (fileInput.files && fileInput.files.length > 0) {
        this.handleFileSelection(fileInput.files[0]);
      }
    });

    if (removeFileBtn) {
      removeFileBtn.addEventListener('click', () => {
        this.clearFileSelection();
      });
    }
  },

  handleFileSelection(file) {
    // Validate file type
    if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
      this.showAlert('Invalid file format. Please upload a PDF document (.pdf).', 'danger');
      return;
    }

    // Validate size (10 MB limit)
    if (file.size > 10 * 1024 * 1024) {
      this.showAlert('File exceeds the 10 MB limit. Please select a smaller resume file.', 'danger');
      return;
    }

    selectedFile = file;
    activeSampleId = null;

    // Reset sample resume active state
    document.querySelectorAll('.btn-sample-resume').forEach(b => b.classList.remove('active'));
    document.getElementById('sample-active-indicator')?.classList.add('hidden');

    // Display selected file card
    document.getElementById('dropzone')?.classList.add('hidden');
    const fileCard = document.getElementById('selected-file-card');
    if (fileCard) {
      fileCard.classList.remove('hidden');
      document.getElementById('selected-filename').textContent = file.name;
      document.getElementById('selected-filesize').textContent = this.formatFileSize(file.size);
    }
    this.hideAlert();
  },

  clearFileSelection() {
    selectedFile = null;
    const fileInput = document.getElementById('resume-file-input');
    if (fileInput) fileInput.value = '';

    document.getElementById('selected-file-card')?.classList.add('hidden');
    document.getElementById('dropzone')?.classList.remove('hidden');
  },

  formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    else return (bytes / 1048576).toFixed(1) + ' MB';
  },

  /* Sample Resumes */
  bindSampleButtons() {
    const sampleButtons = document.querySelectorAll('.btn-sample-resume');
    sampleButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const sampleId = btn.getAttribute('data-sample-id');
        this.selectSampleResume(sampleId, btn);
      });
    });
  },

  selectSampleResume(sampleId, activeBtn) {
    activeSampleId = sampleId;
    selectedFile = null;
    this.clearFileSelection();

    document.querySelectorAll('.btn-sample-resume').forEach(b => b.classList.remove('active'));
    activeBtn.classList.add('active');

    const indicator = document.getElementById('sample-active-indicator');
    const link = document.getElementById('view-sample-pdf-link');
    const nameSpan = document.getElementById('active-sample-name');

    if (indicator && link && nameSpan) {
      indicator.classList.remove('hidden');
      nameSpan.textContent = `Using: ${activeBtn.textContent.trim()}`;
      link.href = `/api/sample-resumes/${sampleId}/pdf`;
    }

    this.hideAlert();
  },

  /* Job Description Input */
  bindJobTextarea() {
    const textarea = document.getElementById('job-description-input');
    const counter = document.getElementById('jd-char-count');
    const clearBtn = document.getElementById('clear-jd-btn');

    if (textarea && counter) {
      textarea.addEventListener('input', () => {
        const text = textarea.value;
        const charCount = text.length;
        const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
        counter.textContent = `${charCount} characters (${wordCount} words)`;
      });
    }

    if (clearBtn && textarea) {
      clearBtn.addEventListener('click', () => {
        textarea.value = '';
        if (counter) counter.textContent = '0 characters (0 words)';
        textarea.focus();
      });
    }
  },

  /* Load Preconfigured Sample Jobs */
  async loadSampleJobs() {
    try {
      const res = await fetch('/api/sample-jobs');
      const data = await res.json();
      if (data.success && data.jobs) {
        this.sampleJobs = data.jobs;
        const select = document.getElementById('sample-job-select');
        if (select) {
          data.jobs.forEach(job => {
            const opt = document.createElement('option');
            opt.value = job.id;
            opt.textContent = `${job.title} (${job.company})`;
            select.appendChild(opt);
          });

          select.addEventListener('change', () => {
            const selectedId = select.value;
            const chosen = this.sampleJobs.find(j => j.id === selectedId);
            if (chosen) {
              const textarea = document.getElementById('job-description-input');
              if (textarea) {
                textarea.value = chosen.description;
                const counter = document.getElementById('jd-char-count');
                const words = chosen.description.trim().split(/\s+/).length;
                if (counter) {
                  counter.textContent = `${chosen.description.length} characters (${words} words)`;
                }
              }
            }
          });
        }
      }
    } catch (e) {
      console.warn('Failed to fetch sample jobs', e);
    }
  },

  /* Tab Switching */
  bindTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const targetId = btn.getAttribute('data-tab');

        tabButtons.forEach(b => {
          b.classList.remove('active');
          b.setAttribute('aria-selected', 'false');
        });
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

        btn.classList.add('active');
        btn.setAttribute('aria-selected', 'true');
        const targetPane = document.getElementById(targetId);
        if (targetPane) targetPane.classList.add('active');
      });
    });
  },

  /* Form Submission & API Fetch */
  bindForm() {
    const form = document.getElementById('analyze-form');
    const resetBtn = document.getElementById('reset-btn');

    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await this.handleAnalysisSubmit();
      });
    }

    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        this.resetAll();
      });
    }
  },

  async handleAnalysisSubmit() {
    const jdText = document.getElementById('job-description-input')?.value.trim();

    if (!selectedFile && !activeSampleId) {
      this.showAlert('Please upload a resume in PDF format or select one of the sample resumes.', 'danger');
      return;
    }

    if (!jdText) {
      this.showAlert('Please paste a job description or select a sample job posting from the dropdown.', 'danger');
      return;
    }

    if (jdText.length < 25) {
      this.showAlert('Job description is too brief. Please provide a more detailed job posting.', 'danger');
      return;
    }

    this.hideAlert();
    this.showLoading();

    const formData = new FormData();
    formData.append('job_description', jdText);

    if (activeSampleId) {
      formData.append('sample_id', activeSampleId);
    } else if (selectedFile) {
      formData.append('resume', selectedFile);
    }

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        throw new Error(result.error || 'Failed to complete resume analysis.');
      }

      window.currentAnalysisResult = result;
      this.hideLoading();

      // Render dashboard with returned data
      window.renderAnalysisResults(result);

      // Auto save to history
      AppHistory.saveAnalysis(result);

      // Scroll smoothly down to the results section
      const resultsSection = document.getElementById('results-dashboard');
      if (resultsSection) {
        resultsSection.classList.remove('hidden');
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }

    } catch (err) {
      this.hideLoading();
      this.showAlert(err.message, 'danger');
    }
  },

  /* Progressive Loading UI */
  showLoading() {
    const loadingState = document.getElementById('loading-state');
    const submitBtn = document.getElementById('submit-btn');
    const progressBar = document.getElementById('loading-progress-bar');
    const loadingStep = document.getElementById('loading-step');

    if (submitBtn) submitBtn.disabled = true;
    if (loadingState) loadingState.classList.remove('hidden');

    const steps = [
      { pct: 20, text: 'Extracting readable text and structure with PyMuPDF...' },
      { pct: 45, text: 'Parsing technical skills, education, and work experience...' },
      { pct: 70, text: 'Executing TF-IDF vectorization and keyword match scoring...' },
      { pct: 90, text: 'Synthesizing tailored AI suggestions and ATS diagnostic...' }
    ];

    let currentStep = 0;
    this.loadingInterval = setInterval(() => {
      if (currentStep < steps.length) {
        if (progressBar) progressBar.style.width = steps[currentStep].pct + '%';
        if (loadingStep) loadingStep.textContent = steps[currentStep].text;
        currentStep++;
      }
    }, 600);
  },

  hideLoading() {
    if (this.loadingInterval) clearInterval(this.loadingInterval);
    const loadingState = document.getElementById('loading-state');
    const submitBtn = document.getElementById('submit-btn');
    const progressBar = document.getElementById('loading-progress-bar');

    if (progressBar) progressBar.style.width = '100%';
    setTimeout(() => {
      if (loadingState) loadingState.classList.add('hidden');
      if (submitBtn) submitBtn.disabled = false;
    }, 200);
  },

  /* Alert Banners */
  bindAlert() {
    const closeBtn = document.getElementById('alert-close-btn');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.hideAlert());
    }
  },

  showAlert(message, type = 'warning') {
    const banner = document.getElementById('alert-banner');
    const msg = document.getElementById('alert-message');
    if (!banner || !msg) return;

    banner.className = 'alert-banner';
    if (type === 'danger') banner.classList.add('alert-danger');

    msg.textContent = message;
    banner.classList.remove('hidden');
    banner.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  },

  hideAlert() {
    const banner = document.getElementById('alert-banner');
    if (banner) banner.classList.add('hidden');
  },

  resetAll() {
    this.clearFileSelection();
    activeSampleId = null;
    document.querySelectorAll('.btn-sample-resume').forEach(b => b.classList.remove('active'));
    document.getElementById('sample-active-indicator')?.classList.add('hidden');

    const textarea = document.getElementById('job-description-input');
    if (textarea) textarea.value = '';
    const counter = document.getElementById('jd-char-count');
    if (counter) counter.textContent = '0 characters (0 words)';

    const select = document.getElementById('sample-job-select');
    if (select) select.value = '';

    const results = document.getElementById('results-dashboard');
    if (results) results.classList.add('hidden');

    this.hideAlert();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
};

/* --------------------------------------------------------------------------
   Dashboard Results Renderer
   -------------------------------------------------------------------------- */
window.renderAnalysisResults = function(data) {
  const analysis = data.analysis || {};
  const ai = data.ai_suggestions || {};
  const profile = data.candidate_profile || {};
  const docStats = data.document_stats || {};

  // 1. KPI Top Strip
  const overallScore = analysis.overall_match_percentage || 0;
  document.getElementById('kpi-overall-score').textContent = overallScore + '%';
  document.getElementById('kpi-tfidf-score').textContent = (analysis.similarity_score || 0) + '%';
  document.getElementById('kpi-tech-score').textContent = (analysis.tech_skill_score || 0) + '%';
  
  const atsScore = analysis.ats_audit?.score || 0;
  document.getElementById('kpi-ats-score').textContent = `${atsScore}/100`;
  document.getElementById('kpi-ats-rating').textContent = `Rating: ${analysis.ats_audit?.rating || 'Good'}`;

  // Verdict Title & Summary
  const verdictEl = document.getElementById('kpi-verdict');
  const summaryEl = document.getElementById('kpi-summary');
  if (overallScore >= 75) {
    verdictEl.textContent = 'Strong Qualification Match';
    summaryEl.textContent = 'High alignment with primary technologies and core job criteria.';
  } else if (overallScore >= 50) {
    verdictEl.textContent = 'Moderate Alignment';
    summaryEl.textContent = 'Good foundational skills present; targeted keyword additions recommended.';
  } else {
    verdictEl.textContent = 'Significant Keyword Gaps';
    summaryEl.textContent = 'Substantial missing technical requirements. Follow AI suggestions to tailor.';
  }

  // Document metadata info strip
  document.getElementById('analyzed-filename').textContent = data.filename || 'resume.pdf';
  document.getElementById('analyzed-pages').textContent = `${docStats.page_count || 1} page${docStats.page_count > 1 ? 's' : ''}`;
  document.getElementById('analyzed-words').textContent = `${docStats.word_count || 0} words`;

  // Render Charts
  AppCharts.renderGaugeChart(overallScore);
  AppCharts.renderRadarChart(analysis.category_breakdown);

  // 2. Tab 1: Skills Badges
  renderSkillsBadges(analysis);
  renderCategoryBars(analysis.category_breakdown);

  // 3. Tab 2: AI Recommendations
  renderAISuggestions(ai);

  // 4. Tab 3: ATS Diagnostics
  renderATSDiagnostics(analysis.ats_audit, analysis.strengths, analysis.areas_for_improvement);

  // 5. Tab 4: Parsed Qualifications
  renderParsedProfile(profile);
};

function renderSkillsBadges(analysis) {
  const matched = analysis.matched_skills || [];
  const missing = analysis.missing_skills || [];
  const bonus = analysis.additional_skills || [];

  document.getElementById('matched-count').textContent = matched.length;
  document.getElementById('missing-count').textContent = missing.length;
  document.getElementById('additional-count').textContent = bonus.length;

  const matchedContainer = document.getElementById('matched-skills-list');
  const missingContainer = document.getElementById('missing-skills-list');
  const bonusContainer = document.getElementById('additional-skills-list');

  matchedContainer.innerHTML = matched.length > 0 ? matched.map(s => `
    <span class="skill-badge skill-badge-matched">
      <img src="/static/icons/check-circle.svg" alt="Check" class="svg-icon-xs">
      <span>${escapeHtml(s)}</span>
    </span>
  `).join('') : `<p style="font-size: 0.85rem; color: var(--text-muted);">No overlapping skills detected.</p>`;

  missingContainer.innerHTML = missing.length > 0 ? missing.map(s => `
    <span class="skill-badge skill-badge-missing">
      <img src="/static/icons/alert-triangle.svg" alt="Missing" class="svg-icon-xs">
      <span>${escapeHtml(s)}</span>
    </span>
  `).join('') : `<p style="font-size: 0.85rem; color: var(--text-success);">All required skills are present in the resume!</p>`;

  bonusContainer.innerHTML = bonus.length > 0 ? bonus.slice(0, 25).map(s => `
    <span class="skill-badge skill-badge-bonus">
      <img src="/static/icons/code.svg" alt="Code" class="svg-icon-xs">
      <span>${escapeHtml(s)}</span>
    </span>
  `).join('') : `<p style="font-size: 0.85rem; color: var(--text-muted);">No extra skills detected.</p>`;
}

function renderCategoryBars(breakdown) {
  const container = document.getElementById('category-bars-list');
  if (!container || !breakdown) return;

  container.innerHTML = Object.entries(breakdown).map(([key, item]) => {
    return `
      <div class="cat-bar-item">
        <div class="cat-bar-header">
          <span class="cat-bar-title">${escapeHtml(item.display_name)}</span>
          <span class="cat-bar-ratio">Matched ${item.matched_count} of ${item.required_count} (${item.match_rate}%)</span>
        </div>
        <div class="cat-track">
          <div class="cat-fill" style="width: ${Math.min(100, item.match_rate)}%;"></div>
        </div>
      </div>
    `;
  }).join('');
}

function renderAISuggestions(ai) {
  document.getElementById('ai-engine-source').textContent = ai.source || 'Intelligent AI Engine';
  document.getElementById('recruiter-verdict-pill').textContent = ai.recruiter_verdict || 'Interview Readiness: High';

  document.getElementById('ai-summary-critique').textContent = ai.summary_critique || 'Good foundation.';
  document.getElementById('ai-tailored-summary').textContent = ai.tailored_summary_suggestion || 'No suggestion generated.';

  // Bullet improvements
  const bulletsContainer = document.getElementById('ai-bullet-improvements-list');
  const bullets = ai.bullet_improvements || [];
  if (bulletsContainer) {
    bulletsContainer.innerHTML = bullets.map(b => `
      <div class="bullet-upgrade-card">
        <div class="bullet-original">
          <strong>Draft / Original:</strong> ${escapeHtml(b.original_concept)}
        </div>
        <div class="bullet-revised">
          <strong>Recommended Rewrite:</strong> ${escapeHtml(b.improved_bullet)}
        </div>
        <div class="bullet-reason">
          <strong>Strategic Value:</strong> ${escapeHtml(b.reason)}
        </div>
      </div>
    `).join('');
  }

  // Keyword tips
  const tipsContainer = document.getElementById('ai-keyword-tips-list');
  const tips = ai.keyword_integration_tips || [];
  if (tipsContainer) {
    tipsContainer.innerHTML = tips.map(tip => `<li>${escapeHtml(tip)}</li>`).join('');
  }

  // Action verbs
  const verbsContainer = document.getElementById('ai-action-verbs-list');
  const verbs = ai.action_verbs_recommended || [];
  if (verbsContainer) {
    verbsContainer.innerHTML = verbs.map(v => `
      <button type="button" class="verb-pill" data-verb="${escapeHtml(v)}" title="Click to copy">
        ${escapeHtml(v)}
      </button>
    `).join('');

    verbsContainer.querySelectorAll('.verb-pill').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const verb = e.currentTarget.getAttribute('data-verb');
        navigator.clipboard.writeText(verb).then(() => {
          const original = btn.textContent;
          btn.textContent = 'Copied!';
          setTimeout(() => { btn.textContent = original; }, 1500);
        });
      });
    });
  }
}

function renderATSDiagnostics(atsAudit, strengths, improvements) {
  const checklistContainer = document.getElementById('ats-checklist-items');
  const badge = document.getElementById('ats-rating-badge');

  if (badge && atsAudit) {
    badge.textContent = `Score: ${atsAudit.score}/100 • ${atsAudit.rating}`;
  }

  if (checklistContainer && atsAudit && atsAudit.checks) {
    checklistContainer.innerHTML = atsAudit.checks.map(c => `
      <div class="ats-check-item ${c.passed ? 'passed' : 'failed'}">
        <img src="/static/icons/${c.passed ? 'check-circle' : 'x-circle'}.svg" alt="Status" class="svg-icon ${c.passed ? 'icon-success' : ''}">
        <div class="ats-item-content">
          <span class="ats-item-label">${escapeHtml(c.label)}</span>
          <span class="ats-item-details">${escapeHtml(c.details)}</span>
        </div>
      </div>
    `).join('');
  }

  // Strengths
  const strengthsContainer = document.getElementById('strengths-list');
  if (strengthsContainer && strengths) {
    strengthsContainer.innerHTML = strengths.map(s => `<li>${escapeHtml(s)}</li>`).join('');
  }

  // Improvements
  const improvementsContainer = document.getElementById('improvements-list');
  if (improvementsContainer && improvements) {
    improvementsContainer.innerHTML = improvements.map(i => `<li>${escapeHtml(i)}</li>`).join('');
  }
}

function renderParsedProfile(profile) {
  // Contact
  const contact = profile.contact || {};
  const contactContainer = document.getElementById('parsed-contact-details');
  if (contactContainer) {
    contactContainer.innerHTML = `
      <div class="contact-item">
        <span class="contact-label">Candidate Name</span>
        <span class="contact-val">${escapeHtml(contact.name || 'Not detected')}</span>
      </div>
      <div class="contact-item">
        <span class="contact-label">Email Address</span>
        <span class="contact-val">${escapeHtml(contact.email || 'Not detected')}</span>
      </div>
      <div class="contact-item">
        <span class="contact-label">Phone Number</span>
        <span class="contact-val">${escapeHtml(contact.phone || 'Not detected')}</span>
      </div>
      <div class="contact-item">
        <span class="contact-label">LinkedIn Profile</span>
        <span class="contact-val">${escapeHtml(contact.linkedin || 'Not detected')}</span>
      </div>
      <div class="contact-item">
        <span class="contact-label">GitHub Profile</span>
        <span class="contact-val">${escapeHtml(contact.github || 'Not detected')}</span>
      </div>
      <div class="contact-item">
        <span class="contact-label">Portfolio / Website</span>
        <span class="contact-val">${escapeHtml(contact.portfolio || 'Not detected')}</span>
      </div>
    `;
  }

  // Education
  const eduContainer = document.getElementById('parsed-education-list');
  const education = profile.education || [];
  if (eduContainer) {
    eduContainer.innerHTML = education.length > 0 ? education.map(e => `
      <div class="timeline-entry">
        <div class="timeline-title">${escapeHtml(e.degree || 'Degree')}</div>
        <div class="timeline-meta">${escapeHtml(e.institution || e.text)} ${e.year ? '• ' + escapeHtml(e.year) : ''} ${e.gpa ? '• GPA: ' + escapeHtml(e.gpa) : ''}</div>
      </div>
    `).join('') : `<p style="font-size: 0.85rem; color: var(--text-muted);">No structured education detected.</p>`;
  }

  // Experience
  const expContainer = document.getElementById('parsed-experience-list');
  const experience = profile.experience || [];
  if (expContainer) {
    expContainer.innerHTML = experience.length > 0 ? experience.map(exp => `
      <div class="timeline-entry">
        <div class="timeline-title">${escapeHtml(exp.title_line || 'Role / Position')}</div>
        <div class="timeline-meta">${escapeHtml(exp.date_range || '')}</div>
        ${exp.bullets && exp.bullets.length > 0 ? `
          <ul class="timeline-bullets">
            ${exp.bullets.map(b => `<li>${escapeHtml(b)}</li>`).join('')}
          </ul>
        ` : ''}
      </div>
    `).join('') : `<p style="font-size: 0.85rem; color: var(--text-muted);">No structured work experience detected.</p>`;
  }

  // Projects
  const projContainer = document.getElementById('parsed-projects-list');
  const projects = profile.projects || [];
  if (projContainer) {
    projContainer.innerHTML = projects.length > 0 ? projects.map(p => `
      <div class="compact-item">
        <strong>${escapeHtml(p.name)}</strong>
        ${p.details && p.details.length > 0 ? `<p style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.2rem;">${escapeHtml(p.details.join(' • '))}</p>` : ''}
      </div>
    `).join('') : `<p style="font-size: 0.85rem; color: var(--text-muted);">No projects section detected.</p>`;
  }

  // Certifications
  const certContainer = document.getElementById('parsed-certifications-list');
  const certifications = profile.certifications || [];
  if (certContainer) {
    certContainer.innerHTML = certifications.length > 0 ? certifications.map(c => `
      <div class="compact-item">
        <span>${escapeHtml(c)}</span>
      </div>
    `).join('') : `<p style="font-size: 0.85rem; color: var(--text-muted);">No certifications section detected.</p>`;
  }
}
