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
            department TEXT DEFAULT 'DEVELOPMENT',
            designation TEXT DEFAULT 'SOFTWARE ENGINEER',
            manager TEXT DEFAULT 'N/A',
            location TEXT DEFAULT 'NEW DELHI',
            ctc REAL DEFAULT 0.0,
            salary REAL DEFAULT 0.0,
            cl_balance REAL DEFAULT 3.0,
            sl_balance REAL DEFAULT 3.0,
            pl_balance REAL DEFAULT 1.0,
            cycle_start TEXT NOT NULL,
            cycle_end TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT,
            item_name TEXT,
            serial_number TEXT,
            assigned_date TEXT,
            status TEXT DEFAULT 'ASSIGNED',
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
        if f_val.is_integer():
            return f"{int(f_val)} DAYS"
        return f"{f_val} DAYS"
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
    cursor.execute("SELECT file_path FROM documents WHERE emp_id = ?", (emp_id,))
    docs = cursor.fetchall()
    for doc in docs:
        if doc[0] and os.path.exists(doc[0]):
            try:
                os.remove(doc[0])
            except:
                pass

    cursor.execute("DELETE FROM inventory WHERE emp_id = ?", (emp_id,))
    cursor.execute("DELETE FROM documents WHERE emp_id = ?", (emp_id,))
    cursor.execute("DELETE FROM employees WHERE emp_id = ?", (emp_id,))
    conn.commit()
    conn.close()

STANDARD_DEPTS = ["HR", "FINANCE", "OPERATION", "MARKETING", "DESIGN", "DEVELOPMENT", "SALES"]

# ==============================================================================
# PAGE CONFIGURATION
# ==============================================================================

st.set_page_config(
    page_title="Employee Dashboard",
    page_icon="📊",
    layout="wide"
)

init_db()

# ==============================================================================
# HEADER SECTION
# ==============================================================================

st.title("📊 Employee Management Dashboard")
st.markdown("Manage employee records, department details, and system reports.")
st.write("---")

conn = get_connection()
df_all = pd.read_sql_query("SELECT * FROM employees", conn)
conn.close()

# Quick Stats / Metrics Bar
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("Total Employees", len(df_all))
col_m2.metric("Departments", len(df_all["department"].unique()) if not df_all.empty else 0)
col_m3.metric("Locations", len(df_all["location"].unique()) if not df_all.empty else 0)

with col_m4:
    if not df_all.empty:
        file_name = "Employee_Data.xlsx"
        with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
            df_all.to_excel(writer, sheet_name='EMPLOYEES', index=False)
        with open(file_name, "rb") as f:
            st.download_button("📥 Export to Excel", f, file_name=file_name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

st.write(" ")

# ==============================================================================
# ACTIONS & FILTERS
# ==============================================================================

btn_col, f1, f2, f3 = st.columns([1.5, 2, 2, 3])

with btn_col:
    if st.button("➕ Add New Employee", type="primary", use_container_width=True):
        st.session_state["show_add_modal"] = True

with f1:
    sel_dept = st.selectbox("Filter Department", ["All Departments"] + STANDARD_DEPTS)

with f2:
    all_desg = sorted(df_all["designation"].dropna().unique().tolist()) if not df_all.empty else []
    sel_desg = st.selectbox("Filter Job Title", ["All Job Titles"] + all_desg)

with f3:
    search_query = st.text_input("Search", placeholder="🔍 Search by Name or ID...")

# ==============================================================================
# DATA TABLE
# ==============================================================================

filtered_df = df_all.copy()

if not filtered_df.empty:
    if sel_dept != "All Departments":
        filtered_df = filtered_df[filtered_df["department"] == sel_dept]
    if sel_desg != "All Job Titles":
        filtered_df = filtered_df[filtered_df["designation"] == sel_desg]
    if search_query:
        filtered_df = filtered_df[
            filtered_df["name"].str.contains(search_query, case=False, na=False) |
            filtered_df["emp_id"].str.contains(search_query, case=False, na=False)
        ]

st.write(" ")

if filtered_df.empty:
    st.info("No employee records found.")
else:
    # Table Display
    display_cols = ["emp_id", "name", "department", "designation", "manager", "location", "joining_date"]
    
    # Rename for cleaner table headers
    renamed_df = filtered_df[display_cols].rename(columns={
        "emp_id": "Emp ID",
        "name": "Employee Name",
        "department": "Department",
        "designation": "Job Title",
        "manager": "Manager",
        "location": "Location",
        "joining_date": "Date of Joining"
    })
    
    st.dataframe(renamed_df, use_container_width=True, hide_index=True)

    # Action Selection
    st.write("### ⚙️ Quick Actions")
    act_col1, act_col2 = st.columns(2)
    
    selected_emp = act_col1.selectbox("Select Employee for Actions", filtered_df["emp_id"].tolist())
    
    a_btn1, a_btn2, a_btn3 = act_col2.columns(3)
    if a_btn1.button("👁️ View Profile", use_container_width=True):
        st.session_state["view_id"] = selected_emp
    if a_btn2.button("✏️ Edit Details", use_container_width=True):
        st.session_state["edit_id"] = selected_emp
    if a_btn3.button("🗑️ Delete Record", use_container_width=True):
        st.session_state["del_id"] = selected_emp

# ==============================================================================
# MODALS & FORMS
# ==============================================================================

# ADD EMPLOYEE
if st.session_state.get("show_add_modal", False):
    st.write("---")
    st.markdown("### ➕ Register Employee")
    with st.form("add_form"):
        e_id = st.text_input("Emp ID *")
        e_name = st.text_input("Full Name *")
        e_dept = st.selectbox("Department", STANDARD_DEPTS)
        e_desg = st.text_input("Designation", value="Software Engineer")
        e_mgr = st.text_input("Manager Name", value="Aditya Ravi")
        e_loc = st.text_input("Location", value="NEW DELHI")
        e_doj = st.date_input("Date of Joining", value=datetime.now().date())

        c1, c2 = st.columns(2)
        submit = c1.form_submit_button("Save Employee", type="primary")
        cancel = c2.form_submit_button("Cancel")

        if submit:
            if e_id and e_name:
                conn = get_connection()
                conn.execute("""
                    INSERT INTO employees (emp_id, name, dob, joining_date, department, designation, manager, location, cycle_start, cycle_end)
                    VALUES (?, ?, '1995-01-01', ?, ?, ?, ?, ?, ?, ?)
                """, (e_id, e_name, e_doj.strftime("%Y-%m-%d"), e_dept, e_desg, e_mgr, e_loc, e_doj.strftime("%Y-%m-%d"), (e_doj + relativedelta(months=6)).strftime("%Y-%m-%d")))
                conn.commit()
                conn.close()
                st.session_state["show_add_modal"] = False
                st.success("Employee Added!")
                st.rerun()
            else:
                st.error("Please fill required fields.")
        if cancel:
            st.session_state["show_add_modal"] = False
            st.rerun()

# VIEW PROFILE
if "view_id" in st.session_state:
    v_id = st.session_state["view_id"]
    conn = get_connection()
    v_emp = pd.read_sql_query(f"SELECT * FROM employees WHERE emp_id='{v_id}'", conn).iloc[0]
    conn.close()

    st.write("---")
    st.markdown(f"### 👤 Profile Details: {v_emp['name']} ({v_emp['emp_id']})")
    p1, p2, p3 = st.columns(3)
    p1.write(f"**Department:** {v_emp['department']}")
    p2.write(f"**Job Title:** {v_emp['designation']}")
    p3.write(f"**Manager:** {v_emp['manager']}")
    
    p1.write(f"**Location:** {v_emp['location']}")
    p2.write(f"**Date of Joining:** {v_emp['joining_date']}")
    p3.write(f"**Leave Balance:** CL: {v_emp['cl_balance']} | SL: {v_emp['sl_balance']} | PL: {v_emp['pl_balance']}")

    if st.button("Close View"):
        del st.session_state["view_id"]
        st.rerun()

# EDIT DETAILS
if "edit_id" in st.session_state:
    ed_id = st.session_state["edit_id"]
    conn = get_connection()
    rec = pd.read_sql_query(f"SELECT * FROM employees WHERE emp_id='{ed_id}'", conn).iloc[0]
    conn.close()

    st.write("---")
    st.markdown(f"### ✏️ Edit Employee: {rec['name']}")
    with st.form("edit_form"):
        u_name = st.text_input("Name", value=rec['name'])
        u_dept = st.selectbox("Department", STANDARD_DEPTS, index=STANDARD_DEPTS.index(rec['department']) if rec['department'] in STANDARD_DEPTS else 0)
        u_desg = st.text_input("Designation", value=rec['designation'])
        u_mgr = st.text_input("Manager", value=rec['manager'])
        u_loc = st.text_input("Location", value=rec['location'])

        if st.form_submit_button("Update Details", type="primary"):
            conn = get_connection()
            conn.execute("UPDATE employees SET name=?, department=?, designation=?, manager=?, location=? WHERE emp_id=?", 
                         (u_name, u_dept, u_desg, u_mgr, u_loc, ed_id))
            conn.commit()
            conn.close()
            del st.session_state["edit_id"]
            st.success("Updated Successfully!")
            st.rerun()

    if st.button("Cancel Edit"):
        del st.session_state["edit_id"]
        st.rerun()

# DELETE RECORD
if "del_id" in st.session_state:
    d_id = st.session_state["del_id"]
    st.warning(f"Are you sure you want to delete Employee ID: {d_id}?")
    col_d1, col_d2 = st.columns(2)
    if col_d1.button("Yes, Delete Record", type="primary"):
        delete_employee(d_id)
        del st.session_state["del_id"]
        st.success("Record Deleted!")
        st.rerun()
    if col_d2.button("Cancel"):
        del st.session_state["del_id"]
        st.rerun()
