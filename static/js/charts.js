/**
 * Resume Analyzer - Chart.js Visualizations Controller
 */

let gaugeChartInstance = null;
let radarChartInstance = null;

const AppCharts = {
  /**
   * Initializes or updates the circular donut gauge for the overall match score.
   */
  renderGaugeChart(score) {
    const ctx = document.getElementById('gaugeChart');
    if (!ctx) return;

    if (gaugeChartInstance) {
      gaugeChartInstance.destroy();
    }

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    
    // Choose color based on score thresholds
    let primaryColor = '#10b981'; // Green
    if (score < 50) {
      primaryColor = '#ef4444'; // Red
    } else if (score < 75) {
      primaryColor = '#f59e0b'; // Amber
    }

    const emptyColor = isDark ? '#1e293b' : '#e2e8f0';

    gaugeChartInstance = new Chart(ctx, {
      type: 'doughnut',
      data: {
        datasets: [{
          data: [score, Math.max(0, 100 - score)],
          backgroundColor: [primaryColor, emptyColor],
          borderWidth: 0,
          circumference: 270,
          rotation: 225
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '80%',
        plugins: {
          tooltip: { enabled: false },
          legend: { display: false }
        },
        animation: {
          duration: 1200,
          easing: 'easeOutQuart'
        }
      }
    });
  },

  /**
   * Initializes or updates the radar chart for domain skills coverage.
   */
  renderRadarChart(categoryBreakdown) {
    const ctx = document.getElementById('radarChart');
    if (!ctx) return;

    if (radarChartInstance) {
      radarChartInstance.destroy();
    }

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';

    // Prepare labels and scores
    const labels = [];
    const matchRates = [];

    for (const [key, data] of Object.entries(categoryBreakdown || {})) {
      labels.push(data.display_name.replace(' & ', '\n& '));
      matchRates.push(data.match_rate || 0);
    }

    const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.08)';
    const textColor = isDark ? '#94a3b8' : '#475569';

    radarChartInstance = new Chart(ctx, {
      type: 'radar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Domain Match %',
          data: matchRates,
          backgroundColor: 'rgba(59, 130, 246, 0.25)',
          borderColor: '#3b82f6',
          pointBackgroundColor: '#3b82f6',
          pointBorderColor: '#ffffff',
          pointHoverBackgroundColor: '#ffffff',
          pointHoverBorderColor: '#3b82f6',
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          r: {
            angleLines: { color: gridColor },
            grid: { color: gridColor },
            pointLabels: {
              color: textColor,
              font: { family: 'Inter', size: 10, weight: 600 }
            },
            ticks: {
              display: false,
              backdropColor: 'transparent',
              stepSize: 20
            },
            suggestedMin: 0,
            suggestedMax: 100
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => ` Match Rate: ${context.raw}%`
            }
          }
        }
      }
    });
  },

  /**
   * Updates charts when the theme changes (Dark/Light).
   */
  refreshTheme(score, categoryBreakdown) {
    if (score !== undefined) {
      this.renderGaugeChart(score);
    }
    if (categoryBreakdown !== undefined) {
      this.renderRadarChart(categoryBreakdown);
    }
  }
};

