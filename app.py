import os
import sqlite3
import pandas as pd
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, send_file, make_response
)
from seed_data import init_database, DB_PATH, CSV_PATH
from pdf_generator import generate_summary_pdf, generate_salary_slip_pdf

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ems-super-secret-key-2026-attendance-salary')

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
EXPORTS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXPORTS_FOLDER, exist_ok=True)

# Ensure database is initialized on start
init_database(force=False)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def calculate_employee_fields(emp):
    """Adds attendance_percentage, overtime_pay, final_salary, and status to an employee dict."""
    total_days = emp['total_working_days'] if emp['total_working_days'] > 0 else 1
    days_present = emp['days_present']
    att_pct = round((days_present / total_days) * 100, 1)
    
    ot_hours = float(emp['overtime_hours'])
    ot_rate = float(emp['overtime_rate'])
    ot_pay = round(ot_hours * ot_rate, 2)
    
    basic = float(emp['basic_salary'])
    final_salary = round(basic + ot_pay, 2)
    
    if att_pct >= 90.0:
        status = "Excellent"
        status_badge = "success"
    elif att_pct >= 75.0:
        status = "Good"
        status_badge = "warning"
    else:
        status = "Below Threshold"
        status_badge = "danger"
        
    emp_copy = dict(emp)
    emp_copy['attendance_percentage'] = att_pct
    emp_copy['overtime_pay'] = ot_pay
    emp_copy['final_salary'] = final_salary
    emp_copy['status'] = status
    emp_copy['status_badge'] = status_badge
    return emp_copy

# ----------------- AUTH ROUTES ----------------- #

@app.route('/')
def index():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
        
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # Default credentials: admin / admin123
        if username == 'admin' and password == 'admin123':
            session['logged_in'] = True
            session['user'] = 'Admin'
            flash('Welcome back! Successfully logged into EMS.', 'success')
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid credentials. Please check your username and password.'
            
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

# ----------------- DASHBOARD & ANALYTICS ----------------- #

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/dashboard-stats')
@login_required
def api_dashboard_stats():
    threshold_val = float(request.args.get('threshold', 75))
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute('SELECT * FROM employees')
    rows = [calculate_employee_fields(dict(r)) for r in cur.fetchall()]
    conn.close()
    
    total_employees = len(rows)
    if total_employees == 0:
        return jsonify({
            'total_employees': 0, 'avg_attendance': 0, 'below_threshold_count': 0,
            'total_salary_expense': 0, 'total_ot_pay': 0, 'total_ot_hours': 0,
            'department_counts': {}, 'dept_attendance': {}, 'dept_salaries': {},
            'status_distribution': {'Excellent': 0, 'Good': 0, 'Below Threshold': 0}
        })
        
    df = pd.DataFrame(rows)
    
    avg_attendance = round(df['attendance_percentage'].mean(), 1)
    below_threshold = int((df['attendance_percentage'] < threshold_val).sum())
    total_salary = round(df['final_salary'].sum(), 2)
    total_ot_pay = round(df['overtime_pay'].sum(), 2)
    total_ot_hours = round(df['overtime_hours'].sum(), 1)
    
    # Department distribution
    dept_group = df.groupby('department')
    dept_counts = dept_group.size().to_dict()
    dept_avg_att = dept_group['attendance_percentage'].mean().round(1).to_dict()
    dept_avg_sal = dept_group['final_salary'].mean().round(2).to_dict()
    dept_total_basic = dept_group['basic_salary'].sum().round(2).to_dict()
    dept_total_ot = dept_group['overtime_pay'].sum().round(2).to_dict()
    dept_total_final = dept_group['final_salary'].sum().round(2).to_dict()
    
    # Status distribution
    status_counts = df['status'].value_counts().to_dict()
    for s in ['Excellent', 'Good', 'Below Threshold']:
        if s not in status_counts:
            status_counts[s] = 0
            
    # Recent alerts: lowest 5 attendance employees
    lowest_att_emps = df.sort_values(by='attendance_percentage', ascending=True).head(5).to_dict('records')
    
    return jsonify({
        'total_employees': total_employees,
        'avg_attendance': avg_attendance,
        'below_threshold_count': below_threshold,
        'threshold_value': threshold_val,
        'total_salary_expense': total_salary,
        'total_ot_pay': total_ot_pay,
        'total_ot_hours': total_ot_hours,
        'department_counts': dept_counts,
        'dept_avg_attendance': dept_avg_att,
        'dept_avg_salary': dept_avg_sal,
        'dept_total_basic': dept_total_basic,
        'dept_total_ot': dept_total_ot,
        'dept_total_final': dept_total_final,
        'status_distribution': status_counts,
        'lowest_attendance_alerts': lowest_att_emps
    })

# ----------------- EMPLOYEE CRUD & TABLE ----------------- #

@app.route('/employees')
@login_required
def employees_page():
    return render_template('employees.html')

@app.route('/api/employees')
@login_required
def api_employees():
    search = request.args.get('search', '').strip().lower()
    department = request.args.get('department', 'all')
    status_filter = request.args.get('status', 'all')
    sort_by = request.args.get('sort_by', 'id')
    order = request.args.get('order', 'asc').lower()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 25))
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM employees')
    raw_rows = cur.fetchall()
    conn.close()
    
    all_employees = [calculate_employee_fields(dict(r)) for r in raw_rows]
    
    # Filter by search
    if search:
        all_employees = [
            e for e in all_employees
            if search in e['employee_name'].lower() or search in e['employee_id'].lower()
        ]
        
    # Filter by department
    if department != 'all':
        all_employees = [e for e in all_employees if e['department'] == department]
        
    # Filter by status
    if status_filter != 'all':
        all_employees = [e for e in all_employees if e['status'] == status_filter]
        
    # Sort
    reverse = (order == 'desc')
    if sort_by in ['attendance_percentage', 'overtime_pay', 'final_salary']:
        all_employees.sort(key=lambda x: x[sort_by], reverse=reverse)
    elif sort_by in ['basic_salary', 'days_present', 'total_working_days', 'overtime_hours', 'overtime_rate', 'id']:
        all_employees.sort(key=lambda x: float(x[sort_by]), reverse=reverse)
    elif sort_by in ['employee_id', 'employee_name', 'department', 'status']:
        all_employees.sort(key=lambda x: str(x[sort_by]).lower(), reverse=reverse)
        
    total_count = len(all_employees)
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    page = min(max(1, page), total_pages)
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_employees = all_employees[start_idx:end_idx]
    
    return jsonify({
        'employees': paginated_employees,
        'total_count': total_count,
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages
    })

@app.route('/api/employees/<emp_id>')
@login_required
def api_get_employee(emp_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM employees WHERE employee_id = ? OR id = ?', (emp_id, emp_id))
    row = cur.fetchone()
    conn.close()
    
    if not row:
        return jsonify({'error': 'Employee not found'}), 404
        
    emp = calculate_employee_fields(dict(row))
    return jsonify(emp)

@app.route('/employees', methods=['POST'])
@login_required
def add_employee():
    data = request.get_json() or request.form
    
    emp_id = data.get('employee_id', '').strip().upper()
    emp_name = data.get('employee_name', '').strip()
    department = data.get('department', '').strip()
    
    # Validations
    if not emp_id or not emp_name or not department:
        return jsonify({'error': 'Employee ID, Name, and Department are required.'}), 400
        
    try:
        working_days = int(data.get('total_working_days', 0))
        days_present = int(data.get('days_present', 0))
        basic_salary = float(data.get('basic_salary', 0))
        overtime_hours = float(data.get('overtime_hours', 0))
        overtime_rate = float(data.get('overtime_rate', 0))
    except (ValueError, TypeError):
        return jsonify({'error': 'Numeric fields must contain valid numbers.'}), 400
        
    if working_days <= 0:
        return jsonify({'error': 'Total working days must be greater than zero.'}), 400
    if days_present < 0 or days_present > working_days:
        return jsonify({'error': f'Days present ({days_present}) cannot exceed total working days ({working_days}) or be negative.'}), 400
    if basic_salary < 0:
        return jsonify({'error': 'Basic salary cannot be negative.'}), 400
    if overtime_hours < 0:
        return jsonify({'error': 'Overtime hours cannot be negative.'}), 400
    if overtime_rate < 0:
        return jsonify({'error': 'Overtime rate cannot be negative.'}), 400
        
    conn = get_db()
    cur = conn.cursor()
    
    # Check uniqueness of employee_id
    cur.execute('SELECT id FROM employees WHERE employee_id = ?', (emp_id,))
    if cur.fetchone():
        conn.close()
        return jsonify({'error': f'Employee ID "{emp_id}" already exists. Please choose a unique ID.'}), 400
        
    cur.execute('''
        INSERT INTO employees (employee_id, employee_name, department, total_working_days, days_present, basic_salary, overtime_hours, overtime_rate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (emp_id, emp_name, department, working_days, days_present, basic_salary, overtime_hours, overtime_rate))
    
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': f'Employee {emp_name} ({emp_id}) added successfully!', 'id': new_id}), 201

@app.route('/employees/<int:emp_db_id>', methods=['PUT'])
@login_required
def update_employee(emp_db_id):
    data = request.get_json() or request.form
    
    emp_id = data.get('employee_id', '').strip().upper()
    emp_name = data.get('employee_name', '').strip()
    department = data.get('department', '').strip()
    
    if not emp_id or not emp_name or not department:
        return jsonify({'error': 'Employee ID, Name, and Department are required.'}), 400
        
    try:
        working_days = int(data.get('total_working_days', 0))
        days_present = int(data.get('days_present', 0))
        basic_salary = float(data.get('basic_salary', 0))
        overtime_hours = float(data.get('overtime_hours', 0))
        overtime_rate = float(data.get('overtime_rate', 0))
    except (ValueError, TypeError):
        return jsonify({'error': 'Numeric fields must contain valid numbers.'}), 400
        
    if working_days <= 0:
        return jsonify({'error': 'Total working days must be greater than zero.'}), 400
    if days_present < 0 or days_present > working_days:
        return jsonify({'error': f'Days present ({days_present}) cannot exceed total working days ({working_days}) or be negative.'}), 400
    if basic_salary < 0:
        return jsonify({'error': 'Basic salary cannot be negative.'}), 400
    if overtime_hours < 0 or overtime_rate < 0:
        return jsonify({'error': 'Overtime values cannot be negative.'}), 400
        
    conn = get_db()
    cur = conn.cursor()
    
    # Check uniqueness of employee_id excluding current record
    cur.execute('SELECT id FROM employees WHERE employee_id = ? AND id != ?', (emp_id, emp_db_id))
    if cur.fetchone():
        conn.close()
        return jsonify({'error': f'Employee ID "{emp_id}" is already used by another employee.'}), 400
        
    cur.execute('''
        UPDATE employees
        SET employee_id = ?, employee_name = ?, department = ?, total_working_days = ?,
            days_present = ?, basic_salary = ?, overtime_hours = ?, overtime_rate = ?
        WHERE id = ?
    ''', (emp_id, emp_name, department, working_days, days_present, basic_salary, overtime_hours, overtime_rate, emp_db_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': f'Employee {emp_name} updated successfully!'})

@app.route('/employees/<int:emp_db_id>', methods=['DELETE'])
@login_required
def delete_employee(emp_db_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT employee_name, employee_id FROM employees WHERE id = ?', (emp_db_id,))
    emp = cur.fetchone()
    
    if not emp:
        conn.close()
        return jsonify({'error': 'Employee not found.'}), 404
        
    cur.execute('DELETE FROM employees WHERE id = ?', (emp_db_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': f'Employee {emp["employee_name"]} ({emp["employee_id"]}) deleted.'})

# ----------------- ATTENDANCE THRESHOLD MONITOR ----------------- #

@app.route('/threshold')
@login_required
def threshold_page():
    return render_template('threshold.html')

@app.route('/api/threshold')
@login_required
def api_threshold():
    threshold_val = float(request.args.get('threshold', 75))
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM employees')
    rows = [calculate_employee_fields(dict(r)) for r in cur.fetchall()]
    conn.close()
    
    below_emps = [e for e in rows if e['attendance_percentage'] < threshold_val]
    below_emps.sort(key=lambda x: x['attendance_percentage'])
    
    return jsonify({
        'threshold_value': threshold_val,
        'total_employees': len(rows),
        'below_count': len(below_emps),
        'percentage_below': round((len(below_emps) / len(rows) * 100), 1) if len(rows) > 0 else 0,
        'employees': below_emps
    })

# ----------------- REPORTS & PDF GENERATION ----------------- #

@app.route('/reports')
@login_required
def reports_page():
    return render_template('reports.html')

def get_complete_report_data(threshold_val=75.0):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM employees')
    raw_rows = cur.fetchall()
    conn.close()
    
    rows = [calculate_employee_fields(dict(r)) for r in raw_rows]
    df = pd.DataFrame(rows)
    
    if len(df) == 0:
        return {}, []
        
    avg_att = round(df['attendance_percentage'].mean(), 1)
    max_row = df.loc[df['attendance_percentage'].idxmax()]
    min_row = df.loc[df['attendance_percentage'].idxmin()]
    
    below_threshold_count = int((df['attendance_percentage'] < threshold_val).sum())
    total_ot_hours = round(df['overtime_hours'].sum(), 1)
    total_ot_pay = round(df['overtime_pay'].sum(), 2)
    total_basic_expense = round(df['basic_salary'].sum(), 2)
    total_salary_expense = round(df['final_salary'].sum(), 2)
    
    summary_data = {
        'total_employees': len(df),
        'avg_attendance': avg_att,
        'max_attendance': max_row['attendance_percentage'],
        'max_att_emp': f"{max_row['employee_name']} ({max_row['employee_id']})",
        'min_attendance': min_row['attendance_percentage'],
        'min_att_emp': f"{min_row['employee_name']} ({min_row['employee_id']})",
        'total_ot_hours': total_ot_hours,
        'total_ot_pay': total_ot_pay,
        'total_basic_expense': total_basic_expense,
        'total_salary_expense': total_salary_expense,
        'below_threshold_count': below_threshold_count
    }
    
    dept_group = df.groupby('department')
    dept_stats = []
    for dept_name, group in dept_group:
        dept_stats.append({
            'department': dept_name,
            'count': len(group),
            'avg_attendance': round(group['attendance_percentage'].mean(), 1),
            'total_basic': round(group['basic_salary'].sum(), 2),
            'total_ot': round(group['overtime_pay'].sum(), 2),
            'total_final': round(group['final_salary'].sum(), 2)
        })
        
    dept_stats.sort(key=lambda x: x['count'], reverse=True)
    return summary_data, dept_stats

@app.route('/api/report-data')
@login_required
def api_report_data():
    threshold_val = float(request.args.get('threshold', 75))
    summary_data, dept_stats = get_complete_report_data(threshold_val)
    return jsonify({
        'summary': summary_data,
        'dept_stats': dept_stats,
        'generated_at': datetime.now().strftime("%d %b %Y, %I:%M %p")
    })

@app.route('/report/pdf')
@login_required
def download_summary_pdf():
    threshold_val = float(request.args.get('threshold', 75))
    summary_data, dept_stats = get_complete_report_data(threshold_val)
    pdf_bytes = generate_summary_pdf(summary_data, dept_stats, threshold_val)
    
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    filename = f"EMS_Summary_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response

@app.route('/salary-slip/<emp_id>/pdf')
@login_required
def download_salary_slip(emp_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM employees WHERE employee_id = ? OR id = ?', (emp_id, emp_id))
    row = cur.fetchone()
    conn.close()
    
    if not row:
        return "Employee not found", 404
        
    emp = calculate_employee_fields(dict(row))
    pdf_bytes = generate_salary_slip_pdf(emp)
    
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    filename = f"Salary_Slip_{emp['employee_id']}_{datetime.now().strftime('%b_%Y')}.pdf"
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response

# ----------------- CSV UPLOAD & DOWNLOAD ----------------- #

@app.route('/upload', methods=['POST'])
@login_required
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Only CSV files (.csv) are allowed'}), 400
        
    try:
        df = pd.read_csv(file)
        
        required_cols = [
            'employee_id', 'employee_name', 'department',
            'total_working_days', 'days_present', 'basic_salary',
            'overtime_hours', 'overtime_rate'
        ]
        
        # Check column headers (case-insensitive and trimmed)
        df.columns = [c.strip().lower() for c in df.columns]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return jsonify({
                'error': f'Missing required columns in CSV: {", ".join(missing_cols)}. Expected headers: {", ".join(required_cols)}'
            }), 400
            
        conn = get_db()
        cur = conn.cursor()
        
        imported_count = 0
        updated_count = 0
        errors = []
        
        for idx, row in df.iterrows():
            row_num = idx + 2
            try:
                emp_id = str(row['employee_id']).strip().upper()
                emp_name = str(row['employee_name']).strip()
                department = str(row['department']).strip()
                working_days = int(row['total_working_days'])
                days_present = int(row['days_present'])
                basic_salary = float(row['basic_salary'])
                ot_hours = float(row['overtime_hours'])
                ot_rate = float(row['overtime_rate'])
                
                if not emp_id or not emp_name:
                    errors.append(f"Row {row_num}: Employee ID and Name cannot be empty.")
                    continue
                if working_days <= 0:
                    errors.append(f"Row {row_num} ({emp_id}): Working days must be > 0.")
                    continue
                if days_present < 0 or days_present > working_days:
                    errors.append(f"Row {row_num} ({emp_id}): Days present must be between 0 and {working_days}.")
                    continue
                if basic_salary < 0 or ot_hours < 0 or ot_rate < 0:
                    errors.append(f"Row {row_num} ({emp_id}): Financial values cannot be negative.")
                    continue
                    
                cur.execute('SELECT id FROM employees WHERE employee_id = ?', (emp_id,))
                existing = cur.fetchone()
                
                if existing:
                    cur.execute('''
                        UPDATE employees
                        SET employee_name = ?, department = ?, total_working_days = ?,
                            days_present = ?, basic_salary = ?, overtime_hours = ?, overtime_rate = ?
                        WHERE employee_id = ?
                    ''', (emp_name, department, working_days, days_present, basic_salary, ot_hours, ot_rate, emp_id))
                    updated_count += 1
                else:
                    cur.execute('''
                        INSERT INTO employees (employee_id, employee_name, department, total_working_days, days_present, basic_salary, overtime_hours, overtime_rate)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (emp_id, emp_name, department, working_days, days_present, basic_salary, ot_hours, ot_rate))
                    imported_count += 1
                    
            except Exception as e:
                errors.append(f"Row {row_num}: Format error ({str(e)})")
                
        conn.commit()
        conn.close()
        
        msg = f"Import completed: {imported_count} new employees added, {updated_count} updated."
        if errors:
            msg += f" Note: {len(errors)} rows had errors and were skipped."
            
        return jsonify({
            'success': True,
            'message': msg,
            'imported': imported_count,
            'updated': updated_count,
            'errors': errors[:10]  # First 10 error messages
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to process CSV file: {str(e)}'}), 500

@app.route('/download')
@login_required
def download_processed_csv():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM employees ORDER BY employee_id ASC')
    raw_rows = cur.fetchall()
    conn.close()
    
    rows = [calculate_employee_fields(dict(r)) for r in raw_rows]
    df = pd.DataFrame(rows)
    
    # Select and order required columns
    export_cols = [
        'employee_id', 'employee_name', 'department',
        'total_working_days', 'days_present', 'attendance_percentage',
        'basic_salary', 'overtime_hours', 'overtime_rate',
        'overtime_pay', 'final_salary', 'status'
    ]
    df_export = df[export_cols]
    
    csv_bytes = df_export.to_csv(index=False).encode('utf-8')
    response = make_response(csv_bytes)
    response.headers['Content-Type'] = 'text/csv'
    filename = f"EMS_Processed_Payroll_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response

@app.route('/download-sample')
@login_required
def download_sample_csv():
    if os.path.exists(CSV_PATH):
        return send_file(CSV_PATH, as_attachment=True, download_name='sample_employees.csv', mimetype='text/csv')
    return "Sample CSV not found", 404

if __name__ == '__main__':
    print("Starting Employee Attendance & Salary Processing System...")
    print("Access application at http://127.0.0.1:5000")
    print("Default Admin Login: username: admin | password: admin123")
    app.run(debug=True, host='0.0.0.0', port=5000)
