/* ==========================================================================
   CHARTS.JS - Interactive Chart.js Initializer and Theme Handlers
   Provides 5 comprehensive charts for executive dashboard analytics
   ========================================================================== */

let chartInstances = {};

// Palette definitions
const CHART_COLORS = {
  blue: '#2563EB',
  navy: '#1E3A8A',
  teal: '#0D9488',
  green: '#10B981',
  yellow: '#F59E0B',
  red: '#EF4444',
  purple: '#8B5CF6',
  indigo: '#6366F1',
  pink: '#EC4899',
  slate: '#64748B'
};

const DEPT_PALETTE = [
  '#2563EB', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#06B6D4', '#64748B'
];

function getThemeTextColors() {
  const isDark = document.body.classList.contains('dark-mode');
  return {
    textColor: isDark ? '#94A3B8' : '#64748B',
    gridColor: isDark ? '#1E293B' : '#E2E8F0',
    titleColor: isDark ? '#F1F5F9' : '#0F172A'
  };
}

/**
 * Initializes or updates all 5 dashboard charts with live API data
 */
function initDashboardCharts(data) {
  if (!data) return;
  const colors = getThemeTextColors();

  // 1. Department Distribution (Doughnut)
  const deptCtx = document.getElementById('deptDistChart');
  if (deptCtx) {
    if (chartInstances.deptDist) chartInstances.deptDist.destroy();
    const deptLabels = Object.keys(data.department_counts || {});
    const deptValues = Object.values(data.department_counts || {});

    chartInstances.deptDist = new Chart(deptCtx, {
      type: 'doughnut',
      data: {
        labels: deptLabels,
        datasets: [{
          data: deptValues,
          backgroundColor: DEPT_PALETTE.slice(0, deptLabels.length),
          borderWidth: 2,
          borderColor: document.body.classList.contains('dark-mode') ? '#151C2C' : '#FFFFFF'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '68%',
        plugins: {
          legend: {
            position: 'right',
            labels: { color: colors.textColor, boxWidth: 12, font: { size: 11 } }
          },
          tooltip: {
            callbacks: {
              label: function(ctx) {
                const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                const pct = ((ctx.parsed / total) * 100).toFixed(1);
                return ` ${ctx.label}: ${ctx.parsed} employees (${pct}%)`;
              }
            }
          }
        }
      }
    });
  }

  // 2. Attendance Comparison (Bar Chart)
  const attCtx = document.getElementById('attendanceCompChart');
  if (attCtx) {
    if (chartInstances.attComp) chartInstances.attComp.destroy();
    const depts = Object.keys(data.dept_avg_attendance || {});
    const attVals = Object.values(data.dept_avg_attendance || {});

    chartInstances.attComp = new Chart(attCtx, {
      type: 'bar',
      data: {
        labels: depts,
        datasets: [{
          label: 'Avg Attendance (%)',
          data: attVals,
          backgroundColor: attVals.map(val => val >= 85 ? 'rgba(16, 185, 129, 0.85)' : 'rgba(59, 130, 246, 0.85)'),
          borderRadius: 6,
          borderSkipped: false
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            min: 50,
            max: 100,
            ticks: { color: colors.textColor, callback: v => v + '%' },
            grid: { color: colors.gridColor }
          },
          x: {
            ticks: { color: colors.textColor },
            grid: { display: false }
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: ctx => ` Average Attendance: ${ctx.parsed.y}%`
            }
          }
        }
      }
    });
  }

  // 3. Salary Comparison (Line Chart)
  const salCtx = document.getElementById('salaryCompChart');
  if (salCtx) {
    if (chartInstances.salComp) chartInstances.salComp.destroy();
    const depts = Object.keys(data.dept_avg_salary || {});
    const salVals = Object.values(data.dept_avg_salary || {});

    chartInstances.salComp = new Chart(salCtx, {
      type: 'line',
      data: {
        labels: depts,
        datasets: [{
          label: 'Avg Net Salary',
          data: salVals,
          borderColor: '#8B5CF6',
          backgroundColor: 'rgba(139, 92, 246, 0.12)',
          fill: true,
          tension: 0.35,
          pointBackgroundColor: '#8B5CF6',
          pointRadius: 4,
          pointHoverRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            ticks: {
              color: colors.textColor,
              callback: v => '₹' + (v / 1000).toFixed(0) + 'k'
            },
            grid: { color: colors.gridColor }
          },
          x: {
            ticks: { color: colors.textColor },
            grid: { display: false }
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: ctx => ` Average Salary: ₹${ctx.parsed.y.toLocaleString('en-IN')}`
            }
          }
        }
      }
    });
  }

  // 4. Attendance Status (Doughnut Chart: Excellent, Good, Below Threshold)
  const statusCtx = document.getElementById('attendanceStatusChart');
  if (statusCtx) {
    if (chartInstances.statusDist) chartInstances.statusDist.destroy();
    const sData = data.status_distribution || {};

    chartInstances.statusDist = new Chart(statusCtx, {
      type: 'doughnut',
      data: {
        labels: ['Excellent (≥90%)', 'Good (75–89%)', 'Below Threshold (<75%)'],
        datasets: [{
          data: [sData['Excellent'] || 0, sData['Good'] || 0, sData['Below Threshold'] || 0],
          backgroundColor: ['#10B981', '#F59E0B', '#EF4444'],
          borderWidth: 2,
          borderColor: document.body.classList.contains('dark-mode') ? '#151C2C' : '#FFFFFF'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '60%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: colors.textColor, boxWidth: 10, font: { size: 11 } }
          },
          tooltip: {
            callbacks: {
              label: function(ctx) {
                const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                const pct = total > 0 ? ((ctx.parsed / total) * 100).toFixed(1) : 0;
                return ` ${ctx.label}: ${ctx.parsed} (${pct}%)`;
              }
            }
          }
        }
      }
    });
  }

  // 5. Monthly Salary Expense (Stacked Bar Chart: Basic vs Overtime)
  const expCtx = document.getElementById('monthlyExpenseChart');
  if (expCtx) {
    if (chartInstances.monthlyExp) chartInstances.monthlyExp.destroy();
    const depts = Object.keys(data.dept_total_basic || {});
    const basicVals = depts.map(d => data.dept_total_basic[d] || 0);
    const otVals = depts.map(d => data.dept_total_ot[d] || 0);

    chartInstances.monthlyExp = new Chart(expCtx, {
      type: 'bar',
      data: {
        labels: depts,
        datasets: [
          {
            label: 'Basic Salary Expense',
            data: basicVals,
            backgroundColor: '#1E3A8A',
            borderRadius: 4
          },
          {
            label: 'Overtime Pay',
            data: otVals,
            backgroundColor: '#F59E0B',
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            stacked: true,
            ticks: { color: colors.textColor },
            grid: { display: false }
          },
          y: {
            stacked: true,
            ticks: {
              color: colors.textColor,
              callback: v => '₹' + (v / 100000).toFixed(1) + 'L'
            },
            grid: { color: colors.gridColor }
          }
        },
        plugins: {
          legend: {
            position: 'top',
            labels: { color: colors.textColor, boxWidth: 12, font: { size: 11 } }
          },
          tooltip: {
            callbacks: {
              label: ctx => ` ${ctx.dataset.label}: ₹${ctx.parsed.y.toLocaleString('en-IN')}`
            }
          }
        }
      }
    });
  }
}

// Re-render charts when theme changes
window.addEventListener('themeChanged', () => {
  if (window.lastDashboardData) {
    initDashboardCharts(window.lastDashboardData);
  }
});
