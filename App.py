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

    cursor.execute("PRAGMA table_info(employees)")
    columns = [column[1] for column in cursor.fetchall()]

    new_cols = {
        "manager": "TEXT DEFAULT 'N/A'",
        "location": "TEXT DEFAULT 'NEW DELHI'"
    }
    for col, col_type in new_cols.items():
        if col not in columns:
            cursor.execute(f"ALTER TABLE employees ADD COLUMN {col} {col_type}")

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

def parse_date_input(d_input):
    if isinstance(d_input, (date, datetime)):
        return d_input.strftime("%Y-%m-%d")
    if not d_input:
        return ""
    d_str = str(d_input).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(d_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return d_str

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
STANDARD_LOCATIONS = ["NEW DELHI", "MUMBAI", "BANGALORE", "HYDERABAD", "PUNE", "CHENNAI", "KOLKATA", "AHMEDABAD"]

DEPT_COLORS = {
    "DEVELOPMENT": "#7C3AED",
    "DESIGN": "#2563EB",
    "MARKETING": "#D97706",
    "OPERATION": "#059669",
    "FINANCE": "#DC2626",
    "HR": "#EC4899",
    "SALES": "#10B981"
}

# ==============================================================================
# UI CONFIGURATION & CUSTOM CSS
# ==============================================================================

st.set_page_config(
    page_title="Employees Portal",
    page_icon="👤",
    layout="wide",
    initial_sidebar_state="collapsed"
)

init_db()

st.markdown("""
    <style>
    .stApp {
        background-color: #F9FAFB !important;
    }
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    .title-text {
        font-size: 24px;
        font-weight: 700;
        color: #111827;
        margin: 0;
    }
    .subtitle-text {
        font-size: 14px;
        color: #6B7280;
        margin-top: 2px;
    }
    div.stButton > button {
        border-radius: 6px !important;
        font-weight: 500 !important;
        font-size: 14px !important;
    }
    .table-header {
        font-size: 13px;
        font-weight: 600;
        color: #374151;
        padding: 8px 0px;
        border-bottom: 1px solid #E5E7EB;
    }
    .dept-dot {
        height: 8px;
        width: 8px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
    }
    div[data-baseweb="select"] {
        border-radius: 6px !important;
    }
    </style>
""", unsafe_allow_html=True)

if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "Manage Employees"

# ==============================================================================
# HEADER SECTION
# ==============================================================================
top_col1, top_col2, top_col3 = st.columns([3.5, 1, 1.2])

with top_col1:
    st.markdown("<div class='title-text'>Employees</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle-text'>Manage and view the complete list of employees within the organization.</div>", unsafe_allow_html=True)

with top_col2:
    conn = get_connection()
    df_all_emp = pd.read_sql_query("SELECT * FROM employees", conn)
    conn.close()
    
    if not df_all_emp.empty:
        file_name = "Employees_Report.xlsx"
        with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
            df_all_emp.to_excel(writer, sheet_name='EMPLOYEES', index=False)
        with open(file_name, "rb") as f:
            st.download_button(
                "⬆ Export",
                f,
                file_name=file_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

with top_col3:
    if st.button("➕ Add Employee", type="primary", use_container_width=True):
        st.session_state["show_add_modal"] = True

# ==============================================================================
# NAVIGATION TABS
# ==============================================================================
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

    # FILTER BAR
    f_c1, f_c2, f_c3, f_c4, f_c5 = st.columns([1.5, 1.5, 1.5, 1.5, 3])
    
    db_depts = [str(x).upper() for x in df_all_emp["department"].dropna().unique() if str(x).strip() != ""]
    all_depts_unique = sorted(list(set(STANDARD_DEPTS + db_depts)))
    
    db_locs = [str(x).upper() for x in df_all_emp["location"].dropna().unique() if str(x).strip() != ""]
    all_locs_unique = sorted(list(set(STANDARD_LOCATIONS + db_locs)))

    sel_dept = f_c1.selectbox("Department", ["All Departments"] + all_depts_unique, label_visibility="collapsed")
    sel_job = f_c2.selectbox("Job Title", ["All Job Titles"] + sorted(df_all_emp["designation"].dropna().unique().tolist()) if not df_all_emp.empty else ["All Job Titles"], label_visibility="collapsed")
    sel_loc = f_c3.selectbox("Location", ["All Locations"] + all_locs_unique, label_visibility="collapsed")

    if f_c4.button("Clear Filters"):
        st.rerun()

    search_q = f_c5.text_input("Search", placeholder="🔍 Search Employees by Name, ID, Location...", label_visibility="collapsed")

    # FILTERING LOGIC
    filtered_df = df_all_emp.copy() if not df_all_emp.empty else pd.DataFrame()
    
    if not filtered_df.empty:
        if sel_dept != "All Departments":
            filtered_df = filtered_df[filtered_df["department"].str.upper() == sel_dept.upper()]
        if sel_job != "All Job Titles":
            filtered_df = filtered_df[filtered_df["designation"] == sel_job]
        if sel_loc != "All Locations":
            filtered_df = filtered_df[filtered_df["location"].str.upper() == sel_loc.upper()]
        if search_q:
            filtered_df = filtered_df[
                filtered_df["name"].str.contains(search_q, case=False, na=False) |
                filtered_df["emp_id"].str.contains(search_q, case=False, na=False) |
                filtered_df["location"].str.contains(search_q, case=False, na=False)
            ]

    st.write(" ")

    # TABLE HEADER
    h_c1, h_c2, h_c3, h_c4, h_c5, h_c6, h_c7, h_c8 = st.columns([1, 2.2, 1.8, 2.2, 2, 1.8, 1.8, 1.2])
    h_c1.markdown("<div class='table-header'>Emp ID</div>", unsafe_allow_html=True)
    h_c2.markdown("<div class='table-header'>Employee Name</div>", unsafe_allow_html=True)
    h_c3.markdown("<div class='table-header'>Department</div>", unsafe_allow_html=True)
    h_c4.markdown("<div class='table-header'>Job Title</div>", unsafe_allow_html=True)
    h_c5.markdown("<div class='table-header'>Manager</div>", unsafe_allow_html=True)
    h_c6.markdown("<div class='table-header'>Date of Joining</div>", unsafe_allow_html=True)
    h_c7.markdown("<div class='table-header'>Location 📍</div>", unsafe_allow_html=True)
    h_c8.markdown("<div class='table-header'>Actions</div>", unsafe_allow_html=True)

    st.markdown("<hr style='margin:0px; border-top:1px solid #E5E7EB;'>", unsafe_allow_html=True)

    # TABLE ROWS
    if filtered_df.empty:
        st.info("No employee record found.")
    else:
        for _, row in filtered_df.iterrows():
            emp_id = str(row["emp_id"]).upper()
            name = str(row.get("name", "")).title()
            dept = str(row.get("department") if pd.notna(row.get("department")) else "DEVELOPMENT").upper()
            desg = str(row.get("designation") if pd.notna(row.get("designation")) else "Software Engineer").title()
            mogr = str(row.get("manager") if pd.notna(row.get("manager")) else "N/A").title()
            doj = format_date_display(row.get("joining_date", ""))
            loc = str(row.get("location") if pd.notna(row.get("location")) else "New Delhi").upper()

            dot_color = DEPT_COLORS.get(dept, "#6B7280")

            c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([1, 2.2, 1.8, 2.2, 2, 1.8, 1.8, 1.2])

            c1.write(f"`{emp_id}`")
            c2.write(f"**{name}**")
            c3.markdown(f"<span class='dept-dot' style='background-color:{dot_color};'></span> {dept.title()}", unsafe_allow_html=True)
            c4.write(desg)
            c5.write(mogr)
            c6.write(doj)
            c7.write(loc)

            act_col1, act_col2, act_col3 = c8.columns(3)
            if act_col1.button("👁️", key=f"view_{emp_id}", help="View Profile"):
                st.session_state["view_id"] = emp_id
            if act_col2.button("✏️", key=f"edit_{emp_id}", help="Edit Details"):
                st.session_state["edit_id"] = emp_id
            if act_col3.button("🗑️", key=f"del_{emp_id}", help="Delete Employee"):
                st.session_state["confirm_del_id"] = emp_id

            st.markdown("<hr style='margin:0px; border-top:1px solid #F3F4F6;'>", unsafe_allow_html=True)

# ==============================================================================
# TAB 2: ORGANISATION CHART
# ==============================================================================
elif st.session_state["active_tab"] == "Organisation Chart":
    st.markdown("### 🌿 Organisation Structure")
    if not df_all_emp.empty:
        for dept in df_all_emp["department"].unique():
            st.markdown(f"#### 🟢 Department: {str(dept).title()}")
            sub_df = df_all_emp[df_all_emp["department"] == dept]
            for _, r in sub_df.iterrows():
                st.write(f"• **{r['name']}** ({r['designation']}) — Manager: {r.get('manager', 'N/A')} | Location: {r.get('location', 'NEW DELHI')}")
            st.divider()
    else:
        st.info("No organization data available.")

# ==============================================================================
# TAB 3: LEAVE REQUESTS
# ==============================================================================
elif st.session_state["active_tab"] == "Leave Requests":
    st.markdown("### 📅 Leave Applications & Requests")
    if df_all_emp.empty:
        st.info("No employees available to request leave.")
    else:
        emp_dict = {f"{str(r['emp_id'])} - {str(r['name'])}": str(r['emp_id']) for _, r in df_all_emp.iterrows()}
        sel_emp_key = st.selectbox("Select Employee", list(emp_dict.keys()))
        target_id = emp_dict[sel_emp_key]

        conn = get_connection()
        rec = pd.read_sql_query(f"SELECT * FROM employees WHERE emp_id='{target_id}'", conn).iloc[0]
        conn.close()

        m1, m2, m3 = st.columns(3)
        m1.metric("Casual Leave (CL)", format_days(rec["cl_balance"]))
        m2.metric("Sick Leave (SL)", format_days(rec["sl_balance"]))
        m3.metric("Paid Leave (PL)", format_days(rec["pl_balance"]))

        with st.form("apply_l_form"):
            l_t = st.selectbox("Leave Type", ["CL", "SL", "PL"])
            l_d = st.number_input("Days", min_value=0.5, step=0.5)
            if st.form_submit_button("Deduct Leave", type="primary"):
                col_m = {"CL": "cl_balance", "SL": "sl_balance", "PL": "pl_balance"}
                curr_b = float(rec[col_m[l_t]])
                if curr_b >= l_d:
                    conn = get_connection()
                    conn.execute(f"UPDATE employees SET {col_m[l_t]} = {curr_b - l_d} WHERE emp_id='{target_id}'")
                    conn.commit()
                    conn.close()
                    st.success("Leave Deducted!")
                    st.rerun()
                else:
                    st.error("Insufficient Leave Balance!")

# ==============================================================================
# MODALS & POPUPS (ADD EMPLOYEE WITH LOCATION / VIEW / EDIT / DELETE)
# ==============================================================================

# ADD EMPLOYEE MODAL
if st.session_state.get("show_add_modal", False):
    with st.sidebar:
        st.markdown("### ➕ Register New Employee")
        with st.form("add_emp_modal_form"):
            e_id = st.text_input("Emp ID *").upper().strip()
            e_name = st.text_input("Full Name *").strip()
            e_dept = st.selectbox("Department", STANDARD_DEPTS)
            e_desg = st.text_input("Job Title / Designation", value="Software Engineer")
            e_mgr = st.text_input("Manager Name", value="Aditya Ravi")
            
            # Location Selection
            loc_options = STANDARD_LOCATIONS + ["➕ OTHER (ENTER MANUALLY)"]
            selected_loc = st.selectbox("Location", loc_options)
            custom_loc = ""
            if selected_loc == "➕ OTHER (ENTER MANUALLY)":
                custom_loc = st.text_input("Enter Custom Location").upper().strip()

            e_doj = st.date_input("Date of Joining", value=datetime.now().date())
            e_dob = st.date_input("Date of Birth", value=date(1995, 1, 1))

            st.markdown("---")
            st.markdown("**Optional Documents/Inventory**")
            e_inv = st.text_input("Initial Inventory (e.g. Laptop)")
            e_inv_ser = st.text_input("Serial No")

            if st.form_submit_button("Save Employee", type="primary"):
                final_loc = custom_loc if selected_loc == "➕ OTHER (ENTER MANUALLY)" else selected_loc
                if not final_loc:
                    final_loc = "NEW DELHI"

                if e_id and e_name:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO employees (emp_id, name, dob, joining_date, department, designation, manager, location, cycle_start, cycle_end)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (e_id, e_name, e_dob.strftime("%Y-%m-%d"), e_doj.strftime("%Y-%m-%d"), e_dept, e_desg, e_mgr, final_loc, e_doj.strftime("%Y-%m-%d"), (e_doj + relativedelta(months=6)).strftime("%Y-%m-%d")))
                    
                    if e_inv:
                        cursor.execute("INSERT INTO inventory (emp_id, item_name, serial_number, assigned_date) VALUES (?, ?, ?, ?)",
                                       (e_id, e_inv, e_inv_ser, datetime.now().strftime("%Y-%m-%d")))
                    
                    conn.commit()
                    conn.close()
                    st.success("Employee Added!")
                    st.session_state["show_add_modal"] = False
                    st.rerun()
                else:
                    st.error("Emp ID and Name are mandatory!")

        if st.button("Cancel"):
            st.session_state["show_add_modal"] = False
            st.rerun()

# DELETE CONFIRMATION
if "confirm_del_id" in st.session_state:
    del_id = st.session_state["confirm_del_id"]
    st.warning(f"Are you sure you want to delete Employee ID: **{del_id}**?")
    if st.button("Yes, Delete"):
        delete_employee(del_id)
        del st.session_state["confirm_del_id"]
        st.success("Deleted!")
        st.rerun()
    if st.button("Cancel Delete"):
        del st.session_state["confirm_del_id"]
        st.rerun()

# EDIT DETAILS
if "edit_id" in st.session_state:
    ed_id = st.session_state["edit_id"]
    conn = get_connection()
    df_e = pd.read_sql_query(f"SELECT * FROM employees WHERE emp_id='{ed_id}'", conn)
    conn.close()

    if not df_e.empty:
        rec = df_e.iloc[0]
        st.markdown(f"### ✏️ Edit Details: {rec['name']} ({rec['emp_id']})")
        
        with st.form("edit_modal_form"):
            u_name = st.text_input("Full Name", value=rec['name'])
            u_dept = st.selectbox("Department", STANDARD_DEPTS, index=STANDARD_DEPTS.index(rec['department']) if rec['department'] in STANDARD_DEPTS else 0)
            u_desg = st.text_input("Designation", value=rec['designation'])
            u_mgr = st.text_input("Manager", value=rec.get('manager', 'N/A'))
            u_loc = st.text_input("Location", value=rec.get('location', 'NEW DELHI')).upper()

            if st.form_submit_button("Save Changes", type="primary"):
                conn = get_connection()
                conn.execute("""
                    UPDATE employees 
                    SET name=?, department=?, designation=?, manager=?, location=?
                    WHERE emp_id=?
                """, (u_name, u_dept, u_desg, u_mgr, u_loc, ed_id))
                conn.commit()
                conn.close()
                st.success("Details Updated!")
                del st.session_state["edit_id"]
                st.rerun()

        if st.button("Close Edit"):
            del st.session_state["edit_id"]
            st.rerun()

# VIEW PROFILE
if "view_id" in st.session_state:
    v_id = st.session_state["view_id"]
    conn = get_connection()
    v_emp = pd.read_sql_query(f"SELECT * FROM employees WHERE emp_id='{v_id}'", conn).iloc[0]
    v_inv = pd.read_sql_query(f"SELECT * FROM inventory WHERE emp_id='{v_id}'", conn)
    conn.close()

    st.markdown(f"### 👤 Profile: {v_emp['name']} ({v_emp['emp_id']})")
    st.write(f"**Department:** {v_emp['department']} | **Job Title:** {v_emp['designation']} | **Manager:** {v_emp['manager']}")
    st.write(f"**Location 📍:** {v_emp.get('location', 'NEW DELHI')} | **Joining Date:** {format_date_display(v_emp['joining_date'])}")
    
    st.markdown("#### Assigned Inventory")
    st.dataframe(v_inv, use_container_width=True)

    if st.button("Close Profile"):
        del st.session_state["view_id"]
        st.rerun()
