from datetime import datetime, date
import os
import sqlite3
from dateutil.relativedelta import relativedelta
import pandas as pd
import streamlit as st

# ==============================================================================
# DATABASE SETUP
# ==============================================================================

def init_db():
    conn = sqlite3.connect("employee_management.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            emp_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            dob TEXT,
            joining_date TEXT NOT NULL,
            doe TEXT,
            aadhar TEXT,
            pan TEXT,
            uan TEXT,
            department TEXT DEFAULT 'Engineering',
            designation TEXT DEFAULT 'Software Engineer',
            manager TEXT DEFAULT 'Meera Venkatesh',
            location TEXT DEFAULT 'New York',
            job_type TEXT DEFAULT 'Full-time',
            ctc REAL DEFAULT 0.0,
            salary REAL DEFAULT 0.0,
            cl_balance REAL DEFAULT 3.0,
            sl_balance REAL DEFAULT 3.0,
            pl_balance REAL DEFAULT 1.0,
            cycle_start TEXT NOT NULL,
            cycle_end TEXT NOT NULL
        )
    """)

    # Pre-fill sample data if table is empty (Matching your exact screenshot)
    cursor.execute("SELECT COUNT(*) FROM employees")
    if cursor.fetchone()[0] == 0:
        sample_employees = [
            ('4821', 'Aditya Ravi', '1992-05-10', '2020-05-10', 'Engineering', 'Lead Engineer', 'Meera Venkatesh', 'New York'),
            ('5732', 'Karan Rajesh', '1993-06-15', '2020-06-15', 'Product Design', 'Product Manager', 'Ritika Suresh', 'Los Angeles'),
            ('6943', 'Nikhil Pradeep', '1994-07-20', '2020-07-20', 'Marketing', 'Brand Strategist', 'Sonal Hari', 'San Francisco'),
            ('7054', 'Raghav Mohan', '1991-08-25', '2020-08-25', 'Operations', 'Human Resources..', 'Isha Kumar', 'Chicago'),
            ('8165', 'Dhruv Anil', '1989-09-30', '2020-09-30', 'Finance', 'Chief Financial Off..', 'Lalita Ramesh', 'Miami'),
            ('9276', 'Vivek Shankar', '1996-10-05', '2020-10-05', 'Academy', 'Intern', 'Ananya Manoj', 'Houston'),
            ('0387', 'Siddharth Arun', '1993-05-10', '2020-05-10', 'Engineering', 'Engineer', 'Tara Vijay', 'New York'),
            ('1498', 'Rohan Naveen', '1994-06-15', '2020-06-15', 'Product Design', 'UI Designer', 'Simran Karthik', 'Los Angeles'),
            ('2509', 'Aarav Nitin', '1995-07-20', '2020-07-20', 'Marketing', 'Digital Marketing..', 'Naina Ashok', 'San Francisco'),
            ('3610', 'Kabir Raghav', '1992-08-25', '2020-08-25', 'Operations', 'Administration', 'Sanya Ajay', 'Chicago'),
            ('4721', 'Arnav Sandeep', '1990-09-30', '2020-09-30', 'Finance', 'Financial Controller', 'Maya Deepak', 'Miami'),
            ('5832', 'Rajat Vishal', '1997-10-05', '2020-10-05', 'Academy', 'Intern', 'Diya Sanjay', 'Houston'),
        ]
        for emp in sample_employees:
            cursor.execute("""
                INSERT INTO employees (emp_id, name, dob, joining_date, department, designation, manager, location, cycle_start, cycle_end)
                VALUES (?, ?, '1995-01-01', ?, ?, ?, ?, ?, '2020-01-01', '2020-07-01')
            """, emp)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT,
            item_name TEXT,
            serial_number TEXT,
            assigned_date TEXT,
            FOREIGN KEY (emp_id) REFERENCES employees (emp_id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT,
            doc_name TEXT,
            file_path TEXT,
            upload_date TEXT,
            FOREIGN KEY (emp_id) REFERENCES employees (emp_id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()

def get_connection():
    conn = sqlite3.connect("employee_management.db")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def format_days(val):
    try:
        f_val = float(val)
        return f"{int(f_val)} DAYS" if f_val.is_integer() else f"{f_val} DAYS"
    except:
        return "0 DAYS"

def format_date_display(date_str):
    if not date_str or date_str in ["N/A", "ACTIVE", "None", ""]:
        return date_str
    try:
        return datetime.strptime(str(date_str), "%Y-%m-%d").strftime("%Y-%m-%d")
    except:
        return str(date_str)

def delete_employee(emp_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM inventory WHERE emp_id = ?", (emp_id,))
    cursor.execute("DELETE FROM documents WHERE emp_id = ?", (emp_id,))
    cursor.execute("DELETE FROM employees WHERE emp_id = ?", (emp_id,))
    conn.commit()
    conn.close()

STANDARD_DEPTS = ["Engineering", "Product Design", "Marketing", "Operations", "Finance", "Academy"]
STANDARD_LOCATIONS = ["New York", "Los Angeles", "San Francisco", "Chicago", "Miami", "Houston"]

DEPT_COLORS = {
    "Engineering": "#7C3AED",     # Purple
    "Product Design": "#2563EB",  # Blue
    "Marketing": "#D97706",       # Yellow/Orange
    "Operations": "#059669",      # Green
    "Finance": "#DC2626",         # Red
    "Academy": "#10B981"          # Light Green
}

# ==============================================================================
# UI CONFIGURATION & STYLING (EXACT SCREENSHOT MATCHING)
# ==============================================================================

st.set_page_config(
    page_title="Happy HR",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_db()

st.markdown("""
    <style>
    /* Global App Background */
    .stApp {
        background-color: #FAFAFA !important;
    }
    
    /* Hide Default Streamlit Elements */
    #MainMenu, header, footer {visibility: hidden;}
    
    /* Left Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0B192C !important;
        padding-top: 0.5rem !important;
    }
    [data-testid="stSidebar"] * {
        color: #94A3B8 !important;
    }
    
    /* Sidebar Headers */
    .sidebar-section-label {
        font-size: 11px;
        font-weight: 600;
        color: #64748B !important;
        margin-top: 15px;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Top Bar Search and Icons */
    .top-navbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background-color: #0B192C;
        padding: 8px 20px;
        margin-top: -60px;
        margin-left: -5rem;
        margin-right: -5rem;
        margin-bottom: 20px;
    }
    
    /* Custom Navigation Tabs */
    .stButton > button {
        border-radius: 6px !important;
        font-weight: 500 !important;
        font-size: 13.5px !important;
    }
    
    /* Primary Action Buttons */
    div.stButton > button[kind="primary"] {
        background-color: #0284C7 !important;
        color: white !important;
        border: none !important;
    }
    
    /* Dot Badge for Departments */
    .dept-dot {
        height: 8px;
        width: 8px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
    }
    
    /* Table Headers */
    .th-cell {
        font-size: 12.5px;
        font-weight: 600;
        color: #374151;
        padding: 6px 0px;
    }
    
    /* Custom Input Fields */
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border-radius: 6px !important;
        border: 1px solid #E5E7EB !important;
        font-size: 13px !important;
    }
    
    /* Pagination Styling */
    .pagination-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 25px;
        font-size: 13px;
        color: #6B7280;
    }
    .page-num {
        padding: 5px 10px;
        border-radius: 4px;
        margin: 0 2px;
        cursor: pointer;
    }
    .page-active {
        background-color: #0284C7;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize Session States
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "Manage Employees"
if "sidebar_menu" not in st.session_state:
    st.session_state["sidebar_menu"] = "Employees"

# ==============================================================================
# SIDEBAR NAVIGATION (HAPPY HR)
# ==============================================================================
with st.sidebar:
    st.markdown("<h3 style='color:#38BDF8 !important; margin-bottom:20px; font-weight:700;'>✨ Happy HR</h3>", unsafe_allow_html=True)
    
    st.markdown("<div class='sidebar-section-label'>MAIN MENU</div>", unsafe_allow_html=True)
    
    menu_items = [
        ("📊", "Dashboard"),
        ("👥", "Employees"),
        ("💼", "Recruitments"),
        ("💵", "Payrolls"),
        ("🎓", "Trainings"),
        ("🛡️", "Policies")
    ]
    
    for icon, label in menu_items:
        is_selected = st.session_state["sidebar_menu"] == label
        btn_type = "primary" if is_selected else "secondary"
        if st.button(f"{icon}  {label}", key=f"side_{label}", type=btn_type, use_container_width=True):
            st.session_state["sidebar_menu"] = label
            st.rerun()

    st.markdown("<div class='sidebar-section-label'>TEAMS</div>", unsafe_allow_html=True)
    for team, color in DEPT_COLORS.items():
        st.markdown(f"<p style='font-size:13px; margin-bottom:8px;'><span class='dept-dot' style='background-color:{color};'></span> {team}</p>", unsafe_allow_html=True)

    st.write("---")
    st.markdown("<p style='font-size:12px; color:#64748B;'>🦉 Owl Solutions ⚙️</p>", unsafe_allow_html=True)

# ==============================================================================
# MAIN CONTENT AREA
# ==============================================================================

# Top Navigation Bar (Header)
t_search, t_space, t_bell, t_user = st.columns([4, 4, 0.5, 0.5])
t_search.text_input("TopSearch", placeholder="🔍 Search Employees, Policies... (⌘K)", label_visibility="collapsed")
t_bell.markdown("<h3 style='margin:0; text-align:right;'>🔔</h3>", unsafe_allow_html=True)
t_user.markdown("<h3 style='margin:0; text-align:right;'>👨‍💼</h3>", unsafe_allow_html=True)

st.write(" ")

# Page Title & Header Actions
title_col, export_col, add_col = st.columns([5, 1.2, 1.5])

with title_col:
    st.markdown("<h2 style='margin:0; color:#111827; font-weight:700;'>Employees</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#6B7280; font-size:14px; margin-top:2px;'>Manage and view the complete list of employees within the organization.</p>", unsafe_allow_html=True)

conn = get_connection()
df_all_emp = pd.read_sql_query("SELECT * FROM employees", conn)
conn.close()

with export_col:
    if not df_all_emp.empty:
        file_name = "Employees_Export.xlsx"
        with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
            df_all_emp.to_excel(writer, sheet_name='EMPLOYEES', index=False)
        with open(file_name, "rb") as f:
            st.download_button("⬆ Export", f, file_name=file_name, use_container_width=True)

with add_col:
    if st.button("+ Add Employee", type="primary", use_container_width=True):
        st.session_state["show_add_modal"] = True

st.write(" ")

# Sub Navigation Tabs (Manage Employees, Org Chart, Leave Requests)
tab_col1, tab_col2, tab_col3, _ = st.columns([1.5, 1.5, 1.5, 4.5])

if tab_col1.button("👤 Manage Employees", type="primary" if st.session_state["active_tab"] == "Manage Employees" else "secondary", use_container_width=True):
    st.session_state["active_tab"] = "Manage Employees"
    st.rerun()

if tab_col2.button("🌿 Organisation Chart", type="primary" if st.session_state["active_tab"] == "Organisation Chart" else "secondary", use_container_width=True):
    st.session_state["active_tab"] = "Organisation Chart"
    st.rerun()

if tab_col3.button("📅 Leave Requests", type="primary" if st.session_state["active_tab"] == "Leave Requests" else "secondary", use_container_width=True):
    st.session_state["active_tab"] = "Leave Requests"
    st.rerun()

st.write(" ")

# ==============================================================================
# TAB 1: MANAGE EMPLOYEES VIEW
# ==============================================================================
if st.session_state["active_tab"] == "Manage Employees":

    # EXACT FILTERS BAR (Matching Screenshot)
    f1, f2, f3, f4, f5, f6, f7, f8 = st.columns([1.2, 1.2, 1.2, 1.3, 1.1, 1.1, 1, 2.5])

    sel_dept = f1.selectbox("Dept", ["Department"] + STANDARD_DEPTS, label_visibility="collapsed")
    sel_job = f2.selectbox("Job", ["Job Title"] + sorted(list(set(df_all_emp["designation"].dropna().tolist()))), label_visibility="collapsed")
    sel_mgr = f3.selectbox("Mgr", ["Manager"] + sorted(list(set(df_all_emp["manager"].dropna().tolist()))), label_visibility="collapsed")
    sel_doj = f4.selectbox("DOJ", ["Date of Joining"], label_visibility="collapsed")
    sel_type = f5.selectbox("Type", ["Job Type", "Full-time", "Contract", "Intern"], label_visibility="collapsed")
    sel_loc = f6.selectbox("Loc", ["Location"] + STANDARD_LOCATIONS, label_visibility="collapsed")

    if f7.button("Clear Filters"):
        st.rerun()

    search_query = f8.text_input("TableSearch", placeholder="🔍 Search Employees by Name, ID..", label_visibility="collapsed")

    # Filter Application Logic
    filtered_df = df_all_emp.copy()
    if sel_dept != "Department":
        filtered_df = filtered_df[filtered_df["department"] == sel_dept]
    if sel_job != "Job Title":
        filtered_df = filtered_df[filtered_df["designation"] == sel_job]
    if sel_mgr != "Manager":
        filtered_df = filtered_df[filtered_df["manager"] == sel_mgr]
    if sel_loc != "Location":
        filtered_df = filtered_df[filtered_df["location"] == sel_loc]
    if search_query:
        filtered_df = filtered_df[
            filtered_df["name"].str.contains(search_query, case=False, na=False) |
            filtered_df["emp_id"].str.contains(search_query, case=False, na=False)
        ]

    st.write(" ")

    # TABLE HEADER (SAME TO SAME)
    h_chk, h_id, h_name, h_dept, h_desg, h_mgr, h_doj, h_loc, h_act = st.columns([0.4, 1, 2, 1.8, 2, 1.8, 1.5, 1.5, 1.2])
    
    h_chk.write("☐")
    h_id.markdown("<div class='th-cell'>Emp ID ⇅</div>", unsafe_allow_html=True)
    h_name.markdown("<div class='th-cell'>Employee Name</div>", unsafe_allow_html=True)
    h_dept.markdown("<div class='th-cell'>Department</div>", unsafe_allow_html=True)
    h_desg.markdown("<div class='th-cell'>Job Title</div>", unsafe_allow_html=True)
    h_mgr.markdown("<div class='th-cell'>Manager</div>", unsafe_allow_html=True)
    h_doj.markdown("<div class='th-cell'>Date of Joining ⇅</div>", unsafe_allow_html=True)
    h_loc.markdown("<div class='th-cell'>Location</div>", unsafe_allow_html=True)
    h_act.markdown("<div class='th-cell'></div>", unsafe_allow_html=True)

    st.markdown("<hr style='margin:2px 0px 8px 0px; border-top:1px solid #E5E7EB;'>", unsafe_allow_html=True)

    # TABLE ROWS DATA
    for _, row in filtered_df.iterrows():
        emp_id = str(row["emp_id"])
        name = str(row["name"])
        dept = str(row["department"])
        desg = str(row["designation"])
        mgr = str(row.get("manager", "N/A"))
        doj = format_date_display(row["joining_date"])
        loc = str(row.get("location", "New York"))
        
        dot_color = DEPT_COLORS.get(dept, "#6B7280")

        c_chk, c_id, c_name, c_dept, c_desg, c_mgr, c_doj, c_loc, c_act = st.columns([0.4, 1, 2, 1.8, 2, 1.8, 1.5, 1.5, 1.2])

        c_chk.checkbox("", key=f"chk_{emp_id}", label_visibility="collapsed")
        c_id.write(f"{emp_id}")
        c_name.write(f"**{name}**")
        c_dept.markdown(f"<span class='dept-dot' style='background-color:{dot_color};'></span> {dept}", unsafe_allow_html=True)
        c_desg.write(f"{desg}")
        c_mgr.write(f"{mgr}")
        c_doj.write(f"{doj}")
        c_loc.write(f"{loc}")

        a1, a2, a3 = c_act.columns(3)
        if a1.button("👁️", key=f"v_{emp_id}", help="View Profile"):
            st.session_state["view_id"] = emp_id
        if a2.button("🌿", key=f"o_{emp_id}", help="Org Chart"):
            st.session_state["active_tab"] = "Organisation Chart"
            st.rerun()
        if a3.button("⋮", key=f"m_{emp_id}", help="Options"):
            st.session_state["edit_id"] = emp_id

        st.markdown("<hr style='margin:0px; border-top:1px solid #F3F4F6;'>", unsafe_allow_html=True)

    # FOOTER PAGINATION BAR (MATCHING SCREENSHOT)
    st.markdown("""
        <div class='pagination-container'>
            <div>10 of 2000 row(s) selected.</div>
            <div>
                <span>&lt; Previous</span>
                <span class='page-num page-active'>1</span>
                <span class='page-num'>2</span>
                <span class='page-num'>3</span>
                <span>...</span>
                <span class='page-num'>200</span>
                <span>Next &gt;</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# TAB 2 & 3 VIEWS
# ==============================================================================
elif st.session_state["active_tab"] == "Organisation Chart":
    st.markdown("### 🌿 Organisation Chart View")
    st.info("Interactive Hierarchy View loaded.")

elif st.session_state["active_tab"] == "Leave Requests":
    st.markdown("### 📅 Leave Requests Portal")
    st.info("Manage Employee Leave Balances and Approvals.")

# ==============================================================================
# MODALS & POPUPS (ADD / EDIT / VIEW / DELETE)
# ==============================================================================

if st.session_state.get("show_add_modal", False):
    with st.sidebar:
        st.markdown("### ➕ Register Employee")
        with st.form("add_e_form"):
            e_id = st.text_input("Emp ID *")
            e_name = st.text_input("Full Name *")
            e_dept = st.selectbox("Department", STANDARD_DEPTS)
            e_desg = st.text_input("Job Title", value="Software Engineer")
            e_mgr = st.text_input("Manager Name", value="Meera Venkatesh")
            e_loc = st.selectbox("Location", STANDARD_LOCATIONS)
            e_doj = st.date_input("Date of Joining", value=datetime.now().date())
            
            st.markdown("**Optional Asset Assignment**")
            e_inv = st.text_input("Inventory Item (e.g. Laptop)")
            e_ser = st.text_input("Serial No.")

            if st.form_submit_button("Save Employee", type="primary"):
                if e_id and e_name:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO employees (emp_id, name, dob, joining_date, department, designation, manager, location, cycle_start, cycle_end)
                        VALUES (?, ?, '1995-01-01', ?, ?, ?, ?, ?, ?, ?)
                    """, (e_id, e_name, e_doj.strftime("%Y-%m-%d"), e_dept, e_desg, e_mgr, e_loc, e_doj.strftime("%Y-%m-%d"), (e_doj + relativedelta(months=6)).strftime("%Y-%m-%d")))
                    
                    if e_inv:
                        cursor.execute("INSERT INTO inventory (emp_id, item_name, serial_number, assigned_date) VALUES (?, ?, ?, ?)",
                                       (e_id, e_inv, e_ser, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    conn.close()
                    st.success("Employee Saved!")
                    st.session_state["show_add_modal"] = False
                    st.rerun()

        if st.button("Close"):
            st.session_state["show_add_modal"] = False
            st.rerun()

if "edit_id" in st.session_state:
    ed_id = st.session_state["edit_id"]
    conn = get_connection()
    rec = pd.read_sql_query(f"SELECT * FROM employees WHERE emp_id='{ed_id}'", conn).iloc[0]
    conn.close()

    st.markdown(f"### ✏️ Edit Employee: {rec['name']} ({rec['emp_id']})")
    with st.form("edit_f"):
        u_name = st.text_input("Name", value=rec['name'])
        u_dept = st.selectbox("Department", STANDARD_DEPTS, index=STANDARD_DEPTS.index(rec['department']) if rec['department'] in STANDARD_DEPTS else 0)
        u_desg = st.text_input("Job Title", value=rec['designation'])
        u_mgr = st.text_input("Manager", value=rec['manager'])
        u_loc = st.selectbox("Location", STANDARD_LOCATIONS, index=STANDARD_LOCATIONS.index(rec['location']) if rec['location'] in STANDARD_LOCATIONS else 0)

        if st.form_submit_button("Save Changes", type="primary"):
            conn = get_connection()
            conn.execute("UPDATE employees SET name=?, department=?, designation=?, manager=?, location=? WHERE emp_id=?", 
                         (u_name, u_dept, u_desg, u_mgr, u_loc, ed_id))
            conn.commit()
            conn.close()
            del st.session_state["edit_id"]
            st.success("Updated!")
            st.rerun()

    c_d1, c_d2 = st.columns(2)
    if c_d1.button("🗑️ Delete Employee", type="primary"):
        delete_employee(ed_id)
        del st.session_state["edit_id"]
        st.success("Employee Deleted!")
        st.rerun()
    if c_d2.button("Close Modal"):
        del st.session_state["edit_id"]
        st.rerun()
