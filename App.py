import streamlit as st
import sqlite3
import pandas as pd
import json
import os
import base64
from datetime import datetime, date

# ==============================================================================
# 1. PAGE CONFIGURATION & STYLING
# ==============================================================================
st.set_page_config(
    page_title="HR & Payroll Management System",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling matching Image 2 (AdminLTE Style Tables & Buttons)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Source Sans Pro', sans-serif !important;
        background-color: #f4f6f9 !important;
    }
    
    footer {visibility: hidden;}
    
    /* Sidebar Styling */
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

    /* Top Header Bar */
    .top-navbar {
        background-color: #1a4d3e;
        color: white;
        padding: 12px 20px;
        margin: -60px -60px 20px -60px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* Table Container Styling */
    .admin-table-header {
        background-color: #ffffff;
        font-weight: 700;
        color: #333333;
        border-bottom: 2px solid #dee2e6;
        padding: 10px 5px;
        font-size: 14px;
    }
    
    .admin-table-row {
        background-color: #ffffff;
        border-bottom: 1px solid #e9ecef;
        padding: 8px 5px;
        font-size: 13px;
        color: #495057;
    }

    .admin-table-row:hover {
        background-color: #f8f9fa;
    }

    /* Styled Buttons like Image 2 */
    div.stButton > button[key^="edit_"] {
        background-color: #28a745 !important;
        color: white !important;
        border: none !important;
        padding: 4px 10px !important;
        font-size: 12px !important;
        border-radius: 3px !important;
        width: 100%;
    }
    
    div.stButton > button[key^="del_"] {
        background-color: #dc3545 !important;
        color: white !important;
        border: none !important;
        padding: 4px 10px !important;
        font-size: 12px !important;
        border-radius: 3px !important;
        width: 100%;
    }

    /* Metric Cards */
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

# Top Bar Header
st.markdown("""
    <div class="top-navbar">
        <div style="font-size: 18px; font-weight: 600;">HR & Payroll Management System</div>
        <div style="font-size: 14px; display: flex; align-items: center; gap: 8px;">
            <span style="background-color:#f39c12; padding:3px 8px; border-radius:50%; font-weight:bold; font-size:12px;">A</span>
            Welcome Admin
        </div>
    </div>
""", unsafe_allow_html=True)

# Upload Directory Setup
UPLOADS_DIR = "uploaded_documents"
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

# Standard Inventory Items List
ASSET_OPTIONS = ["Laptop", "Desktop", "Wireless Mouse", "Keyboard", "Headset / Headphones", "Company Mobile", "ID Card", "Access Card", "Laptop Bag"]

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
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leave_balances (
            emp_id TEXT PRIMARY KEY,
            cl INTEGER DEFAULT 3,
            sl INTEGER DEFAULT 3,
            pl INTEGER DEFAULT 1,
            paid_leave INTEGER DEFAULT 1
        )
    """)
    
    conn.commit()
    conn.close()

init_db()

# Safe Date Parser
def parse_date_safe(date_str, fallback=date.today()):
    if not date_str or date_str == 'None' or date_str == '':
        return fallback
    try:
        return datetime.strptime(str(date_str), "%Y-%m-%d").date()
    except:
        return fallback

# PDF Viewer Helper
def display_pdf_preview(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="450" type="application/pdf" style="border: 1px solid #ddd; border-radius: 5px;"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# ==============================================================================
# EDIT & DOCUMENT MODAL DIALOG WITH PREVIEW
# ==============================================================================
@st.dialog("⚙️ Manage Employee Profile", width="large")
def edit_employee_dialog(emp_data):
    st.caption(f"Employee ID: **{emp_data['emp_id']}** | Name: **{emp_data['emp_name']}**")
    
    tab_edit, tab_docs = st.tabs(["✏️ Edit Profile & Assets", "📂 View & Manage Documents"])

    # ------------------ TAB 1: EDIT PROFILE & INVENTORY ------------------
    with tab_edit:
        with st.form("edit_modal_form"):
            st.markdown("##### 👤 Personal & Contact Info")
            c1, c2, c3 = st.columns(3)
            e_name = c1.text_input("Name *", value=emp_data['emp_name'])
            e_status = c2.selectbox("Status", ["Active", "Inactive"], index=0 if emp_data['status']=='Active' else 1)
            e_mobile = c3.text_input("Mobile Number", value=emp_data['mobile'])
            
            c4, c5, c6 = st.columns(3)
            e_pemail = c4.text_input("Personal Email", value=emp_data['personal_email'])
            e_oemail = c5.text_input("Office Email", value=emp_data['office_email'])
            e_location = c6.text_input("Location", value=emp_data['location'])

            st.markdown("##### 🆔 Identity & Emergency Contact")
            c7, c8, c9, c10 = st.columns(4)
            e_aadhar = c7.text_input("Aadhar Number", value=emp_data['aadhar'])
            e_pan = c8.text_input("PAN Number", value=emp_data['pan'])
            e_emg_name = c9.text_input("Emergency Contact Person", value=emp_data['emergency_name'])
            e_emg_contact = c10.text_input("Emergency Contact Number", value=emp_data['emergency_contact'])

            st.markdown("##### 📅 Employment Dates")
            c11, c12, c13 = st.columns(3)
            e_dob = c11.date_input("Date of Birth (DOB)", value=parse_date_safe(emp_data['dob'], date(1998, 1, 19)))
            e_doj = c12.date_input("Date of Joining (DOJ)", value=parse_date_safe(emp_data['doj']))
            e_doe_str = c13.text_input("Date of Exit (DOE)", value=str(emp_data['doe']) if emp_data['doe'] and emp_data['doe']!='None' else "")

            st.markdown("##### 💻 Asset & Inventory Management")
            existing_inv_str = emp_data['inventory_details'] if emp_data['inventory_details'] else ""
            existing_items = [i.strip() for i in existing_inv_str.split(",") if i.strip()]
            
            preset_selected = [item for item in existing_items if item in ASSET_OPTIONS]
            custom_selected = [item for item in existing_items if item not in ASSET_OPTIONS]

            selected_assets = st.multiselect("Assigned Assets", options=ASSET_OPTIONS, default=preset_selected)
            other_assets = st.text_input("Other Assets / Serial Numbers (Optional)", value=", ".join(custom_selected), placeholder="e.g. Dell Monitor S/N 9821, Dongle")

            save_btn = st.form_submit_button("💾 Save All Changes", type="primary")
            
            if save_btn:
                all_inv = selected_assets.copy()
                if other_assets.strip():
                    all_inv.append(other_assets.strip())
                final_inv_str = ", ".join(all_inv)

                conn = get_db_connection()
                conn.cursor().execute("""
                    UPDATE employees 
                    SET emp_name=?, status=?, mobile=?, personal_email=?, office_email=?, location=?,
                        aadhar=?, pan=?, emergency_name=?, emergency_contact=?, dob=?, doj=?, doe=?, inventory_details=?
                    WHERE emp_id=?
                """, (
                    e_name, e_status, e_mobile, e_pemail, e_oemail, e_location,
                    e_aadhar, e_pan, e_emg_name, e_emg_contact, str(e_dob), str(e_doj), e_doe_str, final_inv_str,
                    emp_data['emp_id']
                ))
                conn.commit()
                conn.close()
                st.success("Sari details aur inventory update ho gayi!")
                st.rerun()

    # ------------------ TAB 2: PREVIEW, DOWNLOAD & UPLOAD DOCUMENTS ------------------
    with tab_docs:
        docs_raw = emp_data['documents_uploaded']
        try:
            current_docs = json.loads(docs_raw) if docs_raw else []
        except:
            current_docs = []

        st.markdown("##### 👁️ Uploaded Documents (Preview & Download)")

        if not current_docs:
            st.info("Abhi is employee ke koi documents uploaded nahi hain.")
        else:
            for idx, doc in enumerate(current_docs):
                file_path = doc.get('path', '')
                file_name = doc.get('filename', 'file')
                doc_type = doc.get('type', 'Document')
                
                with st.expander(f"📄 {doc_type} - {file_name}", expanded=(idx == 0)):
                    if os.path.exists(file_path):
                        ext = os.path.splitext(file_name)[1].lower()
                        
                        st.markdown("**Preview:**")
                        if ext in ['.png', '.jpg', '.jpeg']:
                            st.image(file_path, caption=file_name, use_column_width=True)
                        elif ext == '.pdf':
                            display_pdf_preview(file_path)
                        else:
                            st.caption(f"📁 Preview not supported for {ext} files. Please download to view.")
                        
                        st.write("")
                        btn_c1, btn_c2 = st.columns([1, 4])
                        with open(file_path, "rb") as f:
                            btn_c1.download_button("⬇️ Download File", data=f, file_name=file_name, key=f"preview_dl_{emp_data['emp_id']}_{idx}", type="primary")
                        
                        if btn_c2.button("🗑️ Remove Document", key=f"del_doc_{emp_data['emp_id']}_{idx}"):
                            current_docs.pop(idx)
                            conn = get_db_connection()
                            conn.cursor().execute("UPDATE employees SET documents_uploaded=? WHERE emp_id=?", (json.dumps(current_docs), emp_data['emp_id']))
                            conn.commit()
                            conn.close()
                            st.toast("Document removed!")
                            st.rerun()
                    else:
                        st.error("⚠️ File missing on server system!")

        st.markdown("---")
        st.markdown("##### 📤 Upload New Document")
        with st.form("modal_upload_form"):
            uc1, uc2 = st.columns([1, 2])
            new_doc_type = uc1.selectbox("Document Category", ["Aadhar Card", "PAN Card", "Offer Letter", "Relieving Letter", "Markssheet", "Resume", "Other"])
            new_file = uc2.file_uploader("Choose File (PDF, PNG, JPG supported)", type=['pdf', 'png', 'jpg', 'jpeg', 'docx'])
            
            upload_submit = st.form_submit_button("⬆️ Upload Document")
            
            if upload_submit:
                if new_file is not None:
                    file_path = os.path.join(UPLOADS_DIR, f"{emp_data['emp_id']}_{new_doc_type}_{new_file.name}")
                    with open(file_path, "wb") as buffer:
                        buffer.write(new_file.getbuffer())
                    
                    current_docs.append({
                        "type": new_doc_type,
                        "filename": new_file.name,
                        "path": file_path,
                        "uploaded_on": str(date.today())
                    })
                    
                    conn = get_db_connection()
                    conn.cursor().execute("UPDATE employees SET documents_uploaded=? WHERE emp_id=?", (json.dumps(current_docs), emp_data['emp_id']))
                    conn.commit()
                    conn.close()
                    st.success(f"{new_file.name} successfully upload ho gaya!")
                    st.rerun()
                else:
                    st.error("Pehle file choose karein!")

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
# 4. DASHBOARD PAGE
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
    
    missing_docs_df = df_emp[(df_emp['documents_uploaded'].isna()) | (df_emp['documents_uploaded'] == '') | (df_emp['documents_uploaded'] == 'None') | (df_emp['documents_uploaded'] == '[]')] if total_emp > 0 else pd.DataFrame()
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
# 5. ADD EMPLOYEE PAGE
# ==============================================================================
elif main_menu == "➕ Add Employee":
    st.markdown("<h2 style='color:#333; font-weight:400;'>Add New Employee Details</h2>", unsafe_allow_html=True)
    st.write("")
    
    with st.form("add_emp_form"):
        st.subheader("1. Basic & Contact Details")
        c1, c2, c3 = st.columns(3)
        emp_id = c1.text_input("Employee ID *", placeholder="e.g. VMPL19")
        emp_name = c2.text_input("Employee Name *", placeholder="Full Name")
        mobile = c3.text_input("Mobile Number", placeholder="10 Digit Number")
        
        c4, c5, c6 = st.columns(3)
        personal_email = c4.text_input("Personal Email")
        office_email = c5.text_input("Office Email")
        location = c6.text_input("Work Location", value="Gurgaon")

        st.subheader("2. Identity & Emergency Details")
        i1, i2, i3, i4 = st.columns(4)
        aadhar = i1.text_input("Aadhar Card Number")
        pan = i2.text_input("PAN Card Number")
        emergency_name = i3.text_input("Emergency Contact Name")
        emergency_contact = i4.text_input("Emergency Contact Number")

        st.subheader("3. Important Dates & Status")
        d1, d2, d3, d4 = st.columns(4)
        dob = d1.date_input("Date of Birth (DOB)", value=date(1998, 1, 19))
        doj = d2.date_input("Date of Joining (DOJ)", value=date.today())
        doe_check = d3.checkbox("Has Exit Date (DOE)?")
        doe = d4.date_input("Date of Exit (DOE)", value=date.today()) if doe_check else ""
        emp_status = d1.selectbox("Status", ["Active", "Inactive"])

        st.subheader("4. Inventory & Asset Details")
        selected_assets = st.multiselect("Select Assigned Assets", options=ASSET_OPTIONS)
        custom_asset = st.text_input("Other Custom Assets (Optional)", placeholder="e.g. Monitor S/N 1234")

        st.subheader("5. Document Upload Center")
        doc_c1, doc_c2 = st.columns([1, 2])
        doc_type = doc_c1.selectbox("Document Type", ["Aadhar Card", "PAN Card", "Offer Letter", "Experience Letter", "Markssheet", "Other"])
        uploaded_files = doc_c2.file_uploader("Upload Documents (Multiple Allowed)", accept_multiple_files=True)

        submit_btn = st.form_submit_button("Save Employee", type="primary")

        if submit_btn:
            if not emp_id or not emp_name:
                st.error("Employee ID aur Name mandatory hai!")
            else:
                inv_list = selected_assets.copy()
                if custom_asset.strip():
                    inv_list.append(custom_asset.strip())
                final_inv = ", ".join(inv_list)

                saved_docs = []
                if uploaded_files:
                    for f in uploaded_files:
                        file_path = os.path.join(UPLOADS_DIR, f"{emp_id}_{doc_type}_{f.name}")
                        with open(file_path, "wb") as buffer:
                            buffer.write(f.getbuffer())
                        saved_docs.append({"type": doc_type, "filename": f.name, "path": file_path, "uploaded_on": str(date.today())})

                docs_str = json.dumps(saved_docs) if saved_docs else ""

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
                        emergency_name, emergency_contact, location, str(doj), str(dob), str(doe), final_inv, docs_str
                    ))
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO leave_balances (emp_id, cl, sl, pl, paid_leave)
                        VALUES (?, 3, 3, 1, 1)
                    """, (emp_id,))

                    conn.commit()
                    st.success(f"Employee {emp_name} ({emp_id}) successfully saved!")
                except sqlite3.IntegrityError:
                    st.error("Ye Employee ID pehle se registered hai!")
                finally:
                    conn.close()

# ==============================================================================
# 6. EMPLOYEE MASTER (NEW CLEAN ADMIN-LTE STYLE TABLE LIKE IMAGE 2)
# ==============================================================================
elif main_menu == "👥 Employee Master":
    st.markdown("<h2 style='color:#333; font-weight:400;'>Employee Directory</h2>", unsafe_allow_html=True)
    
    conn = get_db_connection()
    df_all = pd.read_sql_query("SELECT * FROM employees", conn)
    conn.close()
    
    if len(df_all) == 0:
        st.info("Abhi koi employee record nahi hai. Sidebar se **➕ Add Employee** par jayein.")
    else:
        # Search & Display Controls
        sc1, sc2 = st.columns([3, 1])
        search = sc1.text_input("🔍 Search Employee:", "", placeholder="Type name, ID or mobile...")
        if search:
            df_all = df_all[
                df_all['emp_name'].str.contains(search, case=False, na=False) |
                df_all['emp_id'].str.contains(search, case=False, na=False) |
                df_all['mobile'].str.contains(search, case=False, na=False)
            ]

        st.write("")

        # Column Layout Width Ratios to prevent horizontal text wrapping issue
        # Clean Admin Table headers matching Image 2
        col_ratios = [1.1, 1.4, 0.8, 1.1, 1.6, 1.0, 1.0, 1.3, 1.8]
        
        # Table Header Row
        th_cols = st.columns(col_ratios)
        headers = ["Emp ID", "Name", "Status", "Mobile", "Office Email", "DOJ", "Location", "Assets", "Tools / Actions"]
        
        for idx, head in enumerate(headers):
            th_cols[idx].markdown(f"<div class='admin-table-header'>{head}</div>", unsafe_allow_html=True)
        
        # Table Data Rows
        for idx, row in df_all.iterrows():
            tr_cols = st.columns(col_ratios)
            
            tr_cols[0].markdown(f"<div class='admin-table-row'><b>{row['emp_id']}</b></div>", unsafe_allow_html=True)
            tr_cols[1].markdown(f"<div class='admin-table-row'>{row['emp_name']}</div>", unsafe_allow_html=True)
            
            # Status badge style
            status_color = "#28a745" if row['status'] == 'Active' else "#dc3545"
            tr_cols[2].markdown(f"<div class='admin-table-row'><span style='color:{status_color}; font-weight:bold;'>● {row['status']}</span></div>", unsafe_allow_html=True)
            
            tr_cols[3].markdown(f"<div class='admin-table-row'>{row['mobile'] or '-'}</div>", unsafe_allow_html=True)
            tr_cols[4].markdown(f"<div class='admin-table-row'>{row['office_email'] or '-'}</div>", unsafe_allow_html=True)
            tr_cols[5].markdown(f"<div class='admin-table-row'>{row['doj'] or '-'}</div>", unsafe_allow_html=True)
            tr_cols[6].markdown(f"<div class='admin-table-row'>{row['location'] or '-'}</div>", unsafe_allow_html=True)
            tr_cols[7].markdown(f"<div class='admin-table-row'>{row['inventory_details'] or '-'}</div>", unsafe_allow_html=True)
            
            # Action Buttons Column like Image 2 (Green Edit + Red Delete)
            act_col1, act_col2 = tr_cols[8].columns(2)
            if act_col1.button("✏️ Edit", key=f"edit_{row['emp_id']}"):
                edit_employee_dialog(row)
            
            if act_col2.button("🗑️ Delete", key=f"del_{row['emp_id']}"):
                conn = get_db_connection()
                conn.cursor().execute("DELETE FROM employees WHERE emp_id=?", (row['emp_id'],))
                conn.commit()
                conn.close()
                st.toast(f"Employee {row['emp_id']} deleted!")
                st.rerun()

# ==============================================================================
# 7. LEAVE TRACKER
# ==============================================================================
elif main_menu == "🍃 Leave Tracker":
    st.markdown("<h2 style='color:#333; font-weight:400;'>Apply Leave</h2>", unsafe_allow_html=True)
    
    conn = get_db_connection()
    employees_df = pd.read_sql_query("SELECT emp_id, emp_name, doj FROM employees WHERE status='Active'", conn)
    conn.close()
    
    if len(employees_df) == 0:
        st.warning("Pehle Active employees add karein.")
    else:
        emp_map = {f"{r['emp_id']} - {r['emp_name']}": r for _, r in employees_df.iterrows()}
        selected_emp_key = st.selectbox("Select Employee", list(emp_map.keys()))
        selected_emp = emp_map[selected_emp_key]

        try:
            doj_date = datetime.strptime(selected_emp['doj'], "%Y-%m-%d").date()
            days_completed = (date.today() - doj_date).days
        except:
            days_completed = 100

        if days_completed < 90:
            st.error(f"⚠️ **Not Eligible:** Employee ko joining kiye hue 3 months (90 days) nahi hue hain. (Completed: {days_completed} days)")
        else:
            conn = get_db_connection()
            bal = pd.read_sql_query("SELECT * FROM leave_balances WHERE emp_id=?", conn, params=(selected_emp['emp_id'],))
            conn.close()

            if len(bal) > 0:
                b = bal.iloc[0]
                st.info(f"📊 **Available Leaves:** Casual Leave (CL): **{b['cl']}** | Sick Leave (SL): **{b['sl']}** | Paid Leave (PL): **{b['pl']}** | Special Paid Leave: **{b['paid_leave']}**")

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
                    st.success("Leave Request successfully submit ho gayi!")

# ==============================================================================
# 8. LEAVE MANAGEMENT
# ==============================================================================
elif main_menu == "📑 Leave Management":
    st.markdown("<h2 style='color:#333; font-weight:400;'>Leave Approvals & Management</h2>", unsafe_allow_html=True)
    
    conn = get_db_connection()
    df_requests = pd.read_sql_query("""
        SELECT l.id, l.emp_id, e.emp_name, l.leave_type, l.from_date, l.to_date, l.reason, l.status
        FROM leave_requests l
        LEFT JOIN employees e ON l.emp_id = e.emp_id
    """, conn)
    conn.close()
    
    if len(df_requests) == 0:
        st.info("Koi leave request nahi hai.")
    else:
        for idx, row in df_requests.iterrows():
            with st.expander(f"{row['emp_name']} ({row['emp_id']}) - {row['leave_type']} [{row['status']}]"):
                st.write(f"**Dates:** {row['from_date']} to {row['to_date']}")
                st.write(f"**Reason:** {row['reason']}")
                
                if row['status'] == 'Pending':
                    cb1, cb2 = st.columns(2)
                    if cb1.button("✅ Approve", key=f"app_{row['id']}"):
                        conn = get_db_connection()
                        conn.cursor().execute("UPDATE leave_requests SET status='Approved' WHERE id=?", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.success("Leave Approved!")
                        st.rerun()
                        
                    if cb2.button("❌ Reject", key=f"rej_{row['id']}"):
                        conn = get_db_connection()
                        conn.cursor().execute("UPDATE leave_requests SET status='Rejected' WHERE id=?", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.rerun()
