import streamlit as st
import sqlite3
import pandas as pd
import json
import os
from datetime import datetime, date, timedelta

# ==============================================================================
# 1. PAGE CONFIGURATION & CSS
# ==============================================================================
st.set_page_config(
    page_title="HR & Payroll Management System",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Source Sans Pro', sans-serif !important;
        background-color: #ecf0f5 !important;
    }
    
    footer {visibility: hidden;}
    
    [data-testid="stSidebar"] {
        background-color: #222d32 !important;
    }
    [data-testid="stSidebar"] * {
        color: #b8c7ce !important;
    }
    
    .sidebar-brand {
        background-color: #008d4c;
        color: #ffffff !important;
        text-align: center;
        font-size: 20px;
        font-weight: 700;
        padding: 13px 10px;
        margin-top: -10px;
    }
    
    .sidebar-user {
        padding: 12px 15px;
        display: flex;
        align-items: center;
        gap: 12px;
        background-color: #222d32;
    }
    
    .sidebar-user-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background-color: #f39c12;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
    }

    .sidebar-header {
        color: #4b646f !important;
        background: #1a2226;
        padding: 8px 15px;
        font-size: 11px;
        font-weight: 700;
        margin-top: 10px;
    }

    .top-navbar {
        background-color: #1a4d3e;
        color: white;
        padding: 12px 20px;
        margin: -60px -60px 20px -60px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .metric-card {
        background-color: #fff;
        border-radius: 4px;
        padding: 15px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border-left: 5px solid #3c8dbc;
    }
    .metric-title {
        font-size: 13px;
        color: #777;
        font-weight: 600;
        text-transform: uppercase;
    }
    .metric-value {
        font-size: 26px;
        font-weight: 700;
        color: #333;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Top Navbar
st.markdown("""
    <div class="top-navbar">
        <div style="font-size: 18px; font-weight: 600;">HR & Payroll Management System</div>
        <div style="font-size: 14px; display: flex; align-items: center; gap: 8px;">
            <span style="background-color:#f39c12; padding:3px 8px; border-radius:50%; font-weight:bold; font-size:12px;">A</span>
            Welcome Admin
        </div>
    </div>
""", unsafe_allow_html=True)

# Directory to store uploaded files
UPLOADS_DIR = "uploaded_documents"
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

# ==============================================================================
# 2. DATABASE SETUP
# ==============================================================================
def get_db_connection():
    conn = sqlite3.connect("hr_management.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            emp_id TEXT PRIMARY KEY,
            emp_name TEXT NOT NULL,
            status TEXT DEFAULT 'Active',
            mobile TEXT,
            personal_email TEXT,
            office_email TEXT,
            aadhar TEXT,
            pan TEXT,
            emergency_name TEXT,
            emergency_contact TEXT,
            location TEXT,
            doj TEXT,
            dob TEXT,
            doe TEXT,
            inventory_details TEXT,
            documents_uploaded TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT,
            leave_type TEXT,
            from_date TEXT,
            to_date TEXT,
            reason TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)
    
    # Leave Balances Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leave_balances (
            emp_id TEXT PRIMARY KEY,
            cl INTEGER DEFAULT 3,
            sl INTEGER DEFAULT 3,
            pl INTEGER DEFAULT 1,
            paid_leave INTEGER DEFAULT 1,
            last_reset_date TEXT
        )
    """)
    
    conn.commit()
    conn.close()

init_db()

# ==============================================================================
# 3. SIDEBAR NAVIGATION
# ==============================================================================
st.sidebar.markdown('<div class="sidebar-brand">Payroll</div>', unsafe_allow_html=True)

st.sidebar.markdown("""
    <div class="sidebar-user">
        <div class="sidebar-user-avatar">A</div>
        <div>
            <div style="color:#fff; font-weight:600; font-size:14px;">Welcome Admin</div>
            <div style="color:#00a65a; font-size:11px;">● Online</div>
        </div>
    </div>
""", unsafe_allow_html=True)

st.sidebar.markdown('<div class="sidebar-header">MENU</div>', unsafe_allow_html=True)

main_menu = st.sidebar.radio(
    "NAVIGATION",
    ["📊 Dashboard", "➕ Add Employee", "👥 Employee Master", "🍃 Leave Tracker", "📑 Leave Management"],
    label_visibility="collapsed"
)

# ==============================================================================
# 4. DASHBOARD
# ==============================================================================
if main_menu == "📊 Dashboard":
    st.markdown("<h2 style='color:#333; font-weight:400;'>HR Dashboard</h2>", unsafe_allow_html=True)
    st.write("")
    
    conn = get_db_connection()
    df_emp = pd.read_sql_query("SELECT * FROM employees", conn)
    df_leaves = pd.read_sql_query("SELECT * FROM leave_requests WHERE status='Pending'", conn)
    conn.close()
    
    total_emp = len(df_emp)
    active_emp = len(df_emp[df_emp['status'] == 'Active']) if total_emp > 0 else 0
    inactive_emp = len(df_emp[df_emp['status'] == 'Inactive']) if total_emp > 0 else 0
    
    missing_docs_df = df_emp[(df_emp['documents_uploaded'].isna()) | (df_emp['documents_uploaded'] == '') | (df_emp['documents_uploaded'] == '[]')] if total_emp > 0 else pd.DataFrame()
    missing_docs_count = len(missing_docs_df)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card" style="border-left-color: #00c0ef;"><div class="metric-title">Total Employees</div><div class="metric-value">{total_emp}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card" style="border-left-color: #00a65a;"><div class="metric-title">Active Employees</div><div class="metric-value">{active_emp}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card" style="border-left-color: #dd4b39;"><div class="metric-title">Inactive Employees</div><div class="metric-value">{inactive_emp}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card" style="border-left-color: #f39c12;"><div class="metric-title">Missing Documents</div><div class="metric-value">{missing_docs_count}</div></div>', unsafe_allow_html=True)
        
    st.write("")
    st.write("")
    
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("⚠️ Employees with Missing / Pending Documents")
        if missing_docs_count > 0:
            st.dataframe(missing_docs_df[['emp_id', 'emp_name', 'mobile', 'office_email', 'status']], use_container_width=True, hide_index=True)
        else:
            st.success("Sabhi employees ke documents uploaded hain!")
            
    with col_right:
        st.subheader("⏳ Pending Leave Requests")
        if len(df_leaves) > 0:
            st.warning(f"Aapke paas **{len(df_leaves)}** leave requests pending hain.")
            st.dataframe(df_leaves[['emp_id', 'leave_type', 'from_date']], use_container_width=True, hide_index=True)
        else:
            st.info("Koi pending leave request nahi hai.")

# ==============================================================================
# 5. PROFESSIONAL ADD EMPLOYEE
# ==============================================================================
elif main_menu == "➕ Add Employee":
    st.markdown("<h2 style='color:#333; font-weight:400;'>Add New Employee Details</h2>", unsafe_allow_html=True)
    st.write("")
    
    with st.form("add_emp_form"):
        st.subheader("1. Basic & Contact Details")
        c1, c2, c3 = st.columns(3)
        emp_id = c1.text_input("Employee ID *", placeholder="e.g. EMP1001")
        emp_name = c2.text_input("Employee Name *", placeholder="Full Name")
        mobile = c3.text_input("Mobile Number", placeholder="10 Digit Number")
        
        c4, c5, c6 = st.columns(3)
        personal_email = c4.text_input("Personal Email")
        office_email = c5.text_input("Office Email")
        location = c6.text_input("Work Location", value="Delhi WFO")

        st.subheader("2. Identity & Emergency Details")
        i1, i2, i3, i4 = st.columns(4)
        aadhar = i1.text_input("Aadhar Card Number")
        pan = i2.text_input("PAN Card Number")
        emergency_name = i3.text_input("Emergency Contact Name")
        emergency_contact = i4.text_input("Emergency Contact Number")

        st.subheader("3. Important Dates & Status")
        d1, d2, d3, d4 = st.columns(4)
        dob = d1.date_input("Date of Birth (DOB)", value=date(1995, 1, 1))
        doj = d2.date_input("Date of Joining (DOJ)", value=date.today())
        doe_check = d3.checkbox("Has Exit Date (DOE)?")
        doe = d4.date_input("Date of Exit (DOE)", value=date.today()) if doe_check else ""
        emp_status = d1.selectbox("Status", ["Active", "Inactive"])

        st.subheader("4. Asset & Inventory Allocation")
        ic1, ic2, ic3, ic4 = st.columns(4)
        inv_item = ic1.selectbox("Item Type", ["Laptop", "Desktop", "Mobile", "Monitor", "Keyboard/Mouse", "Access Card", "Other"])
        inv_name = ic2.text_input("Brand / Model", placeholder="e.g. Dell Latitude 5420")
        inv_serial = ic3.text_input("Serial Number", placeholder="S/N: 987654321")
        inv_status = ic4.selectbox("Condition", ["New", "Good", "Refurbished"])

        st.subheader("5. Document Upload Center")
        doc_c1, doc_c2 = st.columns([1, 2])
        doc_type = doc_c1.selectbox("Select Document Type", [
            "Aadhar Card", "PAN Card", "Offer Letter", "Experience Letter", 
            "Relieving Letter", "Educational Marksheet", "Bank Passbook/Cheque", "Other"
        ])
        uploaded_files = doc_c2.file_uploader("Upload Documents (Multiple Allowed)", accept_multiple_files=True)

        submit_btn = st.form_submit_button("Save Employee Record", type="primary")

        if submit_btn:
            if not emp_id or not emp_name:
                st.error("Employee ID aur Name fill karna mandatory hai!")
            else:
                # Save Files
                saved_docs = []
                if uploaded_files:
                    for f in uploaded_files:
                        file_path = os.path.join(UPLOADS_DIR, f"{emp_id}_{doc_type.replace(' ', '_')}_{f.name}")
                        with open(file_path, "wb") as buffer:
                            buffer.write(f.getbuffer())
                        saved_docs.append({"type": doc_type, "filename": f.name, "path": file_path})

                # Inventory JSON
                inv_data = [{
                    "item": inv_item,
                    "model": inv_name,
                    "serial": inv_serial,
                    "condition": inv_status,
                    "issued_date": str(date.today())
                }] if inv_name else []

                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute("""
                        INSERT INTO employees 
                        (emp_id, emp_name, status, mobile, personal_email, office_email, aadhar, pan, 
                         emergency_name, emergency_contact, location, doj, dob, doe, inventory_details, documents_uploaded)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        emp_id, emp_name, emp_status, mobile, personal_email, office_email, aadhar, pan,
                        emergency_name, emergency_contact, location, str(doj), str(dob), str(doe),
                        json.dumps(inv_data), json.dumps(saved_docs)
                    ))
                    
                    # Initialize Leave Balance
                    cursor.execute("""
                        INSERT OR REPLACE INTO leave_balances (emp_id, cl, sl, pl, paid_leave, last_reset_date)
                        VALUES (?, 3, 3, 1, 1, ?)
                    """, (emp_id, str(date.today())))

                    conn.commit()
                    st.success(f"Employee {emp_name} ({emp_id}) successfully register ho gaye!")
                except sqlite3.IntegrityError:
                    st.error("Ye Employee ID pehle se exist karti hai!")
                finally:
                    conn.close()

# ==============================================================================
# 6. EMPLOYEE MASTER (EDIT, EXPORT & VIEW DOCUMENTS)
# ==============================================================================
elif main_menu == "👥 Employee Master":
    st.markdown("<h2 style='color:#333; font-weight:400;'>Employee Directory & Management</h2>", unsafe_allow_html=True)
    
    conn = get_db_connection()
    df_all = pd.read_sql_query("SELECT * FROM employees", conn)
    conn.close()
    
    if len(df_all) == 0:
        st.info("Koi Employee record nahi hai. Naya Employee add karein.")
    else:
        # Search & Export Bar
        exp_col1, exp_col2, exp_col3 = st.columns([3, 1, 1])
        search_term = exp_col1.text_input("🔍 Search Employee:", "", placeholder="Type Name or ID...")
        
        # Filter
        if search_term:
            df_all = df_all[
                df_all['emp_name'].str.contains(search_term, case=False, na=False) |
                df_all['emp_id'].str.contains(search_term, case=False, na=False)
            ]

        # Export Buttons
        csv_data = df_all.to_csv(index=False).encode('utf-8')
        exp_col2.download_button("📥 Export CSV", data=csv_data, file_name="employee_directory.csv", mime="text/csv")
        
        st.write("")

        # Action Tabs
        for idx, row in df_all.iterrows():
            with st.expander(f"👤 {row['emp_name']} ({row['emp_id']}) - {row['status']} | Location: {row['location']}"):
                
                tab1, tab2, tab3, tab4 = st.tabs(["📑 Full Details", "✏️ Edit Employee", "📂 View Documents", "💻 Inventory Assets"])

                # TAB 1: Details View
                with tab1:
                    c1, c2, c3 = st.columns(3)
                    c1.write(f"**Mobile:** {row['mobile']}")
                    c1.write(f"**Personal Email:** {row['personal_email']}")
                    c1.write(f"**Office Email:** {row['office_email']}")
                    
                    c2.write(f"**Aadhar:** {row['aadhar']}")
                    c2.write(f"**PAN:** {row['pan']}")
                    c2.write(f"**Emergency Contact:** {row['emergency_name']} ({row['emergency_contact']})")

                    c3.write(f"**DOJ:** {row['doj']}")
                    c3.write(f"**DOB:** {row['dob']}")
                    c3.write(f"**DOE:** {row['doe'] if row['doe'] else 'N/A'}")

                # TAB 2: Edit Form
                with tab2:
                    with st.form(f"edit_form_{row['emp_id']}"):
                        e1, e2, e3 = st.columns(3)
                        edit_name = e1.text_input("Name", value=row['emp_name'])
                        edit_mobile = e2.text_input("Mobile", value=row['mobile'])
                        edit_status = e3.selectbox("Status", ["Active", "Inactive"], index=0 if row['status']=="Active" else 1)
                        
                        e4, e5 = st.columns(2)
                        edit_off_email = e4.text_input("Office Email", value=row['office_email'])
                        edit_location = e5.text_input("Location", value=row['location'])

                        btn_update = st.form_submit_button("Update Employee Details")
                        if btn_update:
                            conn = get_db_connection()
                            conn.cursor().execute("""
                                UPDATE employees 
                                SET emp_name=?, mobile=?, status=?, office_email=?, location=?
                                WHERE emp_id=?
                            """, (edit_name, edit_mobile, edit_status, edit_off_email, edit_location, row['emp_id']))
                            conn.commit()
                            conn.close()
                            st.success("Details updated successfully!")
                            st.rerun()

                # TAB 3: Documents Viewer & Downloader
                with tab3:
                    st.subheader("Uploaded Documents")
                    docs = json.loads(row['documents_uploaded']) if row['documents_uploaded'] else []
                    if not docs:
                        st.info("Is employee ke koi documents upload nahi hain.")
                    else:
                        for doc in docs:
                            dc1, dc2, dc3 = st.columns([2, 2, 1])
                            dc1.write(f"**Type:** {doc.get('type', 'Document')}")
                            dc2.write(f"**File:** {doc.get('filename', '')}")
                            
                            file_path = doc.get('path', '')
                            if os.path.exists(file_path):
                                with open(file_path, "rb") as file:
                                    dc3.download_button("⬇️ Download", data=file, file_name=doc['filename'], key=f"dl_{row['emp_id']}_{doc['filename']}")
                            else:
                                dc3.error("File missing")

                # TAB 4: Inventory Details
                with tab4:
                    st.subheader("Assigned Assets")
                    inv = json.loads(row['inventory_details']) if row['inventory_details'] else []
                    if not inv:
                        st.info("Koi asset assign nahi kiya gaya.")
                    else:
                        st.table(pd.DataFrame(inv))

# ==============================================================================
# 7. LEAVE TRACKER (WITH 3-MONTH ELIGIBILITY & CARRY FORWARD)
# ==============================================================================
elif main_menu == "🍃 Leave Tracker":
    st.markdown("<h2 style='color:#333; font-weight:400;'>Apply Leave</h2>", unsafe_allow_html=True)
    
    conn = get_db_connection()
    employees_df = pd.read_sql_query("SELECT emp_id, emp_name, doj FROM employees WHERE status='Active'", conn)
    conn.close()
    
    if len(employees_df) == 0:
        st.warning("Leave apply karne ke liye koi Active employee nahi hai.")
    else:
        emp_map = {f"{r['emp_id']} - {r['emp_name']}": r for _, r in employees_df.iterrows()}
        selected_emp_key = st.selectbox("Select Employee", list(emp_map.keys()))
        selected_emp = emp_map[selected_emp_key]

        # Calculate Eligibility (3 Months Check)
        doj_date = datetime.strptime(selected_emp['doj'], "%Y-%m-%d").date()
        days_completed = (date.today() - doj_date).days
        is_eligible = days_completed >= 90  # 3 Months ~ 90 Days

        if not is_eligible:
            st.error(f"⚠️ **Not Eligible for Leave:** {selected_emp['emp_name']} ki joining date {selected_emp['doj']} hai. Leave apply karne ke liye minimum **3 months (90 days)** completed hone chahiye. (Completed: {days_completed} days)")
        else:
            # Show Balances
            conn = get_db_connection()
            bal = pd.read_sql_query("SELECT * FROM leave_balances WHERE emp_id=?", conn, params=(selected_emp['emp_id'],))
            conn.close()

            if len(bal) > 0:
                b = bal.iloc[0]
                st.info(f"📊 **Available Leave Balances:** Casual Leave (CL): **{b['cl']}** | Sick Leave (SL): **{b['sl']}** | Paid Leave (PL): **{b['pl']}** | Special Paid Leave: **{b['paid_leave']}**")

            with st.form("apply_leave_form"):
                leave_type = st.selectbox("Leave Type", ["Casual Leave (CL)", "Sick Leave (SL)", "Paid Leave (PL)", "Special Paid Leave"])
                c1, c2 = st.columns(2)
                from_date = c1.date_input("From Date", value=date.today())
                to_date = c2.date_input("To Date", value=date.today())
                reason = st.text_area("Reason for Leave")
                
                submit_leave = st.form_submit_button("Submit Leave Request", type="primary")
                if submit_leave:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO leave_requests (emp_id, leave_type, from_date, to_date, reason)
                        VALUES (?, ?, ?, ?, ?)
                    """, (selected_emp['emp_id'], leave_type, str(from_date), str(to_date), reason))
                    conn.commit()
                    conn.close()
                    st.success("Leave Request submit ho gayi! Admin approval ka wait karein.")

# ==============================================================================
# 8. LEAVE MANAGEMENT (APPROVAL & CARRY FORWARD)
# ==============================================================================
elif main_menu == "📑 Leave Management":
    st.markdown("<h2 style='color:#333; font-weight:400;'>Leave Management & Approvals</h2>", unsafe_allow_html=True)
    
    conn = get_db_connection()
    df_requests = pd.read_sql_query("""
        SELECT l.id, l.emp_id, e.emp_name, l.leave_type, l.from_date, l.to_date, l.reason, l.status
        FROM leave_requests l
        LEFT JOIN employees e ON l.emp_id = e.emp_id
    """, conn)
    conn.close()

    if len(df_requests) == 0:
        st.info("Koi leave request application nahi hai.")
    else:
        for idx, row in df_requests.iterrows():
            with st.expander(f"{row['emp_name']} ({row['emp_id']}) - {row['leave_type']} | Status: {row['status']}"):
                st.write(f"**Dates:** {row['from_date']} to {row['to_date']}")
                st.write(f"**Reason:** {row['reason']}")
                
                if row['status'] == 'Pending':
                    cb1, cb2 = st.columns(2)
                    if cb1.button("✅ Approve", key=f"app_{row['id']}"):
                        conn = get_db_connection()
                        # Deduct balance
                        cursor = conn.cursor()
                        cursor.execute("UPDATE leave_requests SET status='Approved' WHERE id=?", (row['id'],))
                        
                        col_name = "cl" if "CL" in row['leave_type'] else "sl" if "SL" in row['leave_type'] else "pl" if "PL" in row['leave_type'] else "paid_leave"
                        cursor.execute(f"UPDATE leave_balances SET {col_name} = MAX(0, {col_name} - 1) WHERE emp_id=?", (row['emp_id'],))
                        
                        conn.commit()
                        conn.close()
                        st.success("Leave approved and balance updated!")
                        st.rerun()
                        
                    if cb2.button("❌ Reject", key=f"rej_{row['id']}"):
                        conn = get_db_connection()
                        conn.cursor().execute("UPDATE leave_requests SET status='Rejected' WHERE id=?", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.rerun()
