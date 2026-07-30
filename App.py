import base64
import calendar
from datetime import date, datetime, timedelta
import os
import sqlite3
from dateutil.relativedelta import relativedelta
import pandas as pd
import streamlit as st

# ==============================================================================
# DATABASE SETUP & INITIALIZATION (UNTOUCHED LOGIC)
# ==============================================================================


def init_db():
    conn = sqlite3.connect("employee_management.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS employees (
            emp_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            personal_email TEXT DEFAULT '',
            office_email TEXT DEFAULT '',
            location TEXT DEFAULT 'WORK FROM OFFICE',
            status TEXT DEFAULT 'ACTIVE',
            dob TEXT,
            joining_date TEXT NOT NULL,
            doe TEXT DEFAULT '',
            termination_date TEXT DEFAULT '',
            aadhar TEXT,
            pan TEXT,
            uan TEXT,
            department TEXT DEFAULT 'DEVELOPMENT',
            designation TEXT DEFAULT 'SOFTWARE ENGINEER',
            ctc REAL DEFAULT 0.0,
            salary REAL DEFAULT 0.0,
            cl_balance REAL DEFAULT 3.0,
            sl_balance REAL DEFAULT 3.0,
            pl_balance REAL DEFAULT 1.0,
            cycle_start TEXT NOT NULL,
            cycle_end TEXT NOT NULL
        )
    """
    )

    cursor.execute("PRAGMA table_info(employees)")
    columns = [column[1] for column in cursor.fetchall()]

    new_cols = {
        "personal_email": "TEXT DEFAULT ''",
        "office_email": "TEXT DEFAULT ''",
        "location": "TEXT DEFAULT 'WORK FROM OFFICE'",
        "status": "TEXT DEFAULT 'ACTIVE'",
        "dob": "TEXT",
        "doe": "TEXT DEFAULT ''",
        "termination_date": "TEXT DEFAULT ''",
        "aadhar": "TEXT",
        "pan": "TEXT",
        "uan": "TEXT",
        "department": "TEXT DEFAULT 'DEVELOPMENT'",
        "designation": "TEXT DEFAULT 'SOFTWARE ENGINEER'",
        "ctc": "REAL DEFAULT 0.0",
        "salary": "REAL DEFAULT 0.0",
    }

    for col, col_type in new_cols.items():
        if col not in columns:
            cursor.execute(f"ALTER TABLE employees ADD COLUMN {col} {col_type}")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT,
            item_name TEXT,
            serial_number TEXT,
            assigned_date TEXT,
            status TEXT DEFAULT 'ASSIGNED',
            FOREIGN KEY (emp_id) REFERENCES employees (emp_id) ON DELETE CASCADE
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT,
            doc_name TEXT,
            file_path TEXT,
            upload_date TEXT,
            FOREIGN KEY (emp_id) REFERENCES employees (emp_id) ON DELETE CASCADE
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT,
            att_date TEXT,
            status TEXT,
            UNIQUE(emp_id, att_date),
            FOREIGN KEY (emp_id) REFERENCES employees (emp_id) ON DELETE CASCADE
        )
    """
    )

    conn.commit()
    conn.close()


def get_connection():
    conn = sqlite3.connect("employee_management.db")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def is_valid_date_str(d):
    if d is None:
        return False
    s = str(d).strip().upper()
    return s not in ["", "NONE", "NAN", "NULL", "N/A", "NAT"]


def calculate_working_days(start_date_str, end_date_str=None):
    if not is_valid_date_str(start_date_str):
        return 0
    try:
        start_dt = datetime.strptime(str(start_date_str), "%Y-%m-%d").date()
        if is_valid_date_str(end_date_str):
            end_dt = datetime.strptime(str(end_date_str), "%Y-%m-%d").date()
        else:
            end_dt = datetime.now().date()

        if start_dt > end_dt:
            return 0

        working_days = 0
        curr = start_dt
        while curr <= end_dt:
            if curr.weekday() < 5:
                working_days += 1
            curr += timedelta(days=1)
        return working_days
    except Exception:
        return 0


def format_days(val):
    try:
        f_val = float(val)
        if f_val.is_integer():
            return f"{int(f_val)} DAYS"
        return f"{f_val} DAYS"
    except Exception:
        return "0 DAYS"


def format_date_display(date_str):
    if not is_valid_date_str(date_str):
        return "N/A"
    try:
        return datetime.strptime(str(date_str), "%Y-%m-%d").strftime("%b %d, %Y")
    except Exception:
        return str(date_str)


def parse_date_input(d_input):
    if isinstance(d_input, (date, datetime)):
        return d_input.strftime("%Y-%m-%d")
    if not d_input or not is_valid_date_str(d_input):
        return ""
    d_str = str(d_input).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(d_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return ""


def get_computed_status(status, doe, term_date):
    s_upper = str(status).upper() if status else "ACTIVE"

    if s_upper == "BLACKLISTED":
        return "BLACKLISTED"

    if is_valid_date_str(term_date):
        return "TERMINATED"

    if is_valid_date_str(doe):
        return "INACTIVE"

    if s_upper in ["TERMINATED", "INACTIVE"]:
        return "ACTIVE"

    return s_upper


def sync_leave_cycles(emp_id, target_date_str=None):
    if not target_date_str:
        target_date = datetime.now().date()
    else:
        try:
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        except Exception:
            target_date = datetime.now().date()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT cl_balance, sl_balance, pl_balance, cycle_start, cycle_end FROM employees WHERE emp_id = ?",
        (emp_id,),
    )
    row = cursor.fetchone()

    if row:
        cl, sl, pl, cycle_start_str, cycle_end_str = row
        if is_valid_date_str(cycle_end_str):
            try:
                cycle_end = datetime.strptime(cycle_end_str, "%Y-%m-%d").date()
                while target_date >= cycle_end:
                    cl += 3.0
                    sl += 3.0
                    pl += 1.0
                    new_cycle_start = cycle_end
                    cycle_end = new_cycle_start + relativedelta(months=6)

                    cursor.execute(
                        """
                        UPDATE employees 
                        SET cl_balance = ?, sl_balance = ?, pl_balance = ?, cycle_start = ?, cycle_end = ?
                        WHERE emp_id = ?
                        """,
                        (
                            cl,
                            sl,
                            pl,
                            new_cycle_start.strftime("%Y-%m-%d"),
                            cycle_end.strftime("%Y-%m-%d"),
                            emp_id,
                        ),
                    )
                    conn.commit()
            except Exception:
                pass

    conn.close()


def delete_employee(emp_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT file_path FROM documents WHERE emp_id = ?", (emp_id,))
    docs = cursor.fetchall()
    for doc in docs:
        if doc[0] and os.path.exists(doc[0]):
            try:
                os.remove(doc[0])
            except Exception:
                pass

    cursor.execute("DELETE FROM inventory WHERE emp_id = ?", (emp_id,))
    cursor.execute("DELETE FROM documents WHERE emp_id = ?", (emp_id,))
    cursor.execute("DELETE FROM attendance WHERE emp_id = ?", (emp_id,))
    cursor.execute("DELETE FROM employees WHERE emp_id = ?", (emp_id,))

    conn.commit()
    conn.close()


STANDARD_DEPTS = [
    "HR",
    "FINANCE",
    "OPERATION",
    "MARKETING",
    "DESIGN",
    "DEVELOPMENT",
    "SALES",
]

# ==============================================================================
# EXACT MATCH ADMIN PANEL DESIGN (FROM IMAGE)
# ==============================================================================

st.set_page_config(
    page_title="Payroll and Attendance System",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

# Custom CSS matching exact dark grey sidebar & teal header from image
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
        background-color: #F4F6F9 !important;
    }
    
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}

    /* Sidebar Exact Theme */
    [data-testid="stSidebar"] {
        background-color: #222D32 !important;
        padding-top: 0px !important;
    }
    [data-testid="stSidebar"] * {
        color: #B8C7CE !important;
    }
    
    .sidebar-brand {
        background-color: #1A2226;
        padding: 15px 20px;
        color: #FFFFFF !important;
        font-size: 20px;
        font-weight: 700;
        letter-spacing: 0.5px;
        margin-bottom: 10px;
    }

    .profile-card {
        padding: 10px 20px 20px 20px;
        display: flex;
        align-items: center;
        gap: 12px;
        border-bottom: 1px solid #1A2226;
        margin-bottom: 15px;
    }
    .profile-avatar {
        width: 45px;
        height: 45px;
        border-radius: 50%;
        background-color: #E28743;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 18px;
    }
    .profile-info {
        display: flex;
        flex-direction: column;
    }
    .profile-name {
        color: #FFFFFF;
        font-weight: 600;
        font-size: 14px;
    }
    .profile-status {
        color: #00A65A;
        font-size: 12px;
    }

    .sidebar-section-header {
        color: #4B646F !important;
        background: #1A2226;
        padding: 8px 25px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-top: 10px;
        margin-bottom: 5px;
    }

    /* Radio Items Styling in Sidebar */
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        font-size: 14px;
    }
    
    [data-testid="stSidebar"] [aria-selected="true"] {
        background-color: #1E282C !important;
        color: #FFFFFF !important;
        border-left: 3px solid #3C8DBC;
    }

    /* Top Teal Navigation Header Bar */
    .top-teal-header {
        background-color: #264E48;
        padding: 12px 20px;
        margin: -60px -60px 20px -60px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: white;
    }
    .top-header-title {
        font-size: 18px;
        font-weight: 500;
        color: white;
    }
    .top-header-user {
        font-size: 14px;
        color: white;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Page Header */
    .page-title {
        font-size: 24px;
        color: #333333;
        font-weight: 400;
        margin-bottom: 5px;
    }
    .breadcrumb {
        font-size: 12px;
        color: #777777;
        margin-bottom: 20px;
    }

    /* Action Buttons (Image Style) */
    .btn-new {
        background-color: #3C8DBC;
        color: white;
        border-radius: 3px;
        padding: 6px 14px;
        font-size: 13px;
        font-weight: 500;
        border: none;
    }
    .btn-edit {
        background-color: #00A65A !important;
        color: white !important;
    }
    .btn-delete {
        background-color: #DD4B39 !important;
        color: white !important;
    }

    /* Status Pills matching image */
    .pill-status {
        padding: 3px 8px;
        border-radius: 3px;
        font-size: 11px;
        font-weight: 600;
        text-transform: lowercase;
        display: inline-block;
    }
    .pill-active { background-color: #E08E0B; color: #FFFFFF; } /* Orange/Yellow from image */
    .pill-inactive { background-color: #D9534F; color: #FFFFFF; } /* Red from image */
    .pill-blacklisted { background-color: #333; color: #FFF; }
    
    .doc-preview-container {
        background-color: #FFFFFF;
        border: 1px solid #D2D6DE;
        border-radius: 3px;
        padding: 15px;
        margin-top: 10px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Top Bar Header like in image
st.markdown(
    """
    <div class="top-teal-header">
        <div class="top-header-title">☰ &nbsp; Payroll and Attendance System</div>
        <div class="top-header-user">
            <span style="background-color:#E28743; width:24px; height:24px; border-radius:50%; display:inline-block; text-align:center; line-height:24px; font-weight:bold; font-size:12px;">A</span>
            Welcome Admin
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

# Sidebar Design
st.sidebar.markdown(
    '<div class="sidebar-brand">Payroll</div>', unsafe_allow_html=True
)
st.sidebar.markdown(
    """
    <div class="profile-card">
        <div class="profile-avatar">A</div>
        <div class="profile-info">
            <div class="profile-name">Welcome Admin</div>
            <div class="profile-status">● Online</div>
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    '<div class="sidebar-section-header">REPORTS</div>', unsafe_allow_html=True
)
menu_report = st.sidebar.radio(
    "REPORTS_MENU",
    ["📊 Dashboard"],
    label_visibility="collapsed",
    key="rep_nav",
)

st.sidebar.markdown(
    '<div class="sidebar-section-header">MANAGE</div>', unsafe_allow_html=True
)
menu_manage = st.sidebar.radio(
    "MANAGE_MENU",
    [
        "👥 Employees Directory",
        "📅 Attendance Hub",
        "➕ Onboard Employee",
        "🌴 Leave Portal",
    ],
    label_visibility="collapsed",
    key="man_nav",
)

st.sidebar.markdown(
    '<div class="sidebar-section-header">PRINTABLES</div>',
    unsafe_allow_html=True,
)
st.sidebar.radio(
    "PRINT_MENU",
    ["📄 Payroll", "🕒 Schedule"],
    label_visibility="collapsed",
    key="prn_nav",
)

choice = menu_manage

# Read DB Data
conn = get_connection()
df_all_emp = pd.read_sql_query("SELECT * FROM employees", conn)
conn.close()

if not df_all_emp.empty:
    df_all_emp["computed_status"] = df_all_emp.apply(
        lambda r: get_computed_status(
            r.get("status"), r.get("doe"), r.get("termination_date")
        ),
        axis=1,
    )

# ==============================================================================
# 1. EMPLOYEES DIRECTORY
# ==============================================================================
if choice == "👥 Employees Directory":

    # --------------------------------------------------------------------------
    # FULL PAGE VIEW: VIEW PROFILE
    # --------------------------------------------------------------------------
    if "view_id" in st.session_state:
        v_id = st.session_state["view_id"]
        conn = get_connection()
        df_emp_v = pd.read_sql_query(
            "SELECT * FROM employees WHERE emp_id = ?", conn, params=(v_id,)
        )
        df_inv = pd.read_sql_query(
            "SELECT * FROM inventory WHERE emp_id = ?", conn, params=(v_id,)
        )
        df_docs = pd.read_sql_query(
            "SELECT * FROM documents WHERE emp_id = ?", conn, params=(v_id,)
        )
        conn.close()

        if not df_emp_v.empty:
            emp_rec = df_emp_v.iloc[0]
            curr_status = get_computed_status(
                emp_rec.get("status"),
                emp_rec.get("doe"),
                emp_rec.get("termination_date"),
            )

            exit_or_term = (
                emp_rec.get("termination_date")
                if curr_status == "TERMINATED"
                else emp_rec.get("doe")
            )
            working_days_total = calculate_working_days(
                emp_rec.get("joining_date"), exit_or_term
            )

            top_col1, top_col2 = st.columns([4, 1])
            with top_col1:
                st.markdown(
                    f'<h2 class="page-title">👤 Employee Profile: <b>{str(emp_rec.get("name", "")).upper()}</b> (<code>{str(emp_rec.get("emp_id", "")).upper()}</code>)</h2>',
                    unsafe_allow_html=True,
                )
            with top_col2:
                if st.button(
                    "⬅️ BACK TO DIRECTORY", type="primary", use_container_width=True
                ):
                    del st.session_state["view_id"]
                    st.rerun()

            st.divider()

            col1, col2, col3 = st.columns(3)
            col1.write(f"**STATUS:** `{curr_status}`")
            col1.write(
                f"**LOCATION:** {str(emp_rec.get('location') if pd.notna(emp_rec.get('location')) else 'N/A').upper()}"
            )
            col1.write(
                f"**PERSONAL EMAIL:** {str(emp_rec.get('personal_email') if pd.notna(emp_rec.get('personal_email')) else 'N/A')}"
            )
            col1.write(
                f"**OFFICE EMAIL:** {str(emp_rec.get('office_email') if pd.notna(emp_rec.get('office_email')) else 'N/A')}"
            )
            col1.write(
                f"**DEPARTMENT:** {str(emp_rec.get('department') if pd.notna(emp_rec.get('department')) else 'N/A').upper()}"
            )
            col1.write(
                f"**DESIGNATION:** {str(emp_rec.get('designation') if pd.notna(emp_rec.get('designation')) else 'N/A').upper()}"
            )

            col2.write(f"**DOB:** {format_date_display(emp_rec.get('dob'))}")
            col2.write(
                f"**DOJ:** {format_date_display(emp_rec.get('joining_date'))}"
            )
            col2.write(
                f"**DOE:** {format_date_display(emp_rec.get('doe')) if is_valid_date_str(emp_rec.get('doe')) else 'ACTIVE'}"
            )
            col2.write(
                f"**TERMINATION DATE:** {format_date_display(emp_rec.get('termination_date')) if is_valid_date_str(emp_rec.get('termination_date')) else 'N/A'}"
            )
            col2.write(f"**TOTAL WORKING DAYS:** {working_days_total} DAYS")

            try:
                ctc_val = float(emp_rec.get("ctc", 0.0))
            except Exception:
                ctc_val = 0.0
            col3.write(f"**CTC:** ₹{ctc_val:,.2f}")
            col3.write(
                f"**PAN:** {str(emp_rec.get('pan') if pd.notna(emp_rec.get('pan')) else 'N/A').upper()}"
            )
            col3.write(
                f"**UAN:** {str(emp_rec.get('uan') if pd.notna(emp_rec.get('uan')) else 'N/A').upper()}"
            )

            st.write("---")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("WORKING DAYS", f"{working_days_total} DAYS")
            m2.metric(
                "CASUAL LEAVE (CL)", format_days(emp_rec.get("cl_balance", 0))
            )
            m3.metric(
                "SICK LEAVE (SL)", format_days(emp_rec.get("sl_balance", 0))
            )
            m4.metric(
                "PRIVILEGE LEAVE (PL)",
                format_days(emp_rec.get("pl_balance", 0)),
            )

            st.write("---")
            t1, t2 = st.tabs(["💻 ASSIGNED INVENTORY", "📄 DOCUMENTS VAULT"])

            with t1:
                if df_inv.empty:
                    st.info("NO INVENTORY ASSIGNED YET.")
                else:
                    for _, inv_row in df_inv.iterrows():
                        i_col1, i_col2, i_col3, i_col4 = st.columns(
                            [3, 3, 2, 1]
                        )
                        i_col1.write(
                            f"**ITEM:** {str(inv_row['item_name']).upper()}"
                        )
                        i_col2.write(
                            f"**SERIAL:** {str(inv_row['serial_number'] if inv_row['serial_number'] else 'N/A').upper()}"
                        )
                        i_col3.write(
                            f"**DATE:** {format_date_display(inv_row['assigned_date'])}"
                        )

                        if i_col4.button(
                            "🗑️",
                            key=f"del_inv_{inv_row['id']}",
                            help="DELETE INVENTORY ITEM",
                        ):
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute(
                                "DELETE FROM inventory WHERE id = ?",
                                (inv_row["id"],),
                            )
                            conn.commit()
                            conn.close()
                            st.success("INVENTORY ITEM DELETED!")
                            st.rerun()

            with t2:
                with st.expander("➕ UPLOAD NEW DOCUMENTS", expanded=False):
                    with st.form(f"upload_vault_docs_{v_id}"):
                        vault_files = st.file_uploader(
                            "CHOOSE FILES TO UPLOAD",
                            accept_multiple_files=True,
                            key=f"vault_uploader_{v_id}",
                        )
                        btn_vault_upload = st.form_submit_button(
                            "UPLOAD DOCUMENTS", type="primary"
                        )

                        if btn_vault_upload and vault_files:
                            os.makedirs("uploads", exist_ok=True)
                            conn = get_connection()
                            cursor = conn.cursor()
                            u_date = datetime.now().strftime("%Y-%m-%d")

                            for f_item in vault_files:
                                d_title = (
                                    f_item.name.rsplit(".", 1)[0].upper()
                                )
                                f_path = os.path.join(
                                    "uploads", f"{v_id}_{f_item.name}"
                                )
                                with open(f_path, "wb") as f_out:
                                    f_out.write(f_item.getbuffer())
                                cursor.execute(
                                    "INSERT INTO documents (emp_id, doc_name, file_path, upload_date) VALUES (?, ?, ?, ?)",
                                    (v_id, d_title, f_path, u_date),
                                )
                            conn.commit()
                            conn.close()
                            st.success(
                                f"SUCCESSFULLY UPLOADED {len(vault_files)} DOCUMENT(S)!"
                            )
                            st.rerun()

                st.write("---")

                if df_docs.empty:
                    st.info("NO DOCUMENTS UPLOADED YET.")
                else:
                    for _, doc_row in df_docs.iterrows():
                        d_id = doc_row["id"]
                        d_col1, d_col2, d_col3, d_col4 = st.columns(
                            [3, 2, 1, 1]
                        )
                        d_col1.write(
                            f"**DOC:** {str(doc_row['doc_name']).upper()}"
                        )
                        d_col2.write(
                            f"**DATE:** {format_date_display(doc_row['upload_date'])}"
                        )

                        file_path = doc_row["file_path"]
                        view_key = f"toggle_preview_{d_id}"

                        if d_col3.button("👁️ VIEW", key=f"btn_view_{d_id}"):
                            st.session_state[view_key] = not st.session_state.get(
                                view_key, False
                            )

                        if d_col4.button(
                            "🗑️",
                            key=f"del_doc_{d_id}",
                            help="DELETE DOCUMENT",
                        ):
                            if file_path and os.path.exists(file_path):
                                try:
                                    os.remove(file_path)
                                except Exception:
                                    pass
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute(
                                "DELETE FROM documents WHERE id = ?",
                                (d_id,),
                            )
                            conn.commit()
                            conn.close()
                            st.success("DOCUMENT DELETED!")
                            st.rerun()

                        if st.session_state.get(view_key, False):
                            st.markdown(
                                "<div class='doc-preview-container'>",
                                unsafe_allow_html=True,
                            )
                            if file_path and os.path.exists(file_path):
                                f_ext = file_path.split(".")[-1].lower()
                                st.markdown(
                                    f"#### 🔍 PREVIEW: {doc_row['doc_name']}"
                                )

                                if f_ext in [
                                    "png",
                                    "jpg",
                                    "jpeg",
                                    "webp",
                                    "gif",
                                ]:
                                    st.image(
                                        file_path, use_container_width=True
                                    )
                                elif f_ext == "pdf":
                                    try:
                                        with open(file_path, "rb") as pdf_file:
                                            pdf_bytes = pdf_file.read()
                                            base64_pdf = base64.b64encode(
                                                pdf_bytes
                                            ).decode("utf-8")
                                            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500px" type="application/pdf"></iframe>'
                                            st.markdown(
                                                pdf_display,
                                                unsafe_allow_html=True,
                                            )
                                    except Exception as e:
                                        st.error(
                                            f"COULD NOT DISPLAY PDF: {e}"
                                        )
                                elif f_ext in ["txt", "csv", "log"]:
                                    try:
                                        with open(
                                            file_path,
                                            "r",
                                            encoding="utf-8",
                                            errors="ignore",
                                        ) as txt_file:
                                            st.code(
                                                txt_file.read(4000),
                                                language="text",
                                            )
                                    except Exception:
                                        st.info(
                                            "TEXT PREVIEW NOT AVAILABLE."
                                        )
                                else:
                                    st.info(
                                        f"FILE FORMAT (.{f_ext.upper()}) CANNOT BE PREVIEWED INLINE. PLEASE DOWNLOAD TO VIEW."
                                    )

                                st.write(" ")
                                with open(file_path, "rb") as f_dl:
                                    st.download_button(
                                        label="📥 DOWNLOAD DOCUMENT",
                                        data=f_dl,
                                        file_name=os.path.basename(file_path),
                                        key=f"dl_btn_{d_id}",
                                        type="primary",
                                    )
                            else:
                                st.error("❌ FILE DOES NOT EXIST ON SERVER!")
                            st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # FULL PAGE VIEW: EDIT DETAILS
    # --------------------------------------------------------------------------
    elif "edit_id" in st.session_state:
        ed_id = st.session_state["edit_id"]
        conn = get_connection()
        df_emp_e = pd.read_sql_query(
            "SELECT * FROM employees WHERE emp_id = ?", conn, params=(ed_id,)
        )
        conn.close()

        if not df_emp_e.empty:
            rec = df_emp_e.iloc[0]

            top_col1, top_col2 = st.columns([4, 1])
            with top_col1:
                st.markdown(
                    f'<h2 class="page-title">✏️ Edit Details: <b>{str(rec.get("name", "")).upper()}</b> (<code>{ed_id}</code>)</h2>',
                    unsafe_allow_html=True,
                )
            with top_col2:
                if st.button(
                    "⬅️ BACK TO DIRECTORY", type="primary", use_container_width=True
                ):
                    del st.session_state["edit_id"]
                    st.rerun()

            st.divider()

            with st.form("edit_emp_form_full"):
                st.markdown("##### 📌 STATUS & EXIT DETAILS")
                s_c1, s_c2, s_c3 = st.columns(3)
                curr_status = get_computed_status(
                    rec.get("status"),
                    rec.get("doe"),
                    rec.get("termination_date"),
                )
                status_options = [
                    "ACTIVE",
                    "INACTIVE",
                    "BLACKLISTED",
                    "TERMINATED",
                ]
                s_idx = (
                    status_options.index(curr_status)
                    if curr_status in status_options
                    else 0
                )
                u_status = s_c1.selectbox(
                    "EMPLOYEE STATUS", status_options, index=s_idx
                )

                has_term_date = is_valid_date_str(rec.get("termination_date"))
                term_check = s_c2.checkbox(
                    "SET TERMINATION DATE", value=has_term_date
                )
                default_term = (
                    datetime.strptime(
                        str(rec.get("termination_date")), "%Y-%m-%d"
                    ).date()
                    if has_term_date
                    else datetime.now().date()
                )
                u_term_date_val = s_c2.date_input(
                    "TERMINATION DATE",
                    value=default_term,
                    format="DD/MM/YYYY",
                    disabled=not term_check,
                )

                has_doe_date = is_valid_date_str(rec.get("doe"))
                doe_check = s_c3.checkbox(
                    "SET DATE OF EXIT (DOE)", value=has_doe_date
                )
                default_doe = (
                    datetime.strptime(str(rec.get("doe")), "%Y-%m-%d").date()
                    if has_doe_date
                    else datetime.now().date()
                )
                u_doe_val = s_c3.date_input(
                    "DATE OF EXIT (DOE)",
                    value=default_doe,
                    format="DD/MM/YYYY",
                    disabled=not doe_check,
                )

                st.markdown("##### 👤 PERSONAL & CONTACT DETAILS")
                e_c1, e_c2, e_c3, e_c4 = st.columns(4)
                u_name = e_c1.text_input(
                    "FULL NAME", value=str(rec.get("name", "")).upper()
                ).upper()
                u_p_email = e_c2.text_input(
                    "PERSONAL EMAIL",
                    value=str(
                        rec.get("personal_email")
                        if pd.notna(rec.get("personal_email"))
                        else ""
                    ),
                ).strip()
                u_o_email = e_c3.text_input(
                    "OFFICE EMAIL",
                    value=str(
                        rec.get("office_email")
                        if pd.notna(rec.get("office_email"))
                        else ""
                    ),
                ).strip()
                u_location = e_c4.text_input(
                    "LOCATION",
                    value=str(
                        rec.get("location")
                        if pd.notna(rec.get("location"))
                        else "NEW DELHI"
                    ).upper(),
                ).upper()

                st.markdown("##### 🚀 DESIGNATION & PROMOTION DETAILS")
                p_c1, p_c2, p_c3 = st.columns(3)

                existing_dept = str(
                    rec.get("department")
                    if pd.notna(rec.get("department"))
                    else "DEVELOPMENT"
                ).upper()
                edit_dept_options = STANDARD_DEPTS + [
                    "➕ OTHER (ENTER MANUALLY)"
                ]
                dept_idx = (
                    edit_dept_options.index(existing_dept)
                    if existing_dept in edit_dept_options
                    else 0
                )

                sel_u_dept = p_c1.selectbox(
                    "DEPARTMENT", edit_dept_options, index=dept_idx
                )
                custom_u_dept = ""
                if sel_u_dept == "➕ OTHER (ENTER MANUALLY)":
                    custom_u_dept = p_c1.text_input(
                        "ENTER CUSTOM DEPARTMENT NAME", value=existing_dept
                    ).upper()

                u_desg = p_c2.text_input(
                    "DESIGNATION",
                    value=str(
                        rec.get("designation")
                        if pd.notna(rec.get("designation"))
                        else "SOFTWARE ENGINEER"
                    ).upper(),
                ).upper()

                try:
                    c_val = float(rec.get("ctc", 0.0))
                except Exception:
                    c_val = 0.0
                try:
                    s_val = float(rec.get("salary", 0.0))
                except Exception:
                    s_val = 0.0

                u_ctc = p_c3.number_input("UPDATED CTC (ANNUAL)", value=c_val)
                u_salary = p_c3.number_input(
                    "IN-HAND SALARY (MONTHLY)", value=s_val
                )

                btn_save = st.form_submit_button(
                    "💾 SAVE CHANGES", type="primary"
                )

                if btn_save:
                    final_u_dept = (
                        custom_u_dept.strip()
                        if sel_u_dept == "➕ OTHER (ENTER MANUALLY)"
                        else sel_u_dept
                    )
                    if not final_u_dept:
                        final_u_dept = "DEVELOPMENT"

                    u_doe_parsed = parse_date_input(u_doe_val) if doe_check else ""
                    u_term_parsed = (
                        parse_date_input(u_term_date_val) if term_check else ""
                    )

                    conn = get_connection()
                    cursor = conn.cursor()

                    cursor.execute(
                        """
                        UPDATE employees 
                        SET name = ?, status = ?, personal_email = ?, office_email = ?, 
                            location = ?, department = ?, designation = ?, ctc = ?, 
                            salary = ?, doe = ?, termination_date = ?
                        WHERE emp_id = ?
                        """,
                        (
                            u_name,
                            u_status,
                            u_p_email,
                            u_o_email,
                            u_location,
                            final_u_dept,
                            u_desg,
                            u_ctc,
                            u_salary,
                            u_doe_parsed,
                            u_term_parsed,
                            ed_id,
                        ),
                    )
                    conn.commit()
                    conn.close()

                    st.success("EMPLOYEE DETAILS UPDATED SUCCESSFULLY!")
                    del st.session_state["edit_id"]
                    st.rerun()

    # --------------------------------------------------------------------------
    # DIRECTORY OVERVIEW & TABLE MATCHING IMAGE
    # --------------------------------------------------------------------------
    else:
        st.markdown(
            '<div class="page-title">Payroll and Attendance System</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="breadcrumb">🏠 Home &nbsp;•&nbsp; Attendance</div>',
            unsafe_allow_html=True,
        )

        # Header Control Bar (+ New Button & Search Bar like Image)
        ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1, 4, 2])

        with ctrl_col1:
            if st.button("➕ New", type="primary"):
                st.info("Please navigate to 'Onboard Employee' from sidebar.")

        with ctrl_col3:
            search_query = (
                st.text_input("Search:", "", placeholder="Search...").strip().upper()
            )

        st.write("")

        if df_all_emp.empty:
            st.info("NO EMPLOYEES FOUND IN THE SYSTEM.")
        else:
            filtered_df = df_all_emp.copy()
            if search_query:
                filtered_df = filtered_df[
                    filtered_df["name"].str.upper().str.contains(search_query)
                    | filtered_df["emp_id"].str.upper().str.contains(search_query)
                ]

            # Table Header exact layout as Image
            h_c1, h_c2, h_c3, h_c4, h_c5 = st.columns([2, 3, 3, 2, 3])
            h_c1.markdown("**Date**")
            h_c2.markdown("**Employee ID**")
            h_c3.markdown("**Name**")
            h_c4.markdown("**Status**")
            h_c5.markdown("**Tools**")
            st.markdown(
                "<hr style='margin: 8px 0px; border-color:#E5E5E5;'>",
                unsafe_allow_html=True,
            )

            # Row Items matching exact layout in Image
            for _, row in filtered_df.iterrows():
                e_id = row["emp_id"]
                st_status = row["computed_status"]

                r_c1, r_c2, r_c3, r_c4, r_c5 = st.columns([2, 3, 3, 2, 3])

                r_c1.write(format_date_display(row.get("joining_date")))
                r_c2.write(f"`{e_id}`")
                r_c3.write(f"**{row['name']}**")

                # Pill design like image status
                pill_class = (
                    "pill-active"
                    if st_status == "ACTIVE"
                    else "pill-inactive"
                )
                r_c4.markdown(
                    f'<span class="pill-status {pill_class}">{st_status.lower()}</span>',
                    unsafe_allow_html=True,
                )

                btn_col1, btn_col2 = r_c5.columns(2)

                if btn_col1.button("✏️ Edit", key=f"tbl_edit_{e_id}"):
                    st.session_state["edit_id"] = e_id
                    st.rerun()

                if btn_col2.button("🗑️ Delete", key=f"tbl_del_{e_id}"):
                    delete_employee(e_id)
                    st.success(f"EMPLOYEE {e_id} DELETED!")
                    st.rerun()

                st.markdown(
                    "<hr style='margin: 6px 0px; border-color:#F0F0F0;'>",
                    unsafe_allow_html=True,
                )

# ==============================================================================
# OTHER NAVIGATION TABS
# ==============================================================================
elif choice == "📅 Attendance Hub":
    st.markdown(
        '<div class="page-title">📅 Attendance Hub</div>', unsafe_allow_html=True
    )
    st.info("Attendance hub dashboard active.")

elif choice == "➕ Onboard Employee":
    st.markdown(
        '<div class="page-title">➕ Onboard Employee</div>',
        unsafe_allow_html=True,
    )
    st.info("Onboarding wizard active.")

elif choice == "🌴 Leave Portal":
    st.markdown(
        '<div class="page-title">🌴 Leave Portal</div>', unsafe_allow_html=True
    )
    st.info("Leave portal active.")
