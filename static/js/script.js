/* ==========================================================================
   SCRIPT.JS - Core Frontend Logic, Modals, CRUD, Filtering, Pagination
   ========================================================================== */

// Global State
let currentEmployeesPage = 1;
let currentSortBy = 'id';
let currentSortOrder = 'asc';
let currentSearchTerm = '';
let currentDeptFilter = 'all';
let currentStatusFilter = 'all';
let currentThresholdVal = 75;

// Initials Avatar Color Hash
const AVATAR_COLORS = [
  '#2563EB', '#7C3AED', '#DB2777', '#EA580C', '#059669', '#0891B2', '#4F46E5', '#D97706'
];

function getAvatarColor(name) {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
}

function getInitials(name) {
  if (!name) return 'EM';
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

// ----------------- TOAST SYSTEM ----------------- //

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  let iconHtml = '<i class="fas fa-info-circle toast-icon"></i>';
  if (type === 'success') iconHtml = '<i class="fas fa-check-circle toast-icon"></i>';
  else if (type === 'danger') iconHtml = '<i class="fas fa-exclamation-circle toast-icon"></i>';
  else if (type === 'warning') iconHtml = '<i class="fas fa-exclamation-triangle toast-icon"></i>';

  toast.innerHTML = `
    ${iconHtml}
    <div class="toast-message">${message}</div>
    <button onclick="this.parentElement.remove()" style="background:none;border:none;color:inherit;cursor:pointer;opacity:0.6;"><i class="fas fa-times"></i></button>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ----------------- SPINNER SYSTEM ----------------- //

function showSpinner() {
  const sp = document.getElementById('globalSpinner');
  if (sp) sp.classList.add('active');
}

function hideSpinner() {
  const sp = document.getElementById('globalSpinner');
  if (sp) sp.classList.remove('active');
}

// ----------------- MODAL CONTROLS ----------------- //

function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('show');
    document.body.style.overflow = '';
  }
}

// Global modal close on backdrop click or ESC key
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-backdrop')) {
    e.target.classList.remove('show');
    document.body.style.overflow = '';
  }
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-backdrop.show').forEach(m => {
      m.classList.remove('show');
    });
    document.body.style.overflow = '';
  }
});

// ----------------- REAL-TIME LIVE CLOCK ----------------- //

function updateLiveClock() {
  const clockEl = document.getElementById('liveClockText');
  if (!clockEl) return;
  const now = new Date();
  const options = {
    weekday: 'short', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true
  };
  clockEl.textContent = now.toLocaleString('en-US', options);
}

// ----------------- THEME TOGGLE ----------------- //

function initTheme() {
  const savedTheme = localStorage.getItem('ems_theme');
  const toggleBtn = document.getElementById('themeToggleBtn');
  const isDark = savedTheme === 'dark';

  if (isDark) {
    document.body.classList.add('dark-mode');
    if (toggleBtn) toggleBtn.innerHTML = '<i class="fas fa-sun"></i>';
  } else {
    document.body.classList.remove('dark-mode');
    if (toggleBtn) toggleBtn.innerHTML = '<i class="fas fa-moon"></i>';
  }

  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const activeDark = document.body.classList.toggle('dark-mode');
      localStorage.setItem('ems_theme', activeDark ? 'dark' : 'light');
      toggleBtn.innerHTML = activeDark ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
      window.dispatchEvent(new Event('themeChanged'));
    });
  }
}

// ----------------- DASHBOARD DATA LOADER ----------------- //

async function loadDashboardData() {
  const kpiTotal = document.getElementById('kpiTotalEmployees');
  if (!kpiTotal) return; // Not on dashboard page

  showSpinner();
  try {
    const res = await fetch(`/api/dashboard-stats?threshold=${currentThresholdVal}`);
    const data = await res.json();
    window.lastDashboardData = data;

    // Update KPIs
    kpiTotal.textContent = data.total_employees.toLocaleString();
    document.getElementById('kpiAvgAttendance').textContent = `${data.avg_attendance}%`;
    document.getElementById('kpiBelowThreshold').textContent = data.below_threshold_count;
    document.getElementById('kpiTotalSalary').textContent = `₹${data.total_salary_expense.toLocaleString('en-IN')}`;
    document.getElementById('kpiTotalOT').textContent = `₹${data.total_ot_pay.toLocaleString('en-IN')}`;

    // Subtexts
    const otHoursSub = document.getElementById('kpiOTHoursSub');
    if (otHoursSub) otHoursSub.textContent = `Across ${data.total_ot_hours.toFixed(1)} OT hours`;

    // Render 5 Charts
    if (typeof initDashboardCharts === 'function') {
      initDashboardCharts(data);
    }

    // Populate Lowest Attendance Alerts
    const alertList = document.getElementById('dashboardAlertList');
    if (alertList && data.lowest_attendance_alerts) {
      alertList.innerHTML = data.lowest_attendance_alerts.map(emp => `
        <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid var(--border);">
          <div style="display:flex;align-items:center;gap:10px;">
            <div class="initials-avatar" style="background:${getAvatarColor(emp.employee_name)};width:32px;height:32px;font-size:11px;">
              ${getInitials(emp.employee_name)}
            </div>
            <div>
              <div style="font-weight:600;font-size:13px;">${emp.employee_name}</div>
              <div style="font-size:11px;color:var(--text-muted);">${emp.employee_id} • ${emp.department}</div>
            </div>
          </div>
          <div style="text-align:right;">
            <span class="badge badge-danger">${emp.attendance_percentage}%</span>
            <div style="font-size:11px;color:var(--text-muted);margin-top:2px;">${emp.days_present}/${emp.total_working_days} days</div>
          </div>
        </div>
      `).join('');
    }

  } catch (err) {
    console.error('Error loading dashboard:', err);
    showToast('Failed to load dashboard metrics.', 'danger');
  } finally {
    hideSpinner();
  }
}

// ----------------- EMPLOYEES TABLE & PAGINATION ----------------- //

async function loadEmployeesTable() {
  const tbody = document.getElementById('employeeTableBody');
  if (!tbody) return; // Not on employees page

  showSpinner();
  try {
    const params = new URLSearchParams({
      page: currentEmployeesPage,
      per_page: 25,
      search: currentSearchTerm,
      department: currentDeptFilter,
      status: currentStatusFilter,
      sort_by: currentSortBy,
      order: currentSortOrder
    });

    const res = await fetch(`/api/employees?${params.toString()}`);
    const data = await res.json();

    renderEmployeeRows(data.employees, tbody);
    renderPaginationControls(data);

    const countLabel = document.getElementById('tableShowingCount');
    if (countLabel) {
      const start = data.total_count === 0 ? 0 : (data.page - 1) * data.per_page + 1;
      const end = Math.min(data.page * data.per_page, data.total_count);
      countLabel.textContent = `Showing ${start}–${end} of ${data.total_count} employees`;
    }

  } catch (err) {
    console.error('Error loading employees:', err);
    showToast('Failed to load employee list.', 'danger');
  } finally {
    hideSpinner();
  }
}

function renderEmployeeRows(employees, tbody) {
  if (!employees || employees.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="12" style="text-align:center;padding:40px;color:var(--text-muted);">
          <i class="fas fa-user-slash" style="font-size:32px;margin-bottom:10px;display:block;opacity:0.5;"></i>
          No employees found matching your criteria.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = employees.map(emp => {
    let statusClass = 'badge-danger';
    let statusIcon = 'fa-times-circle';
    let progressColor = '#EF4444';

    if (emp.status === 'Excellent') {
      statusClass = 'badge-success';
      statusIcon = 'fa-check-circle';
      progressColor = '#10B981';
    } else if (emp.status === 'Good') {
      statusClass = 'badge-warning';
      statusIcon = 'fa-exclamation-circle';
      progressColor = '#F59E0B';
    }

    return `
      <tr id="row-emp-${emp.id}">
        <td><strong>${emp.employee_id}</strong></td>
        <td>
          <div class="emp-profile-cell">
            <div class="initials-avatar" style="background:${getAvatarColor(emp.employee_name)}">
              ${getInitials(emp.employee_name)}
            </div>
            <div>
              <div class="emp-info-name">${emp.employee_name}</div>
              <div class="emp-info-sub">ID: ${emp.employee_id}</div>
            </div>
          </div>
        </td>
        <td><span class="badge badge-dept">${emp.department}</span></td>
        <td style="text-align:center;">${emp.total_working_days}</td>
        <td style="text-align:center;">${emp.days_present}</td>
        <td>
          <div class="progress-bar-cell">
            <span style="font-weight:600;min-width:42px;">${emp.attendance_percentage}%</span>
            <div class="mini-progress-track">
              <div class="mini-progress-fill" style="width:${Math.min(100, emp.attendance_percentage)}%;background-color:${progressColor};"></div>
            </div>
          </div>
        </td>
        <td>₹${emp.basic_salary.toLocaleString('en-IN')}</td>
        <td style="text-align:center;">${emp.overtime_hours} hrs</td>
        <td>₹${emp.overtime_pay.toLocaleString('en-IN')}</td>
        <td><strong>₹${emp.final_salary.toLocaleString('en-IN')}</strong></td>
        <td>
          <span class="badge ${statusClass}">
            <i class="fas ${statusIcon}"></i> ${emp.status}
          </span>
        </td>
        <td>
          <div class="table-actions">
            <button class="action-btn view-btn" title="View Profile" onclick="viewEmployeeProfile(${emp.id})">
              <i class="fas fa-eye"></i>
            </button>
            <button class="action-btn edit-btn" title="Edit Employee" onclick="editEmployee(${emp.id})">
              <i class="fas fa-edit"></i>
            </button>
            <button class="action-btn slip-btn" title="Salary Slip" onclick="openSalarySlipModal(${emp.id})">
              <i class="fas fa-file-invoice-dollar"></i>
            </button>
            <button class="action-btn delete-btn" title="Delete Employee" onclick="deleteEmployee(${emp.id}, '${emp.employee_name}', '${emp.employee_id}')">
              <i class="fas fa-trash-alt"></i>
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function renderPaginationControls(data) {
  const container = document.getElementById('paginationControls');
  if (!container) return;

  const { page, total_pages } = data;
  let html = `
    <button class="page-btn" onclick="changeEmployeesPage(${page - 1})" ${page <= 1 ? 'disabled' : ''}>
      <i class="fas fa-chevron-left"></i> Prev
    </button>
  `;

  // Dynamic window of page numbers
  let startPage = Math.max(1, page - 2);
  let endPage = Math.min(total_pages, page + 2);

  if (startPage > 1) {
    html += `<button class="page-btn" onclick="changeEmployeesPage(1)">1</button>`;
    if (startPage > 2) html += `<span style="padding:0 4px;color:var(--text-muted);">...</span>`;
  }

  for (let i = startPage; i <= endPage; i++) {
    html += `<button class="page-btn ${i === page ? 'active' : ''}" onclick="changeEmployeesPage(${i})">${i}</button>`;
  }

  if (endPage < total_pages) {
    if (endPage < total_pages - 1) html += `<span style="padding:0 4px;color:var(--text-muted);">...</span>`;
    html += `<button class="page-btn" onclick="changeEmployeesPage(${total_pages})">${total_pages}</button>`;
  }

  html += `
    <button class="page-btn" onclick="changeEmployeesPage(${page + 1})" ${page >= total_pages ? 'disabled' : ''}>
      Next <i class="fas fa-chevron-right"></i>
    </button>
  `;

  container.innerHTML = html;
}

function changeEmployeesPage(newPage) {
  currentEmployeesPage = newPage;
  loadEmployeesTable();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ----------------- CRUD ACTIONS ----------------- //

function openAddEmployeeModal() {
  document.getElementById('employeeModalTitle').textContent = 'Add New Employee';
  document.getElementById('employeeForm').reset();
  document.getElementById('formDbId').value = '';
  document.getElementById('formEmpId').readOnly = false;
  openModal('employeeFormModal');
}

async function editEmployee(id) {
  showSpinner();
  try {
    const res = await fetch(`/api/employees/${id}`);
    if (!res.ok) throw new Error('Employee not found');
    const emp = await res.json();

    document.getElementById('employeeModalTitle').textContent = `Edit Employee: ${emp.employee_name}`;
    document.getElementById('formDbId').value = emp.id;
    document.getElementById('formEmpId').value = emp.employee_id;
    document.getElementById('formEmpId').readOnly = true; // Protect ID during edit
    document.getElementById('formName').value = emp.employee_name;
    document.getElementById('formDept').value = emp.department;
    document.getElementById('formWorkingDays').value = emp.total_working_days;
    document.getElementById('formDaysPresent').value = emp.days_present;
    document.getElementById('formSalary').value = emp.basic_salary;
    document.getElementById('formOtHours').value = emp.overtime_hours;
    document.getElementById('formOtRate').value = emp.overtime_rate;

    openModal('employeeFormModal');
  } catch (err) {
    showToast('Failed to load employee details.', 'danger');
  } finally {
    hideSpinner();
  }
}

async function saveEmployee(e) {
  e.preventDefault();
  const dbId = document.getElementById('formDbId').value;
  const isEdit = Boolean(dbId);

  const payload = {
    employee_id: document.getElementById('formEmpId').value.trim(),
    employee_name: document.getElementById('formName').value.trim(),
    department: document.getElementById('formDept').value,
    total_working_days: parseInt(document.getElementById('formWorkingDays').value, 10),
    days_present: parseInt(document.getElementById('formDaysPresent').value, 10),
    basic_salary: parseFloat(document.getElementById('formSalary').value),
    overtime_hours: parseFloat(document.getElementById('formOtHours').value || 0),
    overtime_rate: parseFloat(document.getElementById('formOtRate').value || 0)
  };

  // Client-side Validations
  if (!payload.employee_id || !payload.employee_name || !payload.department) {
    showToast('Please fill all required fields.', 'warning');
    return;
  }
  if (payload.total_working_days <= 0) {
    showToast('Total working days must be greater than zero.', 'warning');
    return;
  }
  if (payload.days_present < 0 || payload.days_present > payload.total_working_days) {
    showToast(`Days present cannot exceed working days (${payload.total_working_days}) or be negative.`, 'warning');
    return;
  }
  if (payload.basic_salary < 0 || payload.overtime_hours < 0 || payload.overtime_rate < 0) {
    showToast('Salary and overtime values cannot be negative.', 'warning');
    return;
  }

  showSpinner();
  try {
    const url = isEdit ? `/employees/${dbId}` : '/employees';
    const method = isEdit ? 'PUT' : 'POST';

    const res = await fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const result = await res.json();
    if (!res.ok) {
      showToast(result.error || 'Failed to save employee.', 'danger');
      return;
    }

    showToast(result.message || 'Saved successfully!', 'success');
    closeModal('employeeFormModal');

    // Refresh active view
    if (document.getElementById('employeeTableBody')) {
      loadEmployeesTable();
    } else if (document.getElementById('kpiTotalEmployees')) {
      loadDashboardData();
    }
  } catch (err) {
    showToast('Network error while saving employee.', 'danger');
  } finally {
    hideSpinner();
  }
}

async function deleteEmployee(id, name, empId) {
  if (!confirm(`Are you sure you want to permanently delete employee:\n"${name}" (${empId})?`)) {
    return;
  }

  showSpinner();
  try {
    const res = await fetch(`/employees/${id}`, { method: 'DELETE' });
    const result = await res.json();

    if (!res.ok) {
      showToast(result.error || 'Failed to delete employee.', 'danger');
      return;
    }

    showToast(result.message, 'success');
    loadEmployeesTable();
  } catch (err) {
    showToast('Network error while deleting employee.', 'danger');
  } finally {
    hideSpinner();
  }
}

// ----------------- PROFILE MODAL & SVG GAUGE ----------------- //

async function viewEmployeeProfile(id) {
  showSpinner();
  try {
    const res = await fetch(`/api/employees/${id}`);
    if (!res.ok) throw new Error('Employee not found');
    const emp = await res.json();

    // Populate profile fields
    const avatar = document.getElementById('profileModalAvatar');
    avatar.textContent = getInitials(emp.employee_name);
    avatar.style.backgroundColor = getAvatarColor(emp.employee_name);

    document.getElementById('profileModalName').textContent = emp.employee_name;
    document.getElementById('profileModalId').textContent = emp.employee_id;
    document.getElementById('profileModalDept').textContent = emp.department;

    const statusBadge = document.getElementById('profileModalStatus');
    statusBadge.textContent = emp.status;
    statusBadge.className = `badge badge-${emp.status_badge}`;

    // SVG Gauge calculation
    const radius = 45;
    const circumference = 2 * Math.PI * radius;
    const pct = Math.min(100, Math.max(0, emp.attendance_percentage));
    const offset = circumference - (pct / 100) * circumference;

    const gaugeCircle = document.getElementById('profileGaugeCircle');
    gaugeCircle.style.strokeDasharray = `${circumference} ${circumference}`;
    gaugeCircle.style.strokeDashoffset = offset;
    
    // Gauge color
    let strokeColor = '#EF4444';
    if (pct >= 90) strokeColor = '#10B981';
    else if (pct >= 75) strokeColor = '#F59E0B';
    gaugeCircle.style.stroke = strokeColor;

    document.getElementById('profileGaugeVal').textContent = `${emp.attendance_percentage}%`;
    document.getElementById('profileDaysPresent').textContent = `${emp.days_present} Days`;
    document.getElementById('profileTotalDays').textContent = `${emp.total_working_days} Days`;

    // Financials
    document.getElementById('profileBasicSalary').textContent = `₹${emp.basic_salary.toLocaleString('en-IN')}`;
    document.getElementById('profileOTPay').textContent = `₹${emp.overtime_pay.toLocaleString('en-IN')}`;
    document.getElementById('profileOTDetails').textContent = `${emp.overtime_hours} hrs @ ₹${emp.overtime_rate}/hr`;
    document.getElementById('profileFinalSalary').textContent = `₹${emp.final_salary.toLocaleString('en-IN')}`;

    // Action buttons inside profile
    document.getElementById('profileSalarySlipBtn').onclick = () => {
      closeModal('profileModal');
      openSalarySlipModal(emp.id);
    };

    document.getElementById('profileEditBtn').onclick = () => {
      closeModal('profileModal');
      editEmployee(emp.id);
    };

    openModal('profileModal');
  } catch (err) {
    showToast('Failed to load profile.', 'danger');
  } finally {
    hideSpinner();
  }
}

// ----------------- SALARY SLIP MODAL & PDF ----------------- //

async function openSalarySlipModal(id) {
  showSpinner();
  try {
    const res = await fetch(`/api/employees/${id}`);
    if (!res.ok) throw new Error('Employee not found');
    const emp = await res.json();

    document.getElementById('slipEmpName').textContent = emp.employee_name;
    document.getElementById('slipEmpId').textContent = emp.employee_id;
    document.getElementById('slipDept').textContent = emp.department;
    document.getElementById('slipAttRate').textContent = `${emp.attendance_percentage}% (${emp.days_present}/${emp.total_working_days} days)`;
    document.getElementById('slipBasic').textContent = `₹${emp.basic_salary.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
    document.getElementById('slipOT').textContent = `₹${emp.overtime_pay.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
    document.getElementById('slipOTDetails').textContent = `(${emp.overtime_hours} hrs @ ₹${emp.overtime_rate}/hr)`;
    document.getElementById('slipGross').textContent = `₹${emp.final_salary.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
    document.getElementById('slipNetPay').textContent = `₹${emp.final_salary.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;

    // PDF Download Link
    const pdfBtn = document.getElementById('slipDownloadPdfBtn');
    if (pdfBtn) {
      pdfBtn.href = `/salary-slip/${emp.employee_id}/pdf`;
    }

    openModal('salarySlipModal');
  } catch (err) {
    showToast('Failed to generate payslip preview.', 'danger');
  } finally {
    hideSpinner();
  }
}

// ----------------- CSV UPLOAD MODAL ----------------- //

function initCsvUpload() {
  const dropZone = document.getElementById('csvDropZone');
  const fileInput = document.getElementById('csvFileInput');
  const fileNameDisplay = document.getElementById('csvSelectedFileName');
  const uploadForm = document.getElementById('csvUploadForm');

  if (!dropZone || !fileInput) return;

  dropZone.addEventListener('click', () => fileInput.click());

  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.add('drag-over');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.remove('drag-over');
    });
  });

  dropZone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    if (dt.files && dt.files.length > 0) {
      fileInput.files = dt.files;
      fileNameDisplay.textContent = `Selected: ${dt.files[0].name}`;
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files && fileInput.files.length > 0) {
      fileNameDisplay.textContent = `Selected: ${fileInput.files[0].name}`;
    }
  });

  if (uploadForm) {
    uploadForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!fileInput.files || fileInput.files.length === 0) {
        showToast('Please select a CSV file first.', 'warning');
        return;
      }

      const formData = new FormData();
      formData.append('file', fileInput.files[0]);

      showSpinner();
      try {
        const res = await fetch('/upload', { method: 'POST', body: formData });
        const result = await res.json();

        if (!res.ok) {
          showToast(result.error || 'Upload failed.', 'danger');
          return;
        }

        showToast(result.message, 'success');
        closeModal('csvUploadModal');
        uploadForm.reset();
        fileNameDisplay.textContent = '';

        // Reload current view
        if (document.getElementById('employeeTableBody')) loadEmployeesTable();
        if (document.getElementById('kpiTotalEmployees')) loadDashboardData();
      } catch (err) {
        showToast('Error uploading CSV file.', 'danger');
      } finally {
        hideSpinner();
      }
    });
  }
}

// ----------------- THRESHOLD PAGE HANDLER ----------------- //

async function loadThresholdPage(val = 75) {
  const tbody = document.getElementById('thresholdTableBody');
  if (!tbody) return; // Not on threshold page

  currentThresholdVal = val;

  // Update button active styles
  document.querySelectorAll('.threshold-select-btn').forEach(btn => {
    if (parseInt(btn.getAttribute('data-val')) === val) {
      btn.classList.add('btn-primary');
      btn.classList.remove('btn-secondary');
    } else {
      btn.classList.remove('btn-primary');
      btn.classList.add('btn-secondary');
    }
  });

  showSpinner();
  try {
    const res = await fetch(`/api/threshold?threshold=${val}`);
    const data = await res.json();

    document.getElementById('thresholdCount').textContent = data.below_count;
    document.getElementById('thresholdPct').textContent = `${data.percentage_below}%`;
    document.getElementById('thresholdBenchmarkVal').textContent = `${val}%`;

    if (data.employees.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="9" style="text-align:center;padding:40px;color:var(--text-muted);">
            <i class="fas fa-check-circle" style="font-size:32px;color:var(--success);margin-bottom:10px;display:block;"></i>
            Excellent! All employees are currently meeting or exceeding the ${val}% attendance benchmark.
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = data.employees.map(emp => `
      <tr>
        <td><strong>${emp.employee_id}</strong></td>
        <td>
          <div class="emp-profile-cell">
            <div class="initials-avatar" style="background:${getAvatarColor(emp.employee_name)}">
              ${getInitials(emp.employee_name)}
            </div>
            <div>
              <div class="emp-info-name">${emp.employee_name}</div>
              <div class="emp-info-sub">ID: ${emp.employee_id}</div>
            </div>
          </div>
        </td>
        <td><span class="badge badge-dept">${emp.department}</span></td>
        <td style="text-align:center;">${emp.days_present} / ${emp.total_working_days}</td>
        <td>
          <span class="badge badge-danger" style="font-size:12.5px;">
            <i class="fas fa-exclamation-triangle"></i> ${emp.attendance_percentage}%
          </span>
        </td>
        <td>₹${emp.basic_salary.toLocaleString('en-IN')}</td>
        <td>₹${emp.final_salary.toLocaleString('en-IN')}</td>
        <td>
          <div class="table-actions">
            <button class="action-btn view-btn" title="View Profile" onclick="viewEmployeeProfile(${emp.id})">
              <i class="fas fa-eye"></i>
            </button>
            <button class="action-btn edit-btn" title="Edit Employee" onclick="editEmployee(${emp.id})">
              <i class="fas fa-edit"></i>
            </button>
            <button class="action-btn slip-btn" title="Salary Slip" onclick="openSalarySlipModal(${emp.id})">
              <i class="fas fa-file-invoice-dollar"></i>
            </button>
          </div>
        </td>
      </tr>
    `).join('');

  } catch (err) {
    showToast('Failed to load threshold data.', 'danger');
  } finally {
    hideSpinner();
  }
}

// ----------------- REPORTS PAGE HANDLER ----------------- //

async function loadReportsPage() {
  const reportContainer = document.getElementById('reportDetailsContainer');
  if (!reportContainer) return; // Not on reports page

  showSpinner();
  try {
    const res = await fetch('/api/report-data?threshold=75');
    const data = await res.json();
    const sum = data.summary;

    document.getElementById('repTotalWorkforce').textContent = sum.total_employees;
    document.getElementById('repAvgAttendance').textContent = `${sum.avg_attendance}%`;
    document.getElementById('repHighestAttendance').textContent = `${sum.max_attendance}% (${sum.max_att_emp})`;
    document.getElementById('repLowestAttendance').textContent = `${sum.min_attendance}% (${sum.min_att_emp})`;
    document.getElementById('repTotalOTHours').textContent = `${sum.total_ot_hours.toFixed(1)} hrs`;
    document.getElementById('repTotalOTPay').textContent = `₹${sum.total_ot_pay.toLocaleString('en-IN')}`;
    document.getElementById('repTotalBasic').textContent = `₹${sum.total_basic_expense.toLocaleString('en-IN')}`;
    document.getElementById('repTotalSalary').textContent = `₹${sum.total_salary_expense.toLocaleString('en-IN')}`;
    document.getElementById('repBelowCount').textContent = sum.below_threshold_count;

    // Populate Department breakdown table
    const deptBody = document.getElementById('reportDeptTableBody');
    if (deptBody) {
      deptBody.innerHTML = data.dept_stats.map(d => `
        <tr>
          <td><strong>${d.department}</strong></td>
          <td style="text-align:center;">${d.count}</td>
          <td style="text-align:center;"><span class="badge ${d.avg_attendance >= 80 ? 'badge-success' : 'badge-warning'}">${d.avg_attendance}%</span></td>
          <td>₹${d.total_basic.toLocaleString('en-IN')}</td>
          <td>₹${d.total_ot.toLocaleString('en-IN')}</td>
          <td><strong>₹${d.total_final.toLocaleString('en-IN')}</strong></td>
        </tr>
      `).join('');
    }

  } catch (err) {
    showToast('Failed to load summary reports.', 'danger');
  } finally {
    hideSpinner();
  }
}

// ----------------- INITIALIZATION ON DOM READY ----------------- //

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initCsvUpload();

  // Clock
  updateLiveClock();
  setInterval(updateLiveClock, 1000);

  // Employee Form submit
  const empForm = document.getElementById('employeeForm');
  if (empForm) empForm.addEventListener('submit', saveEmployee);

  // Search and Filter Listeners for Employees Page
  const searchInput = document.getElementById('tableSearchInput');
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener('input', (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        currentSearchTerm = e.target.value.trim();
        currentEmployeesPage = 1;
        loadEmployeesTable();
      }, 300);
    });
  }

  const deptSelect = document.getElementById('tableDeptFilter');
  if (deptSelect) {
    deptSelect.addEventListener('change', (e) => {
      currentDeptFilter = e.target.value;
      currentEmployeesPage = 1;
      loadEmployeesTable();
    });
  }

  const statusSelect = document.getElementById('tableStatusFilter');
  if (statusSelect) {
    statusSelect.addEventListener('change', (e) => {
      currentStatusFilter = e.target.value;
      currentEmployeesPage = 1;
      loadEmployeesTable();
    });
  }

  const sortSelect = document.getElementById('tableSortSelect');
  if (sortSelect) {
    sortSelect.addEventListener('change', (e) => {
      const [field, order] = e.target.value.split('-');
      currentSortBy = field;
      currentSortOrder = order || 'asc';
      loadEmployeesTable();
    });
  }

  // Page Specific Loaders
  loadDashboardData();
  loadEmployeesTable();
  loadThresholdPage(75);
  loadReportsPage();
});
