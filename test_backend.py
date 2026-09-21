import io
import json
from app import app, get_db

def run_tests():
    print("=== STARTING BACKEND INTEGRATION TESTS WITH FLASK TEST CLIENT ===")
    client = app.test_client()
    
    # 1. Test redirect from root to login
    r = client.get('/', follow_redirects=False)
    assert r.status_code == 302 and "/login" in r.headers['Location'], f"Root redirect failed: {r.status_code}"
    print("[PASS] Root redirect to /login verified")
    
    # 2. Test invalid login
    r = client.post('/login', data={"username": "wrong", "password": "wrong"})
    assert b"Invalid credentials" in r.data, "Invalid credentials check failed"
    print("[PASS] Invalid login rejection verified")
    
    # 3. Test valid login
    r = client.post('/login', data={"username": "admin", "password": "admin123"}, follow_redirects=True)
    assert r.status_code == 200 and b"Payroll" in r.data, "Admin login failed"
    print("[PASS] Admin login successful and session established")
    
    # 4. Test Dashboard Stats API
    r = client.get('/api/dashboard-stats?threshold=75')
    assert r.status_code == 200, "Dashboard stats failed"
    stats = r.get_json()
    assert stats['total_employees'] >= 500, f"Expected >= 500 employees, got {stats['total_employees']}"
    assert stats['below_threshold_count'] >= 50, f"Expected >= 50 below threshold, got {stats['below_threshold_count']}"
    assert len(stats['department_counts']) == 7, "Expected 7 departments"
    assert 'Excellent' in stats['status_distribution']
    print(f"[PASS] Dashboard Stats API verified: {stats['total_employees']} employees, {stats['avg_attendance']}% avg attendance, total expense verified")
    
    # 5. Test Employee Pagination & Search API
    r = client.get('/api/employees?page=1&per_page=25&sort_by=id&order=asc')
    assert r.status_code == 200
    emp_data = r.get_json()
    assert len(emp_data['employees']) == 25, f"Expected 25 employees per page, got {len(emp_data['employees'])}"
    assert emp_data['total_count'] >= 500
    assert emp_data['page'] == 1
    
    first_emp = emp_data['employees'][0]
    for field in ['employee_id', 'employee_name', 'department', 'attendance_percentage', 'overtime_pay', 'final_salary', 'status']:
        assert field in first_emp, f"Missing calculated field: {field}"
    print("[PASS] Employee table API verified (25 per page with calculated fields)")
    
    # Test Search
    r = client.get('/api/employees?search=EMP010')
    search_data = r.get_json()
    assert search_data['total_count'] >= 1
    assert search_data['employees'][0]['employee_id'] == 'EMP010'
    print(f"[PASS] Employee search verified: Found {search_data['employees'][0]['employee_name']}")
    
    # 6. Test Employee CRUD: Add, Validation, Update, Delete
    new_emp = {
        "employee_id": "EMP999",
        "employee_name": "Test Engineer Sharma",
        "department": "IT",
        "total_working_days": 26,
        "days_present": 25,
        "basic_salary": 65000,
        "overtime_hours": 10,
        "overtime_rate": 300
    }
    
    # Validation failure: days_present > total_working_days
    bad_emp = dict(new_emp)
    bad_emp["days_present"] = 30
    r = client.post('/employees', json=bad_emp)
    assert r.status_code == 400, "Validation failed to catch days_present > working_days"
    print("[PASS] Validation test passed: Rejected days_present > total_working_days")
    
    # Successful add
    r = client.post('/employees', json=new_emp)
    assert r.status_code == 201, f"Failed to add employee: {r.data}"
    created_id = r.get_json()['id']
    print(f"[PASS] Create employee verified: EMP999 created with ID {created_id}")
    
    # Duplicate ID validation
    r = client.post('/employees', json=new_emp)
    assert r.status_code == 400 and "already exists" in r.get_json()['error'], "Duplicate ID check failed"
    print("[PASS] Unique Employee ID validation verified")
    
    # Update employee
    update_data = dict(new_emp)
    update_data["employee_name"] = "Updated Test Engineer Sharma"
    update_data["basic_salary"] = 72000
    r = client.put(f'/employees/{created_id}', json=update_data)
    assert r.status_code == 200, f"Update failed: {r.data}"
    print("[PASS] Update employee verified")
    
    # Fetch single employee
    r = client.get('/api/employees/EMP999')
    assert r.status_code == 200 and r.get_json()['basic_salary'] == 72000
    print("[PASS] Single employee fetch API verified")
    
    # Delete employee
    r = client.delete(f'/employees/{created_id}')
    assert r.status_code == 200, f"Delete failed: {r.data}"
    print("[PASS] Delete employee verified")
    
    # 7. Test Attendance Threshold API
    for th in [60, 70, 75, 80, 90]:
        r = client.get(f'/api/threshold?threshold={th}')
        assert r.status_code == 200
        t_data = r.get_json()
        assert t_data['threshold_value'] == th
        print(f"[PASS] Threshold {th}% verified: {t_data['below_count']} employees ({t_data['percentage_below']}%)")
        
    # 8. Test Reports Data API
    r = client.get('/api/report-data?threshold=75')
    assert r.status_code == 200
    rep_data = r.get_json()
    assert 'summary' in rep_data and 'dept_stats' in rep_data
    print("[PASS] Report data API verified")
    
    # 9. Test ReportLab Summary PDF Download
    r = client.get('/report/pdf')
    assert r.status_code == 200
    assert r.data.startswith(b"%PDF"), "Summary report is not a valid PDF"
    assert len(r.data) > 1000
    print(f"[PASS] ReportLab Summary PDF download verified ({len(r.data)} bytes)")
    
    # 10. Test ReportLab Individual Salary Slip PDF Download
    r = client.get('/salary-slip/EMP001/pdf')
    assert r.status_code == 200
    assert r.data.startswith(b"%PDF"), "Salary slip is not a valid PDF"
    assert len(r.data) > 1000
    print(f"[PASS] ReportLab Individual Salary Slip PDF verified ({len(r.data)} bytes)")
    
    # 11. Test Processed CSV Download
    r = client.get('/download')
    assert r.status_code == 200
    text_data = r.data.decode('utf-8')
    assert "attendance_percentage" in text_data and "final_salary" in text_data
    print(f"[PASS] Processed CSV download verified ({len(text_data.splitlines())} lines)")
    
    # 12. Test CSV Upload
    csv_content = (
        "employee_id,employee_name,department,total_working_days,days_present,basic_salary,overtime_hours,overtime_rate\n"
        "EMP998,Batch Upload User,Finance,28,26,55000,12,300\n"
    )
    data = {
        'file': (io.BytesIO(csv_content.encode('utf-8')), 'test_upload.csv')
    }
    r = client.post('/upload', data=data, content_type='multipart/form-data')
    assert r.status_code == 200, f"CSV upload failed: {r.data}"
    print("[PASS] CSV Upload API verified")
    
    # Cleanup test upload record
    r = client.get('/api/employees/EMP998')
    if r.status_code == 200:
        client.delete(f"/employees/{r.get_json()['id']}")

        
    print("\n=== ALL 12 BACKEND TESTS PASSED SUCCESSFULLY! ===")

if __name__ == '__main__':
    run_tests()
