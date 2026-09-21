import io
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

PRIMARY_COLOR = colors.HexColor("#1E3A8A")     # Deep Navy
SECONDARY_COLOR = colors.HexColor("#3B82F6")   # Royal Blue
LIGHT_BG = colors.HexColor("#F1F5F9")          # Slate 100
HEADER_BG = colors.HexColor("#DBEAFE")         # Soft Blue
TEXT_DARK = colors.HexColor("#0F172A")         # Slate 900
TEXT_MUTED = colors.HexColor("#64748B")        # Slate 500
SUCCESS_COLOR = colors.HexColor("#10B981")     # Emerald
WARNING_COLOR = colors.HexColor("#F59E0B")     # Amber
DANGER_COLOR = colors.HexColor("#EF4444")      # Rose

class NumberedCanvas(canvas.Canvas):
    """Adds 'Page X of Y' and confidential footer to all pages"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(TEXT_MUTED)
        
        # Header banner line
        self.setStrokeColor(PRIMARY_COLOR)
        self.setLineWidth(1)
        self.line(40, letter[1] - 40, letter[0] - 40, letter[1] - 40)
        self.drawString(40, letter[1] - 35, "EMS CORPORATE PAYROLL & ATTENDANCE SYSTEM — OFFICIAL REPORT")
        self.drawRightString(letter[0] - 40, letter[1] - 35, datetime.now().strftime("%d %b %Y, %I:%M %p"))

        # Footer
        self.line(40, 45, letter[0] - 40, 45)
        self.drawString(40, 32, "Confidential — For Internal HR & Payroll Management Only")
        self.drawRightString(letter[0] - 40, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def generate_summary_pdf(summary_data, dept_stats, threshold_val=75):
    """
    Generates an executive-level attendance and salary summary report PDF.
    Returns bytes buffer.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=55,
        bottomMargin=55
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=PRIMARY_COLOR,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=TEXT_MUTED,
        spaceAfter=15
    )
    
    section_heading = ParagraphStyle(
        'SecHead',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=PRIMARY_COLOR,
        spaceBefore=14,
        spaceAfter=8
    )
    
    cell_style = ParagraphStyle(
        'Cell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=TEXT_DARK
    )
    
    cell_bold = ParagraphStyle(
        'CellBold',
        parent=cell_style,
        fontName='Helvetica-Bold'
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph("Executive HR & Payroll Summary Report", title_style))
    story.append(Paragraph(
        f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | Attendance Benchmark Threshold: <b>{threshold_val}%</b>",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY_COLOR, spaceAfter=12))

    # KPI Summary Cards Table (2 rows x 4 cols)
    story.append(Paragraph("Key Performance & Payroll Indicators", section_heading))
    
    kpi_data = [
        [
            Paragraph("<b>Total Workforce</b><br/><font size=14 color='#1E3A8A'><b>" + str(summary_data['total_employees']) + "</b></font>", cell_style),
            Paragraph("<b>Average Attendance</b><br/><font size=14 color='#10B981'><b>" + f"{summary_data['avg_attendance']:.1f}%" + "</b></font>", cell_style),
            Paragraph("<b>Below Threshold (<" + str(threshold_val) + "%)</b><br/><font size=14 color='#EF4444'><b>" + str(summary_data['below_threshold_count']) + "</b></font>", cell_style),
            Paragraph("<b>Total Overtime Hours</b><br/><font size=14 color='#3B82F6'><b>" + f"{summary_data['total_ot_hours']:.1f} hrs" + "</b></font>", cell_style)
        ],
        [
            Paragraph("<b>Highest Attendance</b><br/><font size=11 color='#1E3A8A'><b>" + f"{summary_data['max_attendance']:.1f}% ({summary_data['max_att_emp']})" + "</b></font>", cell_style),
            Paragraph("<b>Lowest Attendance</b><br/><font size=11 color='#EF4444'><b>" + f"{summary_data['min_attendance']:.1f}% ({summary_data['min_att_emp']})" + "</b></font>", cell_style),
            Paragraph("<b>Total Overtime Pay</b><br/><font size=13 color='#1E3A8A'><b>₹" + f"{summary_data['total_ot_pay']:,.2f}" + "</b></font>", cell_style),
            Paragraph("<b>Total Salary Expense</b><br/><font size=13 color='#1E3A8A'><b>₹" + f"{summary_data['total_salary_expense']:,.2f}" + "</b></font>", cell_style)
        ]
    ]
    
    kpi_table = Table(kpi_data, colWidths=[130, 130, 130, 142])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 14))

    # Department-wise Breakdown Table
    story.append(Paragraph("Departmental Attendance & Financial Breakdown", section_heading))
    
    dept_table_data = [[
        Paragraph("<b>Department</b>", cell_bold),
        Paragraph("<b>Headcount</b>", cell_bold),
        Paragraph("<b>Avg Attendance</b>", cell_bold),
        Paragraph("<b>Total Basic Pay</b>", cell_bold),
        Paragraph("<b>Total OT Pay</b>", cell_bold),
        Paragraph("<b>Total Final Salary</b>", cell_bold)
    ]]
    
    for row in dept_stats:
        dept_table_data.append([
            Paragraph(str(row['department']), cell_style),
            Paragraph(str(row['count']), cell_style),
            Paragraph(f"{row['avg_attendance']:.1f}%", cell_style),
            Paragraph(f"₹{row['total_basic']:,.2f}", cell_style),
            Paragraph(f"₹{row['total_ot']:,.2f}", cell_style),
            Paragraph(f"₹{row['total_final']:,.2f}", cell_bold)
        ])
        
    # Totals row
    dept_table_data.append([
        Paragraph("<b>Grand Total</b>", cell_bold),
        Paragraph(f"<b>{summary_data['total_employees']}</b>", cell_bold),
        Paragraph(f"<b>{summary_data['avg_attendance']:.1f}%</b>", cell_bold),
        Paragraph(f"<b>₹{summary_data['total_basic_expense']:,.2f}</b>", cell_bold),
        Paragraph(f"<b>₹{summary_data['total_ot_pay']:,.2f}</b>", cell_bold),
        Paragraph(f"<b>₹{summary_data['total_salary_expense']:,.2f}</b>", cell_bold)
    ])
    
    col_widths = [100, 65, 85, 95, 85, 102]
    dept_table = Table(dept_table_data, colWidths=col_widths)
    dept_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, PRIMARY_COLOR),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E0E7FF')),
        ('TOPPADDING', (0, -1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F8FAFC')])
    ]))
    story.append(dept_table)
    story.append(Spacer(1, 14))

    # Threshold Compliance Summary
    story.append(Paragraph(f"Attendance Compliance Policy Summary (< {threshold_val}% Threshold)", section_heading))
    compliance_text = (
        f"A total of <b>{summary_data['below_threshold_count']} employees</b> ({((summary_data['below_threshold_count']/summary_data['total_employees'])*100):.1f}% of workforce) "
        f"are currently falling below the prescribed {threshold_val}% attendance benchmark. "
        f"HR departmental leads have been notified to review leave regularization and time sheets."
    )
    story.append(Paragraph(compliance_text, cell_style))
    story.append(Spacer(1, 15))

    # Sign-off box
    sign_data = [
        [
            Paragraph("<b>Prepared By:</b><br/>HR Payroll Administration<br/>System Generated", cell_style),
            Paragraph("<b>Reviewed & Approved By:</b><br/>Chief Financial Officer / HR Director<br/>___________________________", cell_style)
        ]
    ]
    sign_table = Table(sign_data, colWidths=[260, 272])
    sign_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('PADDING', (0, 0), (-1, -1), 8)
    ]))
    story.append(sign_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()


def generate_salary_slip_pdf(emp):
    """
    Generates a formal corporate salary slip PDF for an individual employee.
    Returns bytes buffer.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    company_name_style = ParagraphStyle(
        'CompName',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=PRIMARY_COLOR,
        alignment=1
    )
    
    company_sub_style = ParagraphStyle(
        'CompSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=TEXT_MUTED,
        alignment=1
    )
    
    title_slip_style = ParagraphStyle(
        'TitleSlip',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=PRIMARY_COLOR,
        alignment=1,
        spaceBefore=8,
        spaceAfter=8
    )
    
    cell_style = ParagraphStyle(
        'SlipCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=TEXT_DARK
    )
    
    cell_bold = ParagraphStyle(
        'SlipCellB',
        parent=cell_style,
        fontName='Helvetica-Bold'
    )
    
    story = []

    # Header
    story.append(Paragraph("ENTERPRISE GLOBAL SOLUTIONS PVT. LTD.", company_name_style))
    story.append(Paragraph("Corporate Tower 4, Cyber City, Sector 24, Gurugram, Haryana - 122002", company_sub_style))
    story.append(Paragraph("CIN: U72200HR2015PTC054812 | Email: payroll@enterpriseglobal.com", company_sub_style))
    story.append(Spacer(1, 6))
    
    # Pay Slip Banner
    month_year = datetime.now().strftime("%B %Y")
    slip_header_table = Table([[
        Paragraph(f"<b>PAYSLIP FOR THE MONTH OF {month_year.upper()}</b>", title_slip_style)
    ]], colWidths=[532])
    slip_header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HEADER_BG),
        ('BOX', (0, 0), (-1, -1), 1, PRIMARY_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(slip_header_table)
    story.append(Spacer(1, 8))

    # Employee Information Grid
    att_pct = (emp['days_present'] / emp['total_working_days']) * 100 if emp['total_working_days'] > 0 else 0
    status = "Excellent" if att_pct >= 90 else ("Good" if att_pct >= 75 else "Below Threshold")
    status_color = "#10B981" if att_pct >= 90 else ("#F59E0B" if att_pct >= 75 else "#EF4444")
    
    emp_info_data = [
        [
            Paragraph("<b>Employee ID:</b>", cell_bold),
            Paragraph(str(emp['employee_id']), cell_style),
            Paragraph("<b>Department:</b>", cell_bold),
            Paragraph(str(emp['department']), cell_style)
        ],
        [
            Paragraph("<b>Employee Name:</b>", cell_bold),
            Paragraph(str(emp['employee_name']), cell_style),
            Paragraph("<b>Pay Period:</b>", cell_bold),
            Paragraph(month_year, cell_style)
        ],
        [
            Paragraph("<b>Total Working Days:</b>", cell_bold),
            Paragraph(str(emp['total_working_days']), cell_style),
            Paragraph("<b>Days Present:</b>", cell_bold),
            Paragraph(str(emp['days_present']), cell_style)
        ],
        [
            Paragraph("<b>Attendance Rate:</b>", cell_bold),
            Paragraph(f"<b>{att_pct:.1f}%</b>", cell_style),
            Paragraph("<b>Attendance Status:</b>", cell_bold),
            Paragraph(f"<font color='{status_color}'><b>{status}</b></font>", cell_style)
        ]
    ]
    
    emp_table = Table(emp_info_data, colWidths=[120, 146, 120, 146])
    emp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(emp_table)
    story.append(Spacer(1, 10))

    # Salary Breakdown Table (Earnings vs Deductions)
    ot_pay = emp['overtime_hours'] * emp['overtime_rate']
    final_salary = emp['basic_salary'] + ot_pay

    salary_data = [
        [
            Paragraph("<b>EARNINGS</b>", cell_bold),
            Paragraph("<b>AMOUNT (₹)</b>", cell_bold),
            Paragraph("<b>DEDUCTIONS</b>", cell_bold),
            Paragraph("<b>AMOUNT (₹)</b>", cell_bold)
        ],
        [
            Paragraph("Basic Salary", cell_style),
            Paragraph(f"₹{emp['basic_salary']:,.2f}", cell_style),
            Paragraph("Provident Fund (PF)", cell_style),
            Paragraph("₹0.00", cell_style)
        ],
        [
            Paragraph(f"Overtime Pay ({emp['overtime_hours']:.1f} hrs @ ₹{emp['overtime_rate']:.0f}/hr)", cell_style),
            Paragraph(f"₹{ot_pay:,.2f}", cell_style),
            Paragraph("Professional Tax (PT)", cell_style),
            Paragraph("₹0.00", cell_style)
        ],
        [
            Paragraph("House Rent Allowance (HRA)", cell_style),
            Paragraph("Included in Basic", cell_style),
            Paragraph("Income Tax (TDS)", cell_style),
            Paragraph("₹0.00", cell_style)
        ],
        [
            Paragraph("Special Allowances", cell_style),
            Paragraph("₹0.00", cell_style),
            Paragraph("Other Deductions", cell_style),
            Paragraph("₹0.00", cell_style)
        ],
        [
            Paragraph("<b>Total Gross Earnings</b>", cell_bold),
            Paragraph(f"<b>₹{final_salary:,.2f}</b>", cell_bold),
            Paragraph("<b>Total Deductions</b>", cell_bold),
            Paragraph("<b>₹0.00</b>", cell_bold)
        ]
    ]

    salary_table = Table(salary_data, colWidths=[180, 86, 180, 86])
    salary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('LINEBELOW', (0, 0), (-1, 0), 1, PRIMARY_COLOR),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E0E7FF')),
    ]))
    story.append(salary_table)
    story.append(Spacer(1, 10))

    # Net Pay Summary Box
    net_box_data = [[
        Paragraph(
            f"<b>NET TAKE-HOME SALARY:</b> <font size=13 color='#1E3A8A'><b>₹{final_salary:,.2f}</b></font><br/>"
            f"<font size=8 color='#64748B'>Amount Credited directly to Registered Bank Account.</font>",
            cell_style
        )
    ]]
    net_box = Table(net_box_data, colWidths=[532])
    net_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ECFDF5')),
        ('BOX', (0, 0), (-1, -1), 1, SUCCESS_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(net_box)
    story.append(Spacer(1, 25))

    # Signature and Disclaimer
    sign_block = [
        [
            Paragraph("<b>Employee Signature:</b><br/><br/><br/>________________________", cell_style),
            Paragraph("<b>Authorized Signatory:</b><br/><br/><br/><b>EMS Payroll Accounts Officer</b>", cell_style)
        ]
    ]
    sign_table = Table(sign_block, colWidths=[266, 266])
    sign_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(sign_table)
    story.append(Spacer(1, 15))

    disclaimer = Paragraph(
        "<font size=7 color='#94A3B8'>Note: This document is a computer-generated salary statement from EMS Portal. "
        "It carries electronic validation and does not require a physical company stamp.</font>",
        cell_style
    )
    story.append(disclaimer)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
