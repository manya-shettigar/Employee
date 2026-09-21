# Employee Attendance & Salary Processing System

A **full-stack enterprise web application** built with **HTML5, CSS3, JavaScript, Python (Flask), SQLite, Chart.js, Pandas, and ReportLab**.

The system provides complete human resource attendance tracking and automated payroll disbursement calculations with modern corporate aesthetics, interactive visualizations, PDF report generation, and CSV batch processing.

---

## 🚀 Key Features

### 1. 🔐 Authentication & Session Security
- Admin Login page with username and password authentication (`admin` / `admin123`).
- Convenient **"Quick Fill" demo credentials** button for instant testing.
- Secure session state management and protected administrative routes.
- Logout functionality.

### 2. 📊 Executive Dashboard
- **Real-Time Clock**: Live digital clock with seconds ticker.
- **5 KPI Metric Cards**:
  - Total Workforce Headcount
  - Average Company Attendance Percentage
  - Employees Below Attendance Threshold
  - Total Monthly Salary Expense
  - Total Overtime Pay Disbursed
- **Quick Action Buttons**: Add Employee, Upload CSV, Download Processed CSV, Summary Report.
- **5 Interactive Chart.js Visualizations**:
  1. *Department Distribution* (Doughnut Chart)
  2. *Attendance Comparison by Department* (Bar Chart)
  3. *Average Salary Comparison* (Line / Area Chart)
  4. *Attendance Status Breakdown* (Doughnut Chart: Excellent vs Good vs Below Threshold)
  5. *Monthly Department Payroll Breakdown* (Stacked Bar: Basic Pay vs Overtime Pay)
- **Attendance Deficiency Alerts**: Real-time ticker of personnel with lowest recorded attendance.

### 3. 👥 Employee Management (Full CRUD)
- Comprehensive employee records table with **25 employees per page** pagination.
- **Search & Filtering**:
  - Real-time search by Employee Name or Employee ID (e.g. `EMP045`)
  - Department filter (IT, HR, Finance, Sales, Marketing, Operations, Support)
  - Attendance Status filter (Excellent ≥90%, Good 75–89%, Below Threshold <75%)
  - Sorting: By Salary (High/Low), Attendance (High/Low), Name, or ID.
- **Strict Data Validation**:
  - Unique Employee ID enforcement
  - Days Present cannot exceed Total Working Days
  - Positive salary and non-negative overtime hours/rates
  - Required fields checking
- **Employee Profile Modal**:
  - Initials Avatar with dynamic color hashing
  - SVG Circular Attendance Progress Gauge
  - Salary and Overtime breakdown
  - Direct links to edit or generate individual payslip.

### 4. 🧮 Automated Payroll Calculations
- **Attendance Percentage**: `(Days Present / Total Working Days) × 100`
- **Overtime Pay**: `Overtime Hours × Overtime Rate`
- **Final Salary**: `Basic Salary + Overtime Pay`
- **Status Classification**:
  - 🟢 **Excellent**: ≥ 90% (Green badge)
  - 🟡 **Good**: 75% – 89.9% (Yellow badge)
  - 🔴 **Below Threshold**: < 75% (Red badge)

### 5. ⚠️ Attendance Threshold Monitor
- Dedicated compliance page to identify at-risk personnel.
- Interactive threshold switcher: **60%**, **70%**, **75%** (Default), **80%**, and **90%**.
- Real-time impact metric showing percentage of company workforce affected.

### 6. 📄 Reports & PDF Generation (ReportLab)
- **Executive Summary Report**:
  - Company-wide payroll and attendance statistics.
  - Department-wise breakdown table.
  - One-click **Print Report** styling (`@media print`).
  - **Download Official PDF**: Server-side PDF rendered with ReportLab featuring header banner, KPI blocks, departmental tables, page numbering, and executive sign-off.
- **Individual Employee Salary Slip**:
  - Corporate payslip preview modal.
  - **Download Salary Slip PDF**: Formal ReportLab document with company address, employee metadata, itemized earnings/deductions, and electronic authentication.

### 7. 📁 CSV Batch Import & Export
- **CSV Upload**: Drag-and-drop file uploader with automatic header validation and upsert logic.
- **Processed CSV Download**: Exports complete roster with computed metrics (`attendance_percentage`, `overtime_pay`, `final_salary`, `status`).
- **Sample CSV**: Downloadable pre-formatted template (`data/sample_employees.csv`).

### 8. 🌟 Bonus Features
- 🌙 **Dark Mode Toggle**: Persistent dark theme with localStorage synchronization.
- 🔔 **Toast Notification System**: Animated feedback for additions, edits, deletions, and errors.
- ⏳ **Loading Spinner**: Visual feedback during asynchronous API and network operations.
- 🖨️ **Print Support**: Dedicated print stylesheets for paper or PDF printing.
- ⌨️ **Keyboard Accessibility**: Modal dismissal with `Escape` key, intuitive tab navigation.

---

## 🗄️ Database & Preloaded Records

The application automatically seeds **500 realistic employee records** into SQLite (`database.db`) and exports `data/sample_employees.csv`:
- IDs: `EMP001` to `EMP500`
- Authentic Indian male and female names
- Distributed across 7 departments: IT, HR, Finance, Sales, Marketing, Operations, Support
- Working days: 24–31
- Days present: 15–31
- Basic salary: ₹20,000 to ₹80,000
- Overtime hours: 0–40 hrs @ ₹150–₹500/hr
- At least 50+ employees intentionally configured below the 75% attendance threshold for realistic policy auditing.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | HTML5, CSS3 (Modern Executive Theme), Vanilla JavaScript (ES6+) |
| **Styling** | Custom CSS Design System, CSS Variables, Glassmorphism, FontAwesome 6, Google Fonts (Inter) |
| **Charts** | Chart.js 4.4 |
| **Backend** | Python 3.12, Flask 3.1 |
| **Database** | SQLite3 (`database.db`) |
| **Data Engine** | Pandas (CSV ingestion, aggregation, and export) |
| **PDF Engine** | ReportLab (Vector PDF synthesis with styles, tables, and canvas) |

---

## 📦 Installation & Setup

### Prerequisites
- Python 3.8+ installed on your system.

### Steps to Run

1. **Clone or navigate to the project directory**:
   ```bash
   cd Employee
   ```

2. **Install required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch the Flask application**:
   ```bash
   python app.py
   ```

4. **Access in your web browser**:
   Open [http://127.0.0.1:5000](http://127.0.0.1:5000)

5. **Sign in with Admin Credentials**:
   - **Username**: `admin`
   - **Password**: `admin123`
   *(or click the "Quick Fill" button on the login screen)*

---

## 📁 Directory Structure

```text
Employee/
├── app.py                     # Flask web server, API endpoints, routes, CSV & PDF handling
├── seed_data.py               # 500-record generator & SQLite seeding script
├── pdf_generator.py           # ReportLab PDF generator for Summary & Salary Slips
├── database.db                # SQLite database with 500 preloaded employee records
├── requirements.txt           # Python dependencies
├── README.md                  # Project documentation & manual
├── data/
│   └── sample_employees.csv   # Pre-generated 500 employee records CSV
├── uploads/                   # Temporary directory for uploaded CSV files
├── exports/                   # Temporary directory for generated files
├── templates/
│   ├── base.html              # Core layout, navbar, modals, toasts, live clock
│   ├── login.html             # Admin login page
│   ├── dashboard.html         # Executive dashboard with 5 KPI cards and 5 Chart.js charts
│   ├── employees.html         # Employee directory, CRUD, filters, search, pagination
│   ├── threshold.html         # Attendance threshold compliance monitor
│   └── reports.html           # Summary report and PDF export view
└── static/
    ├── css/
    │   └── style.css          # Modern corporate blue/white design system & dark mode
    ├── js/
    │   ├── script.js          # Core client logic, modals, API calls, pagination, toasts
    │   └── charts.js          # 5 interactive Chart.js visualizations
    └── images/
```
