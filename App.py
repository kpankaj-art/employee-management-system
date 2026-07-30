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

# Custom Styling (AdminLTE Theme + High Contrast Readable Sidebar)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Source Sans Pro', sans-serif !important;
        background-color: #f4f6f9 !important;
    }
    
    footer {visibility: hidden;}

    /* ----------------------------------------------------------- */
    /* HIDE TOP TOOLBAR (Share, Edit, GitHub) & BOTTOM MANAGE APP */
    /* ----------------------------------------------------------- */
    header[data-testid="stHeader"] {
        visibility: hidden !important;
        height: 0px !important;
    }

    [data-testid="stAppDeployButton"], 
    .stAppDeployButton, 
    div[class*="viewerBadge"],
    #MainMenu {
        display: none !important;
    }
    /* ----------------------------------------------------------- */
    
    /* SIDEBAR STYLING ENHANCEMENT */
    [data-testid="stSidebar"] {
        background-color: #1e272c !important;
    }
    
    .sidebar-brand {
        background-color: #00a65a;
        color: #ffffff !important;
        text-align: center;
        font-size: 22px;
        font-weight: 700;
        padding: 16px 10px;
        margin-top: -15px;
        border-bottom: 2px solid #008d4c;
        letter-spacing: 1px;
    }

    .sidebar-user {
        padding: 15px 10px;
        background-color: #222d32;
        border-bottom: 1px solid #2c3b41;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    /* HIGH VISIBILITY RADIO BUTTONS & MENU TEXT */
    [data-testid="stSidebar"] div[class*="stRadio"] label {
        font-size: 16px !important;
        font-weight: 600 !important;
        padding: 10px 12px !important;
        color: #ffffff !important; /* Pure White text */
        border-radius: 6px !important;
        transition: all 0.3s ease !important;
        margin-bottom: 4px !important;
        opacity: 1 !important;
    }

    [data-testid="stSidebar"] div[class*="stRadio"] label p {
        color: #ffffff !important;
        font-size: 16px !important;
        font-weight: 600 !important;
    }

    /* Selected Item Highlight */
    [data-testid="stSidebar"] div[class*="stRadio"] label[aria-checked="true"] p {
        color: #00e676 !important; /* Bright Neon Green */
        font-weight: 700 !important;
    }

    [data-testid="stSidebar"] div[class*="stRadio"] label:hover {
        background-color: #2c3b41 !important;
        color: #00e676 !important;
    }

    /* Sidebar Extra Widgets */
    .sidebar-widget {
        background-color: #222d32;
        border-radius: 8px;
        padding: 12px 15px;
        margin-top: 20px;
        border-left: 4px solid #00a65a;
        color: #ffffff;
    }
    .sidebar-widget-title {
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        color: #8aa4af;
        margin-bottom: 8px;
    }
    .sidebar-stat-item {
        display: flex;
        justify-content: space-between;
        font-size: 14px;
        padding: 4px 0;
        border-bottom: 1px solid #2c3b41;
        color: #ffffff;
    }
    .sidebar-stat-item:last-child {
        border-bottom: none;
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

    .admin-table-header {
        background-color: #ffffff;
        font-weight: 700;
        color: #333333;
        border-bottom: 2px solid #dee2e6;
        padding: 10px 5px;
        font-size: 13px;
    }
    
    .admin-table-row {
        background-color: #ffffff;
        border-bottom: 1px solid #e9ecef;
        padding: 8px 5px;
        font-size: 13px;
        color: #495057;
    }

    div.stButton > button[key^="view_"], div.stButton > button[key^="salhist_"] {
        background-color: #17a2b8 !important;
        color: white !important;
        border: none !important;
        padding: 4px 6px !important;
        font-size: 11px !important;
        border-radius: 3px !important;
        width: 100%;
    }

    div.stButton > button[key^="edit_"], div.stButton > button[key^="sal_"] {
        background-color: #28a745 !important;
        color: white !important;
        border: none !important;
        padding: 4px 6px !important;
        font-size: 11px !important;
        border-radius: 3px !important;
        width: 100%;
    }
    
    div.stButton > button[key^="del_"] {
        background-color: #dc3545 !important;
        color: white !important;
        border: none !important;
        padding: 4px 6px !important;
        font-size: 11px !important;
        border-radius: 3px !important;
        width: 100%;
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

UPLOADS_DIR = "uploaded_documents"
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

ASSET_OPTIONS = ["Laptop", "Desktop", "Wireless Mouse", "Keyboard", "Headset / Headphones", "Company Mobile", "ID Card", "Access Card", "Laptop Bag"]

# ==============================================================================
# 2. DATABASE SETUP & HELPER FUNCTIONS
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
            department TEXT,
            designation TEXT,
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
            documents_uploaded TEXT,
            salary REAL DEFAULT 0.0
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS salary_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT,
            previous_salary REAL,
            new_salary REAL,
            updated_at TEXT
        )
    """)
    
    cursor.execute("PRAGMA table_info(employees)")
    columns = [column[1] for column in cursor.fetchall()]
    if "department" not in columns:
        cursor.execute("ALTER TABLE employees ADD COLUMN department TEXT")
    if "designation" not in columns:
        cursor.execute("ALTER TABLE employees ADD COLUMN designation TEXT")
    if "salary" not in columns:
        cursor.execute("ALTER TABLE employees ADD COLUMN salary REAL DEFAULT 0.0")
    
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
    
    cursor.execute("UPDATE leave_balances SET cl=3, sl=3, pl=1, paid_leave=1 WHERE cl=12")
    
    conn.commit()
    conn.close()

init_db()

def parse_date_safe(date_str, fallback=date.today()):
    if not date_str or date_str == 'None' or date_str == '':
        return fallback
    try:
        return datetime.strptime(str(date_str), "%Y-%m-%d").date()
    except:
        return fallback

def display_pdf_preview(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="450" type="application/pdf" style="border: 1px solid #ddd; border-radius: 5px;"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def get_emp_leave_summary(emp_id):
    conn = get_db_connection()
    
    bal = pd.read_sql_query("SELECT * FROM leave_balances WHERE emp_id=?", conn, params=(emp_id,))
    if len(bal) == 0:
        total_cl, total_sl, total_pl, total_spl = 3, 3, 1, 1
    else:
        total_cl = bal.iloc[0]['cl']
        total_sl = bal.iloc[0]['sl']
        total_pl = bal.iloc[0]['pl']
        total_spl = bal.iloc[0]['paid_leave']

    approved_df = pd.read_sql_query("SELECT leave_type, from_date, to_date FROM leave_requests WHERE emp_id=? AND status='Approved'", conn, params=(emp_id,))
    pending_df = pd.read_sql_query("SELECT COUNT(*) as p_count FROM leave_requests WHERE emp_id=? AND status='Pending'", conn, params=(emp_id,))
    conn.close()

    used_cl, used_sl, used_pl, used_spl = 0, 0, 0, 0

    for _, row in approved_df.iterrows():
        try:
            d1 = datetime.strptime(row['from_date'], "%Y-%m-%d")
            d2 = datetime.strptime(row['to_date'], "%Y-%m-%d")
            num_days = (d2 - d1).days + 1
        except:
            num_days = 1
            
        ltype = str(row['leave_type'])
        if "Casual" in ltype or "CL" in ltype:
            used_cl += num_days
        elif "Sick" in ltype or "SL" in ltype:
            used_sl += num_days
        elif "Paid" in ltype or "PL" in ltype:
            used_pl += num_days
        else:
            used_spl += num_days

    return {
        "cl_rem": max(0, total_cl - used_cl),
        "sl_rem": max(0, total_sl - used_sl),
        "pl_rem": max(0, total_pl - used_pl),
        "spl_rem": max(0, total_spl - used_spl),
        "cl_tot": total_cl, "sl_tot": total_sl, "pl_tot": total_pl, "spl_tot": total_spl,
        "pending_count": pending_df.iloc[0]['p_count'] if len(pending_df) > 0 else 0
    }

def get_quick_stats():
    conn = get_db_connection()
    act = conn.execute("SELECT COUNT(*) FROM employees WHERE status='Active'").fetchone()[0]
    pend = conn.execute("SELECT COUNT(*) FROM leave_requests WHERE status='Pending'").fetchone()[0]
    conn.close()
    return act, pend

# ==============================================================================
# 3. DIALOGS
# ==============================================================================
@st.dialog("💵 Update Employee Salary", width="small")
def update_salary_dialog(emp_data):
    st.write(f"**Employee:** {emp_data['emp_name']} (`{emp_data['emp_id']}`)")
    st.write(f"**Department:** {emp_data['department'] or 'N/A'}")
    st.write(f"**Designation:** {emp_data['designation'] or 'N/A'}")
    st.markdown("---")
    
    current_sal = float(emp_data['salary']) if emp_data['salary'] else 0.0
    new_sal = st.number_input("Enter New Monthly Salary (₹)", value=current_sal, min_value=0.0, step=1000.0, format="%.2f")
    
    if st.button("💾 Save Salary Update", type="primary", use_container_width=True):
        if new_sal != current_sal:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor.execute("""
                INSERT INTO salary_history (emp_id, previous_salary, new_salary, updated_at)
                VALUES (?, ?, ?, ?)
            """, (emp_data['emp_id'], current_sal, new_sal, now_str))
            
            cursor.execute("UPDATE employees SET salary=? WHERE emp_id=?", (new_sal, emp_data['emp_id']))
            conn.commit()
            conn.close()
            st.toast("Salary updated & history saved!")
            st.rerun()
        else:
            st.info("Salary same hai, koi change nahi hua.")

@st.dialog("📜 Salary Revision History", width="large")
def view_salary_history_dialog(emp_data):
    st.markdown(f"### **{emp_data['emp_name']}** (`{emp_data['emp_id']}`)")
    st.caption(f"Current Salary: **₹{float(emp_data['salary'] or 0.0):,.2f}**")
    st.markdown("---")
    
    conn = get_db_connection()
    df_hist = pd.read_sql_query("SELECT previous_salary, new_salary, updated_at FROM salary_history WHERE emp_id=? ORDER BY id DESC", conn, params=(emp_data['emp_id'],))
    conn.close()
    
    if len(df_hist) == 0:
        st.info("Is employee ki abhi tak koi salary revision history nahi hai.")
    else:
        st.markdown("##### 📈 Past Salary Changes:")
        
        hist_ratios = [1.5, 1.5, 1.5, 1.5]
        th = st.columns(hist_ratios)
        headers = ["Date & Time", "Previous Salary", "New Salary", "Increment (₹)"]
        for idx, head in enumerate(headers):
            th[idx].markdown(f"<div class='admin-table-header'>{head}</div>", unsafe_allow_html=True)
            
        for _, h_row in df_hist.iterrows():
            tr = st.columns(hist_ratios)
            prev_s = float(h_row['previous_salary'])
            new_s = float(h_row['new_salary'])
            diff = new_s - prev_s
            
            tr[0].markdown(f"<div class='admin-table-row'>{h_row['updated_at']}</div>", unsafe_allow_html=True)
            tr[1].markdown(f"<div class='admin-table-row'>₹{prev_s:,.2f}</div>", unsafe_allow_html=True)
            tr[2].markdown(f"<div class='admin-table-row'><b style='color:#28a745;'>₹{new_s:,.2f}</b></div>", unsafe_allow_html=True)
            
            diff_color = "#28a745" if diff >= 0 else "#dc3545"
            diff_sign = "+" if diff >= 0 else ""
            tr[3].markdown(f"<div class='admin-table-row'><b style='color:{diff_color};'>{diff_sign}₹{diff:,.2f}</b></div>", unsafe_allow_html=True)

@st.dialog("👁️ View Employee Details", width="large")
def view_employee_dialog(emp_data):
    st.markdown(f"### **{emp_data['emp_name']}** (`{emp_data['emp_id']}`)")
    st.caption(f"Status: **{emp_data['status']}** | Location: **{emp_data['location'] or 'N/A'}**")
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**📌 Job & Salary Details**")
        st.write(f"- **Department:** {emp_data['department'] or 'N/A'}")
        st.write(f"- **Designation:** {emp_data['designation'] or 'N/A'}")
        st.write(f"- **Monthly Salary:** ₹{float(emp_data['salary'] or 0.0):,.2f}")
        st.write(f"- **Date of Joining (DOJ):** {emp_data['doj'] or 'N/A'}")
        st.write(f"- **Date of Exit (DOE):** {emp_data['doe'] or 'N/A'}")

        st.markdown("<br>**📞 Contact Details**", unsafe_allow_html=True)
        st.write(f"- **Mobile:** {emp_data['mobile'] or 'N/A'}")
        st.write(f"- **Office Email:** {emp_data['office_email'] or 'N/A'}")
        st.write(f"- **Personal Email:** {emp_data['personal_email'] or 'N/A'}")

    with c2:
        st.markdown("**🆔 Identity & Emergency**")
        st.write(f"- **Date of Birth (DOB):** {emp_data['dob'] or 'N/A'}")
        st.write(f"- **Aadhar Number:** {emp_data['aadhar'] or 'N/A'}")
        st.write(f"- **PAN Number:** {emp_data['pan'] or 'N/A'}")
        st.write(f"- **Emergency Contact:** {emp_data['emergency_name'] or 'N/A'} ({emp_data['emergency_contact'] or 'N/A'})")

        st.markdown("<br>**💻 Inventory & Assets**", unsafe_allow_html=True)
        st.write(f"- **Assigned Assets:** {emp_data['inventory_details'] or 'None'}")

    st.markdown("---")
    st.markdown("**📂 Uploaded Documents**")
    
    docs_raw = emp_data['documents_uploaded']
    try:
        current_docs = json.loads(docs_raw) if docs_raw else []
    except:
        current_docs = []

    if not current_docs:
        st.info("No documents uploaded for this employee.")
    else:
        for idx, doc in enumerate(current_docs):
            file_path = doc.get('path', '')
            file_name = doc.get('filename', 'file')
            doc_type = doc.get('type', 'Document')
            
            with st.expander(f"📄 {doc_type} - {file_name}"):
                if os.path.exists(file_path):
                    ext = os.path.splitext(file_name)[1].lower()
                    if ext in ['.png', '.jpg', '.jpeg']:
                        st.image(file_path, caption=file_name, use_column_width=True)
                    elif ext == '.pdf':
                        display_pdf_preview(file_path)
                    else:
                        st.caption(f"📁 Preview not supported for {ext} files.")
                    
                    with open(file_path, "rb") as f:
                        st.download_button("⬇️ Download File", data=f, file_name=file_name, key=f"view_dl_{emp_data['emp_id']}_{idx}")
                else:
                    st.error("File not found on server.")

@st.dialog("⚙️ Edit Employee Profile", width="large")
def edit_employee_dialog(emp_data):
    st.caption(f"Employee ID: **{emp_data['emp_id']}** | Name: **{emp_data['emp_name']}**")
    
    tab_edit, tab_docs = st.tabs(["✏️ Edit Profile & Assets", "📂 View & Manage Documents"])

    with tab_edit:
        with st.form("edit_modal_form"):
            st.markdown("##### 👤 Personal & Professional Info")
            c1, c2, c3 = st.columns(3)
            e_name = c1.text_input("Name *", value=emp_data['emp_name'])
            e_dept = c2.text_input("Department", value=emp_data['department'] or '')
            e_desig = c3.text_input("Designation", value=emp_data['designation'] or '')

            c4, c5, c6 = st.columns(3)
            e_status = c4.selectbox("Status", ["Active", "Inactive"], index=0 if emp_data['status']=='Active' else 1)
            e_mobile = c5.text_input("Mobile Number", value=emp_data['mobile'])
            e_location = c6.text_input("Location", value=emp_data['location'])

            c7, c8, c9 = st.columns(3)
            e_pemail = c7.text_input("Personal Email", value=emp_data['personal_email'])
            e_oemail = c8.text_input("Office Email", value=emp_data['office_email'])
            e_salary = c9.number_input("Monthly Salary (₹)", value=float(emp_data['salary'] or 0.0), step=1000.0)

            st.markdown("##### 🆔 Identity & Emergency Contact")
            c10, c11, c12, c13 = st.columns(4)
            e_aadhar = c10.text_input("Aadhar Number", value=emp_data['aadhar'])
            e_pan = c11.text_input("PAN Number", value=emp_data['pan'])
            e_emg_name = c12.text_input("Emergency Contact Person", value=emp_data['emergency_name'])
            e_emg_contact = c13.text_input("Emergency Contact Number", value=emp_data['emergency_contact'])

            st.markdown("##### 📅 Employment Dates")
            c14, c15, c16 = st.columns(3)
            e_dob = c14.date_input("Date of Birth (DOB)", value=parse_date_safe(emp_data['dob'], date(1998, 1, 19)))
            e_doj = c15.date_input("Date of Joining (DOJ)", value=parse_date_safe(emp_data['doj']))
            e_doe_str = c16.text_input("Date of Exit (DOE)", value=str(emp_data['doe']) if emp_data['doe'] and emp_data['doe']!='None' else "")

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
                old_salary = float(emp_data['salary'] or 0.0)
                if old_salary != e_salary:
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                    conn.cursor().execute("""
                        INSERT INTO salary_history (emp_id, previous_salary, new_salary, updated_at)
                        VALUES (?, ?, ?, ?)
                    """, (emp_data['emp_id'], old_salary, e_salary, now_str))

                conn.cursor().execute("""
                    UPDATE employees 
                    SET emp_name=?, department=?, designation=?, status=?, mobile=?, personal_email=?, office_email=?, location=?,
                        aadhar=?, pan=?, emergency_name=?, emergency_contact=?, dob=?, doj=?, doe=?, inventory_details=?, salary=?
                    WHERE emp_id=?
                """, (
                    e_name, e_dept, e_desig, e_status, e_mobile, e_pemail, e_oemail, e_location,
                    e_aadhar, e_pan, e_emg_name, e_emg_contact, str(e_dob), str(e_doj), e_doe_str, final_inv_str, e_salary,
                    emp_data['emp_id']
                ))
                conn.commit()
                conn.close()
                st.success("Sari details update ho gayi!")
                st.rerun()

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
                            st.caption(f"📁 Preview not supported for {ext} files.")
                        
                        st.write("")
                        btn_c1, btn_c2 = st.columns([1, 4])
                        with open(file_path, "rb") as f:
                            btn_c1.download_button("⬇️ Download File", data=f, file_name=file_name, key=f"dl_{emp_data['emp_id']}_{idx}", type="primary")
                        
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
            new_file = uc2.file_uploader("Choose File", type=['pdf', 'png', 'jpg', 'jpeg', 'docx'])
            
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
                    st.success("File upload ho gayi!")
                    st.rerun()

# ==============================================================================
# 4. ENHANCED SIDEBAR NAVIGATION & WIDGETS
# ==============================================================================
st.sidebar.markdown('<div class="sidebar-brand">👥 HUMAN RESOURCES</div>', unsafe_allow_html=True)

# User Profile Header
st.sidebar.markdown("""
    <div class="sidebar-user">
        <div style="width: 38px; height: 38px; border-radius: 50%; background-color: #00a65a; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white; font-size: 18px; border: 2px solid #fff;">
            A
        </div>
        <div>
            <div style="color:#ffffff; font-weight:600; font-size:15px; margin-bottom: 2px;">Welcome Admin</div>
            <div style="color:#00e676; font-size:12px; font-weight: bold;">● System Online</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Main Navigation Menu with High Contrast Readable Icons & Text
main_menu = st.sidebar.radio(
    "MAIN NAVIGATION",
    [
        "📊 Dashboard", 
        "➕ Add Employee", 
        "👥 Employee Master", 
        "🍃 Leave Tracker", 
        "📑 Leave Management", 
        "💵 Salary Management"
    ],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")

# Extra Widget 1: Live System Quick Stats
act_count, pend_count = get_quick_stats()
st.sidebar.markdown(f"""
    <div class="sidebar-widget">
        <div class="sidebar-widget-title">⚡ Quick System Overview</div>
        <div class="sidebar-stat-item">
            <span>Active Staff:</span>
            <b style="color:#00e676;">{act_count}</b>
        </div>
        <div class="sidebar-stat-item">
            <span>Pending Leaves:</span>
            <b style="color:#ffb74d;">{pend_count}</b>
        </div>
    </div>
""", unsafe_allow_html=True)

# Extra Widget 2: Live Clock & Date
st.sidebar.markdown(f"""
    <div class="sidebar-widget" style="border-left-color: #17a2b8;">
        <div class="sidebar-widget-title">📅 System Today</div>
        <div style="font-size: 13px; font-weight: 600; color: #ffffff;">
            {datetime.now().strftime("%A, %d %b %Y")}
        </div>
    </div>
""", unsafe_allow_html=True)

st.sidebar.write("")
if st.sidebar.button("🚪 Logout System", type="secondary", use_container_width=True):
    st.sidebar.success("Logged out safely!")

# ==============================================================================
# 5. PAGE ROUTING & LOGIC
# ==============================================================================
if "Dashboard" in main_menu:
    st.markdown("<h2 style='color:#333; font-weight:400;'>HR Dashboard</h2>", unsafe_allow_html=True)
    
    conn = get_db_connection()
    df_emp = pd.read_sql_query("SELECT * FROM employees", conn)
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

elif "Add Employee" in main_menu:
    st.markdown("<h2 style='color:#333; font-weight:400;'>Add New Employee Details</h2>", unsafe_allow_html=True)
    
    if "form_submitted_success" in st.session_state and st.session_state.form_submitted_success:
        st.toast("🎉 Employee successfully added!", icon="✅")
        st.session_state.form_submitted_success = False

    with st.form("add_emp_form", clear_on_submit=True):
        st.subheader("1. Basic & Contact Details")
        c1, c2, c3 = st.columns(3)
        emp_id = c1.text_input("Employee ID *", placeholder="e.g. VMPL19")
        emp_name = c2.text_input("Employee Name *", placeholder="Full Name")
        mobile = c3.text_input("Mobile Number", placeholder="10 Digit Number")
        
        c4, c5, c6 = st.columns(3)
        department = c4.text_input("Department", placeholder="e.g. IT, HR, Sales")
        designation = c5.text_input("Designation", placeholder="e.g. Software Engineer")
        location = c6.text_input("Work Location", value="Gurgaon")

        c7, c8, c9 = st.columns(3)
        personal_email = c7.text_input("Personal Email")
        office_email = c8.text_input("Office Email")
        salary = c9.number_input("Monthly Basic Salary (₹)", min_value=0.0, step=1000.0, placeholder="e.g. 35000")

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
                        (emp_id, emp_name, department, designation, status, mobile, personal_email, office_email, aadhar, pan, 
                         emergency_name, emergency_contact, location, doj, dob, doe, inventory_details, documents_uploaded, salary)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        emp_id, emp_name, department, designation, emp_status, mobile, personal_email, office_email, aadhar, pan,
                        emergency_name, emergency_contact, location, str(doj), str(dob), str(doe), final_inv, docs_str, salary
                    ))
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO leave_balances (emp_id, cl, sl, pl, paid_leave)
                        VALUES (?, 3, 3, 1, 1)
                    """, (emp_id,))

                    conn.commit()
                    st.session_state.form_submitted_success = True
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Employee ID pehle se registered hai!")
                finally:
                    conn.close()

elif "Employee Master" in main_menu:
    st.markdown("<h2 style='color:#333; font-weight:400;'>Employee Directory</h2>", unsafe_allow_html=True)
    
    conn = get_db_connection()
    df_all = pd.read_sql_query("SELECT * FROM employees", conn)
    conn.close()
    
    if len(df_all) == 0:
        st.info("Abhi koi employee record nahi hai.")
    else:
        search = st.text_input("🔍 Search Employee:", "", placeholder="Type name, ID, department or mobile...")
        if search:
            df_all = df_all[
                df_all['emp_name'].str.contains(search, case=False, na=False) |
                df_all['emp_id'].str.contains(search, case=False, na=False) |
                df_all['department'].str.contains(search, case=False, na=False) |
                df_all['designation'].str.contains(search, case=False, na=False)
            ]

        col_ratios = [1.0, 1.3, 1.2, 1.3, 1.0, 1.3, 0.9, 1.0, 1.3, 1.8]
        
        th_cols = st.columns(col_ratios)
        headers = ["Emp ID", "Name", "Department", "Designation", "Mobile", "Office Email", "DOJ", "Location", "Assets", "Tools / Actions"]
        for idx, head in enumerate(headers):
            th_cols[idx].markdown(f"<div class='admin-table-header'>{head}</div>", unsafe_allow_html=True)
        
        for idx, row in df_all.iterrows():
            tr_cols = st.columns(col_ratios)
            tr_cols[0].markdown(f"<div class='admin-table-row'><b>{row['emp_id']}</b></div>", unsafe_allow_html=True)
            tr_cols[1].markdown(f"<div class='admin-table-row'>{row['emp_name']}</div>", unsafe_allow_html=True)
            tr_cols[2].markdown(f"<div class='admin-table-row'>{row['department'] or '-'}</div>", unsafe_allow_html=True)
            tr_cols[3].markdown(f"<div class='admin-table-row'>{row['designation'] or '-'}</div>", unsafe_allow_html=True)
            tr_cols[4].markdown(f"<div class='admin-table-row'>{row['mobile'] or '-'}</div>", unsafe_allow_html=True)
            tr_cols[5].markdown(f"<div class='admin-table-row'>{row['office_email'] or '-'}</div>", unsafe_allow_html=True)
            tr_cols[6].markdown(f"<div class='admin-table-row'>{row['doj'] or '-'}</div>", unsafe_allow_html=True)
            tr_cols[7].markdown(f"<div class='admin-table-row'>{row['location'] or '-'}</div>", unsafe_allow_html=True)
            tr_cols[8].markdown(f"<div class='admin-table-row'>{row['inventory_details'] or '-'}</div>", unsafe_allow_html=True)
            
            act_col1, act_col2, act_col3 = tr_cols[9].columns(3)
            
            if act_col1.button("👁️ View", key=f"view_{row['emp_id']}"):
                view_employee_dialog(row)

            if act_col2.button("✏️ Edit", key=f"edit_{row['emp_id']}"):
                edit_employee_dialog(row)
            
            if act_col3.button("🗑️ Delete", key=f"del_{row['emp_id']}"):
                conn = get_db_connection()
                conn.cursor().execute("DELETE FROM employees WHERE emp_id=?", (row['emp_id'],))
                conn.commit()
                conn.close()
                st.toast("Employee deleted!")
                st.rerun()

elif "Leave Tracker" in main_menu:
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

        summary = get_emp_leave_summary(selected_emp['emp_id'])

        st.markdown(f"""
        <div style="background-color: #ffffff; padding: 15px; border-radius: 6px; border: 1px solid #e0e0e0; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <h5 style="margin:0; color:#333; font-weight:600;">📊 Live Leave Balance for {selected_emp['emp_name']} ({selected_emp['emp_id']})</h5>
            <hr style="margin: 8px 0 12px 0;">
            <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                <div>🟢 Casual Leave (CL): <b style="color:#28a745; font-size:16px;">{summary['cl_rem']}</b> / {summary['cl_tot']} Left</div>
                <div>🔵 Sick Leave (SL): <b style="color:#17a2b8; font-size:16px;">{summary['sl_rem']}</b> / {summary['sl_tot']} Left</div>
                <div>🟣 Paid Leave (PL): <b style="color:#6f42c1; font-size:16px;">{summary['pl_rem']}</b> / {summary['pl_tot']} Left</div>
                <div>⏳ Pending Approvals: <b style="color:#dc3545; font-size:16px;">{summary['pending_count']} Request(s)</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if days_completed < 90:
            st.error(f"⚠️ **Not Eligible:** Joining < 90 days. (Completed: {days_completed} days)")
        else:
            with st.form("apply_leave_form", clear_on_submit=True):
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
                    st.toast("Leave Request submitted!")
                    st.rerun()

elif "Leave Management" in main_menu:
    st.markdown("<h2 style='color:#333; font-weight:400;'>Leave Management</h2>", unsafe_allow_html=True)
    
    conn = get_db_connection()
    df_requests = pd.read_sql_query("""
        SELECT l.id, l.emp_id, e.emp_name, l.leave_type, l.from_date, l.to_date, l.reason, l.status
        FROM leave_requests l
        LEFT JOIN employees e ON l.emp_id = e.emp_id
        ORDER BY l.id DESC
    """, conn)
    
    df_pending_summary = pd.read_sql_query("""
        SELECT e.emp_id, e.emp_name, COUNT(l.id) as pending_leaves
        FROM employees e
        LEFT JOIN leave_requests l ON e.emp_id = l.emp_id AND l.status = 'Pending'
        GROUP BY e.emp_id
        HAVING pending_leaves > 0
    """, conn)
    conn.close()
    
    st.markdown("##### 📌 Pending Leave Requests Summary")
    if len(df_pending_summary) > 0:
        p_cols = st.columns(min(len(df_pending_summary), 4))
        for idx, p_row in df_pending_summary.iterrows():
            with p_cols[idx % 4]:
                st.markdown(f"""
                <div style="background-color: #fff3cd; border: 1px solid #ffeeba; border-radius: 5px; padding: 10px; margin-bottom: 10px;">
                    <div style="font-size: 13px; font-weight: bold; color: #856404;">{p_row['emp_name']} ({p_row['emp_id']})</div>
                    <div style="font-size: 18px; font-weight: bold; color: #d9534f;">{p_row['pending_leaves']} Pending Leave(s)</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.success("🎉 Sabhi leave requests reviewed hain!")

    st.write("")
    st.markdown("##### 📜 All Leave Requests")
    
    if len(df_requests) == 0:
        st.info("Koi leave request record nahi hai.")
    else:
        for idx, row in df_requests.iterrows():
            status_color = "#f39c12" if row['status'] == 'Pending' else ("#28a745" if row['status'] == 'Approved' else "#dc3545")
            emp_summary = get_emp_leave_summary(row['emp_id'])
            
            with st.expander(f"👤 {row['emp_name'] or 'Unknown'} ({row['emp_id']}) — {row['leave_type']} [{row['status']}]", expanded=(row['status'] == 'Pending')):
                c1, c2, c3 = st.columns([2, 2, 2])
                with c1:
                    st.write(f"**From Date:** {row['from_date']}")
                    st.write(f"**To Date:** {row['to_date']}")
                    st.write(f"**Reason:** {row['reason'] or 'N/A'}")
                with c2:
                    st.markdown(f"**Status:** <span style='color:{status_color}; font-weight:bold;'>{row['status']}</span>", unsafe_allow_html=True)
                
                with c3:
                    st.markdown(f"""
                    <div style="background-color:#f8f9fa; padding:8px 12px; border-radius:4px; border-left:3px solid #17a2b8; font-size:12px;">
                        <b>💰 Current Leave Balance:</b><br>
                        • CL Remaining: <b>{emp_summary['cl_rem']} / {emp_summary['cl_tot']}</b><br>
                        • SL Remaining: <b>{emp_summary['sl_rem']} / {emp_summary['sl_tot']}</b><br>
                        • PL Remaining: <b>{emp_summary['pl_rem']} / {emp_summary['pl_tot']}</b>
                    </div>
                    """, unsafe_allow_html=True)

                st.write("")
                btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
                
                if row['status'] == 'Pending':
                    if btn_col1.button("✅ Approve", key=f"app_{row['id']}"):
                        conn = get_db_connection()
                        conn.cursor().execute("UPDATE leave_requests SET status='Approved' WHERE id=?", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.toast("Approved!")
                        st.rerun()
                        
                    if btn_col2.button("❌ Reject", key=f"rej_{row['id']}"):
                        conn = get_db_connection()
                        conn.cursor().execute("UPDATE leave_requests SET status='Rejected' WHERE id=?", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.toast("Rejected!")
                        st.rerun()

                if btn_col3.button("🗑️ Delete Request", key=f"del_req_{row['id']}"):
                    conn = get_db_connection()
                    conn.cursor().execute("DELETE FROM leave_requests WHERE id=?", (row['id'],))
                    conn.commit()
                    conn.close()
                    st.toast("Deleted!")
                    st.rerun()

elif "Salary Management" in main_menu:
    st.markdown("<h2 style='color:#333; font-weight:400;'>Employee Salary Details</h2>", unsafe_allow_html=True)
    
    conn = get_db_connection()
    df_sal = pd.read_sql_query("SELECT emp_id, emp_name, department, designation, salary FROM employees", conn)
    conn.close()
    
    if len(df_sal) == 0:
        st.info("Abhi koi employee record nahi hai.")
    else:
        sal_search = st.text_input("🔍 Search Salary Records:", "", placeholder="Type Name, Emp Code, Department or Designation...")
        if sal_search:
            df_sal = df_sal[
                df_sal['emp_name'].str.contains(sal_search, case=False, na=False) |
                df_sal['emp_id'].str.contains(sal_search, case=False, na=False) |
                df_sal['department'].str.contains(sal_search, case=False, na=False) |
                df_sal['designation'].str.contains(sal_search, case=False, na=False)
            ]

        sal_col_ratios = [1.2, 2.0, 1.8, 1.8, 1.5, 2.0]
        th_cols = st.columns(sal_col_ratios)
        headers = ["Emp Code", "Name", "Department", "Designation", "Current Salary (₹)", "Actions / Tools"]
        for idx, head in enumerate(headers):
            th_cols[idx].markdown(f"<div class='admin-table-header'>{head}</div>", unsafe_allow_html=True)
        
        for idx, row in df_sal.iterrows():
            tr_cols = st.columns(sal_col_ratios)
            tr_cols[0].markdown(f"<div class='admin-table-row'><b>{row['emp_id']}</b></div>", unsafe_allow_html=True)
            tr_cols[1].markdown(f"<div class='admin-table-row'>{row['emp_name']}</div>", unsafe_allow_html=True)
            tr_cols[2].markdown(f"<div class='admin-table-row'>{row['department'] or '-'}</div>", unsafe_allow_html=True)
            tr_cols[3].markdown(f"<div class='admin-table-row'>{row['designation'] or '-'}</div>", unsafe_allow_html=True)
            
            sal_val = float(row['salary']) if row['salary'] else 0.0
            tr_cols[4].markdown(f"<div class='admin-table-row'><b style='color:#28a745;'>₹{sal_val:,.2f}</b></div>", unsafe_allow_html=True)
            
            act1, act2 = tr_cols[5].columns(2)
            
            if act1.button("👁️ View", key=f"salhist_{row['emp_id']}"):
                view_salary_history_dialog(row)

            if act2.button("✏️ Update", key=f"sal_{row['emp_id']}"):
                update_salary_dialog(row)
