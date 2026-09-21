import os
import random
import sqlite3
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'sample_employees.csv')

MALE_FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan",
    "Shaurya", "Atharva", "Advik", "Pranav", "Advaith", "Aaryan", "Dhruv", "Kabir", "Rohan", "Vikram",
    "Karan", "Rahul", "Siddharth", "Varun", "Manish", "Nikhil", "Gaurav", "Anand", "Rajesh", "Amit",
    "Suresh", "Ramesh", "Deepak", "Sanjay", "Alok", "Dev", "Harsh", "Kunal", "Mohit", "Tarun",
    "Abhishek", "Ashwin", "Bhavesh", "Chirag", "Dinesh", "Girish", "Hemant", "Jatin", "Kailash", "Lalit",
    "Manoj", "Naveen", "Omkar", "Pankaj", "Ravi", "Sachin", "Tushar", "Umesh", "Vinay", "Yash"
]

FEMALE_FIRST_NAMES = [
    "Saanvi", "Aanya", "Aadhya", "Aarohi", "Ananya", "Pari", "Anika", "Navya", "Angel", "Diya",
    "Myra", "Sara", "Ira", "Ahana", "Riya", "Prisha", "Isha", "Anvi", "Riddhi", "Sia",
    "Pooja", "Neha", "Sneha", "Kavya", "Priya", "Divya", "Meera", "Swati", "Shreya", "Tanvi",
    "Aditi", "Anushka", "Bhavna", "Chaitali", "Deepika", "Garima", "Harini", "Ishita", "Jyoti", "Komal",
    "Lavanya", "Madhavi", "Nandini", "Pallavi", "Radhika", "Simran", "Trisha", "Urvi", "Vandana", "Yamini",
    "Shruti", "Akanksha", "Chhavi", "Disha", "Ekta", "Geetanjali", "Kalyani", "Mitali", "Payal", "Rupal"
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Malhotra", "Bhatia", "Saxena", "Mehta", "Chopra", "Kapoor", "Patel",
    "Shah", "Joshi", "Deshmukh", "Kulkarni", "Patil", "Pawar", "Shinde", "Iyer", "Iyengar", "Nair",
    "Menon", "Pillai", "Reddy", "Rao", "Naidu", "Chowdhury", "Mukherjee", "Banerjee", "Chatterjee", "Ghosh",
    "Das", "Sen", "Bose", "Dutta", "Singh", "Kaur", "Gill", "Sandhu", "Dhillon", "Grewal",
    "Agarwal", "Bansal", "Mittal", "Goyal", "Singhal", "Jain", "Maheshwari", "Trivedi", "Pandey", "Mishra",
    "Tripathi", "Dubey", "Tiwari", "Shukla", "Pandit", "Rathore", "Chauhan", "Solanki", "Parmar", "Yadav"
]

DEPARTMENTS = ["IT", "HR", "Finance", "Sales", "Marketing", "Operations", "Support"]

def generate_employees_data():
    random.seed(42)  # For consistent and realistic distribution
    employees = []
    
    # We need 500 employees: EMP001 to EMP500
    # At least 50 should have attendance below 75%
    below_threshold_indices = set(random.sample(range(1, 501), 75)) # 75 employees below 75%
    
    for i in range(1, 501):
        emp_id = f"EMP{i:03d}"
        
        # Gender 50/50
        if random.random() < 0.5:
            first_name = random.choice(MALE_FIRST_NAMES)
        else:
            first_name = random.choice(FEMALE_FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        full_name = f"{first_name} {last_name}"
        
        dept = random.choice(DEPARTMENTS)
        working_days = random.randint(24, 31)
        
        if i in below_threshold_indices:
            # Below 75% attendance -> days_present < working_days * 0.75
            max_present = int(working_days * 0.74)
            min_present = max(15, int(working_days * 0.50))
            if min_present > max_present:
                min_present = max(10, max_present - 3)
            days_present = random.randint(min_present, max_present)
        else:
            # Above or equal to 75%
            min_present = int(working_days * 0.75) + 1
            if min_present > working_days:
                min_present = working_days
            days_present = random.randint(min_present, working_days)
            
        # Basic Salary: ₹20,000 to ₹80,000 (rounded to hundreds)
        basic_salary = round(random.randint(200, 800) * 100, 2)
        
        # Overtime hours: 0 to 40
        # 30% chance of 0 OT, otherwise 1-40
        if random.random() < 0.3:
            ot_hours = 0.0
        else:
            ot_hours = round(random.uniform(2.0, 40.0), 1)
            
        # Overtime rate: ₹150 to ₹500 (multiples of 25)
        ot_rate = float(random.choice(range(150, 525, 25)))
        
        employees.append({
            'employee_id': emp_id,
            'employee_name': full_name,
            'department': dept,
            'total_working_days': working_days,
            'days_present': days_present,
            'basic_salary': basic_salary,
            'overtime_hours': ot_hours,
            'overtime_rate': ot_rate
        })
        
    return employees

def init_database(force=False):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE NOT NULL,
            employee_name TEXT NOT NULL,
            department TEXT NOT NULL,
            total_working_days INTEGER NOT NULL,
            days_present INTEGER NOT NULL,
            basic_salary REAL NOT NULL,
            overtime_hours REAL NOT NULL,
            overtime_rate REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('SELECT COUNT(*) FROM employees')
    count = cursor.fetchone()[0]
    
    if count < 500 or force:
        if force:
            cursor.execute('DELETE FROM employees')
            
        data = generate_employees_data()
        
        cursor.executemany('''
            INSERT OR REPLACE INTO employees 
            (employee_id, employee_name, department, total_working_days, days_present, basic_salary, overtime_hours, overtime_rate)
            VALUES (:employee_id, :employee_name, :department, :total_working_days, :days_present, :basic_salary, :overtime_hours, :overtime_rate)
        ''', data)
        
        conn.commit()
        print(f"Database initialized with {len(data)} employee records.")
        
        # Also create sample CSV
        df = pd.DataFrame(data)
        df.to_csv(CSV_PATH, index=False)
        print(f"Sample CSV saved to {CSV_PATH}")
    else:
        print(f"Database already contains {count} employees.")
        
    conn.close()

if __name__ == '__main__':
    init_database(force=True)
