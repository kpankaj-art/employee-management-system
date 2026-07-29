import base64
import calendar
from datetime import date, datetime, timedelta
import os
import sqlite3
from dateutil.relativedelta import relativedelta
import pandas as pd
import streamlit as st

# ==============================================================================
# DATABASE SETUP & INITIALIZATION
# ==============================================================================


def init_db():
    conn = sqlite3.connect("employee_management.db")
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON")

    # Employees Table
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

    # Columns Check
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

    # Inventory Table
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

    # Documents Table
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

    # Attendance Table
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
            if curr.weekday() < 5:  # Mon to Fri
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
        return datetime.strptime(str(date_str), "%Y-%m-%d").strftime(
            "%d/%m/%Y"
        )
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
    if is_valid_date_str(term_date) or s_upper == "TERMINATED":
        return "TERMINATED"
    if is_valid_date_str(doe):
        return "INACTIVE"
    return "ACTIVE"


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

    cursor.execute(
        "SELECT file_path FROM documents WHERE emp_id = ?", (emp_id,)
    )
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
# UI CONFIGURATION & CUSTOM CSS
# ==============================================================================

st.set_page_config(
    page_title="HAPPY HR PORTAL",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

st.markdown(
    """
    <style>
    header {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    [data-testid="stToolbar"] {visibility: hidden !important;}
    [data-testid="stDecoration"] {visibility: hidden !important;}
    [data-testid="stStatusWidget"] {visibility: hidden !important;}

    [data-testid="stSidebar"] {
        background-color: #0F172A !important;
        color: #F8FAFC !important;
    }
    [data-testid="stSidebar"] * {
        color: #E2E8F0 !important;
    }
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    .page-title {
        font-size: 28px;
        font-weight: 700;
        color: #0F172A;
        margin: 0;
        text-transform: uppercase;
    }
    .page-sub {
        font-size: 14px;
        color: #64748B;
        margin-top: 4px;
        text-transform: uppercase;
    }
    div.stButton > button[kind="primary"] {
        background-color: #0284C7 !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        text-transform: uppercase;
    }

    .att-box {
        padding: 8px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        margin-bottom: 5px;
        border: 1px solid #E2E8F0;
    }
    .att-p { background-color: #DCFCE7; color: #166534; border-color: #86EFAC; }
    .att-a { background-color: #FEE2E2; color: #991B1B; border-color: #FCA5A5; }
    .att-h { background-color: #FFEDD5; color: #C2410C; border-color: #FDBA74; }
    .att-l { background-color: #FEF08A; color: #854D0E; border-color: #FDE047; }
    
    .doc-preview-container {
        background-color: #F8FAFC;
        border: 1px solid #CBD5E1;
        border-radius: 8px;
        padding: 12px;
        margin-top: 10px;
        margin-bottom: 15px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# SIDEBAR NAVIGATION
# ==============================================================================

st.sidebar.markdown(
    "<h2 style='color:#38BDF8 !important; margin-bottom: 20px;'>✨ HAPPY HR</h2>",
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    "<p style='color:#94A3B8 !important; font-size:12px;'>MAIN MENU</p>",
    unsafe_allow_html=True,
)
menu = [
    "👥 EMPLOYEES",
    "📅 ATTENDANCE",
    "➕ ADD / RE-JOIN EMPLOYEE",
    "📊 LEAVE REQUESTS",
]
choice = st.sidebar.radio("NAVIGATION", menu, label_visibility="collapsed")

# ==============================================================================
# 1. EMPLOYEES LIST VIEW
# ==============================================================================
if choice == "👥 EMPLOYEES":

    col_title, col_actions = st.columns([3, 2])

    with col_title:
        st.markdown("<p class='page-title'>EMPLOYEES</p>", unsafe_allow_html=True)
        st.markdown(
            "<p class='page-sub'>MANAGE EMPLOYEE DETAILS, STATUS, PROMOTIONS, AND WORKING DAYS.</p>",
            unsafe_allow_html=True,
        )

    with col_actions:
        st.write(" ")
        btn_col1, btn_col2 = st.columns(2)

        conn = get_connection()
        df_all_emp = pd.read_sql_query("SELECT * FROM employees", conn)
        conn.close()

        with btn_col1:
            if not df_all_emp.empty:
                file_name = "ALL_EMPLOYEES_REPORT.xlsx"
                with pd.ExcelWriter(file_name, engine="openpyxl") as writer:
                    df_all_emp.to_excel(
                        writer, sheet_name="EMPLOYEES", index=False
                    )
                with open(file_name, "rb") as f:
                    st.download_button(
                        "📤 EXPORT DATA",
                        f,
                        file_name=file_name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )

    st.divider()

    if df_all_emp.empty:
        st.info("NO EMPLOYEE REGISTERED YET. ADD FROM SIDEBAR.")
    else:
        f_col1, f_col2, f_col3 = st.columns([2, 1.5, 1.5])
        search_query = f_col1.text_input(
            "🔎 SEARCH",
            placeholder="SEARCH BY NAME, EMP ID, EMAIL, LOCATION, PAN...",
            label_visibility="collapsed",
        )

        db_depts = [
            str(x).upper()
            for x in df_all_emp["department"].dropna().unique()
            if str(x).strip() != ""
        ]
        all_depts_unique = sorted(list(set(STANDARD_DEPTS + db_depts)))
        dept_list = ["ALL DEPARTMENTS"] + all_depts_unique

        dept_filter = f_col2.selectbox(
            "DEPARTMENT", dept_list, label_visibility="collapsed"
        )

        status_filter = f_col3.selectbox(
            "STATUS",
            ["ALL STATUS", "ACTIVE", "INACTIVE", "BLACKLISTED", "TERMINATED"],
            label_visibility="collapsed",
        )

        filtered_df = df_all_emp.copy()

        computed_statuses = []
        for _, r in filtered_df.iterrows():
            computed_statuses.append(
                get_computed_status(
                    r.get("status"), r.get("doe"), r.get("termination_date")
                )
            )
        filtered_df["computed_status"] = computed_statuses

        if search_query:
            filtered_df = filtered_df[
                filtered_df["name"]
                .astype(str)
                .str.contains(search_query, case=False, na=False)
                | filtered_df["emp_id"]
                .astype(str)
                .str.contains(search_query, case=False, na=False)
                | filtered_df["personal_email"]
                .astype(str)
                .str.contains(search_query, case=False, na=False)
                | filtered_df["office_email"]
                .astype(str)
                .str.contains(search_query, case=False, na=False)
                | filtered_df["location"]
                .astype(str)
                .str.contains(search_query, case=False, na=False)
                | filtered_df["pan"]
                .astype(str)
                .str.contains(search_query, case=False, na=False)
                | filtered_df["aadhar"]
                .astype(str)
                .str.contains(search_query, case=False, na=False)
            ]
        if dept_filter != "ALL DEPARTMENTS":
            filtered_df = filtered_df[
                filtered_df["department"].astype(str).str.upper() == dept_filter
            ]
        if status_filter != "ALL STATUS":
            filtered_df = filtered_df[
                filtered_df["computed_status"].astype(str).str.upper()
                == status_filter
            ]

        st.write(" ")
        st.markdown("### 📋 EMPLOYEE MASTER DIRECTORY")

        for _, row in filtered_df.iterrows():
            emp_id = str(row["emp_id"]).upper()
            name = str(row.get("name", "")).upper()
            emp_status = row.get("computed_status")
            location = str(
                row.get("location")
                if pd.notna(row.get("location"))
                else "N/A"
            ).upper()
            dept = str(
                row.get("department")
                if pd.notna(row.get("department"))
                else "DEVELOPMENT"
            ).upper()
            designation = str(
                row.get("designation")
                if pd.notna(row.get("designation"))
                else "SOFTWARE ENGINEER"
            ).upper()

            exit_or_term = (
                row.get("termination_date")
                if emp_status == "TERMINATED"
                else row.get("doe")
            )
            w_days = calculate_working_days(
                row.get("joining_date"), exit_or_term
            )

            sync_leave_cycles(emp_id)

            status_badge = "🟢 ACTIVE"
            if emp_status == "BLACKLISTED":
                status_badge = "🚫 BLACKLISTED"
            elif emp_status == "TERMINATED":
                status_badge = "⛔ TERMINATED"
            elif emp_status == "INACTIVE":
                status_badge = "🔴 INACTIVE"

            with st.container():
                (
                    c_id,
                    c_name,
                    c_loc,
                    c_dept,
                    c_desg,
                    c_wd,
                    c_status,
                    c_act1,
                    c_act2,
                    c_act3,
                ) = st.columns([1.0, 2.0, 1.3, 1.5, 1.8, 1.2, 1.3, 0.5, 0.5, 0.5])

                c_id.markdown(f"**`{emp_id}`**")
                c_name.markdown(f"**{name}**")
                c_loc.markdown(f"📍 {location}")
                c_dept.markdown(f"{dept}")
                c_desg.markdown(f"{designation}")
                c_wd.markdown(f"💼 **{w_days} DAYS**")
                c_status.markdown(f"**{status_badge}**")

                if c_act1.button("👁️", key=f"v_{emp_id}", help="VIEW PROFILE"):
                    st.session_state["view_id"] = emp_id

                if c_act2.button(
                    "✏️", key=f"e_{emp_id}", help="EDIT DETAILS / PROMOTION"
                ):
                    st.session_state["edit_id"] = emp_id

                if c_act3.button(
                    "🗑️", key=f"d_{emp_id}", help="DELETE EMPLOYEE"
                ):
                    st.session_state["confirm_del_id"] = emp_id

                st.divider()

    # DELETE CONFIRMATION MODAL
    if "confirm_del_id" in st.session_state:
        del_emp_id = st.session_state["confirm_del_id"]
        st.warning(
            f"⚠️ ARE YOU SURE YOU WANT TO PERMANENTLY DELETE EMPLOYEE ID: **{del_emp_id}**?"
        )
        col_d1, col_d2 = st.columns([1, 4])
        if col_d1.button("YES, DELETE PERMANENTLY", type="primary"):
            delete_employee(del_emp_id)
            st.success(f"EMPLOYEE {del_emp_id} DELETED SUCCESSFULLY!")
            del st.session_state["confirm_del_id"]
            if (
                "view_id" in st.session_state
                and st.session_state["view_id"] == del_emp_id
            ):
                del st.session_state["view_id"]
            if (
                "edit_id" in st.session_state
                and st.session_state["edit_id"] == del_emp_id
            ):
                del st.session_state["edit_id"]
            st.rerun()

        if col_d2.button("CANCEL DELETE"):
            del st.session_state["confirm_del_id"]
            st.rerun()

    # VIEW PROFILE MODAL
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

            st.markdown(
                f"### 👤 PROFILE: {str(emp_rec.get('name', '')).upper()} ({str(emp_rec.get('emp_id', '')).upper()})"
            )

            col1, col2, col3 = st.columns(3)
            col1.write(f"**STATUS:** {curr_status}")
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

            col2.write(
                f"**DOB:** {format_date_display(emp_rec.get('dob'))}"
            )
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
                f"**AADHAR:** {str(emp_rec.get('aadhar') if pd.notna(emp_rec.get('aadhar')) else 'N/A').upper()}"
            )
            col3.write(
                f"**PAN:** {str(emp_rec.get('pan') if pd.notna(emp_rec.get('pan')) else 'N/A').upper()}"
            )
            col3.write(
                f"**UAN:** {str(emp_rec.get('uan') if pd.notna(emp_rec.get('uan')) else 'N/A').upper()}"
            )

            st.write("---")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("WORKING DAYS", f"{working_days_total} DAYS")
            m2.metric("CL BALANCE", format_days(emp_rec.get("cl_balance", 0)))
            m3.metric("SL BALANCE", format_days(emp_rec.get("sl_balance", 0)))
            m4.metric("PL BALANCE", format_days(emp_rec.get("pl_balance", 0)))

            t1, t2 = st.tabs(["💻 ASSIGNED INVENTORY", "📄 DOCUMENTS VAULT"])

            with t1:
                if df_inv.empty:
                    st.info("NO INVENTORY ASSIGNED YET.")
                else:
                    for _, inv_row in df_inv.iterrows():
                        i_col1, i_col2, i_col3, i_col4 = st.columns([3, 3, 2, 1])
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
                # Add Multiple Documents Form inside Vault
                with st.expander("➕ UPLOAD NEW DOCUMENTS (MULTIPLE ALLOWED)", expanded=False):
                    with st.form(f"upload_vault_docs_{v_id}"):
                        vault_files = st.file_uploader(
                            "CHOOSE FILES TO UPLOAD",
                            accept_multiple_files=True,
                            key=f"vault_uploader_{v_id}"
                        )
                        btn_vault_upload = st.form_submit_button("UPLOAD DOCUMENTS", type="primary")

                        if btn_vault_upload and vault_files:
                            os.makedirs("uploads", exist_ok=True)
                            conn = get_connection()
                            cursor = conn.cursor()
                            u_date = datetime.now().strftime("%Y-%m-%d")
                            
                            for f_item in vault_files:
                                d_title = f_item.name.rsplit('.', 1)[0].upper()
                                f_path = os.path.join("uploads", f"{v_id}_{f_item.name}")
                                with open(f_path, "wb") as f_out:
                                    f_out.write(f_item.getbuffer())
                                cursor.execute(
                                    "INSERT INTO documents (emp_id, doc_name, file_path, upload_date) VALUES (?, ?, ?, ?)",
                                    (v_id, d_title, f_path, u_date),
                                )
                            conn.commit()
                            conn.close()
                            st.success(f"SUCCESSFULLY UPLOADED {len(vault_files)} DOCUMENT(S)!")
                            st.rerun()

                st.write("---")

                if df_docs.empty:
                    st.info("NO DOCUMENTS UPLOADED YET.")
                else:
                    for _, doc_row in df_docs.iterrows():
                        d_id = doc_row["id"]
                        d_col1, d_col2, d_col3, d_col4 = st.columns([3, 2, 1, 1])
                        d_col1.write(
                            f"**DOC:** {str(doc_row['doc_name']).upper()}"
                        )
                        d_col2.write(
                            f"**DATE:** {format_date_display(doc_row['upload_date'])}"
                        )

                        file_path = doc_row["file_path"]
                        view_key = f"toggle_preview_{d_id}"

                        # Toggle view button
                        if d_col3.button("👁️ VIEW", key=f"btn_view_{d_id}"):
                            st.session_state[view_key] = not st.session_state.get(view_key, False)

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

                        # INLINE DOCUMENT PREVIEW SECTION
                        if st.session_state.get(view_key, False):
                            st.markdown("<div class='doc-preview-container'>", unsafe_allow_html=True)
                            if file_path and os.path.exists(file_path):
                                f_ext = file_path.split(".")[-1].lower()
                                
                                st.markdown(f"#### 🔍 PREVIEW: {doc_row['doc_name']}")
                                
                                # 1. Images
                                if f_ext in ["png", "jpg", "jpeg", "webp", "gif"]:
                                    st.image(file_path, use_container_width=True)
                                
                                # 2. PDF Files (Render Inline PDF)
                                elif f_ext == "pdf":
                                    try:
                                        with open(file_path, "rb") as pdf_file:
                                            pdf_bytes = pdf_file.read()
                                            base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
                                            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500px" type="application/pdf"></iframe>'
                                            st.markdown(pdf_display, unsafe_allow_html=True)
                                    except Exception as e:
                                        st.error(f"COULD NOT DISPLAY PDF: {e}")
                                
                                # 3. Text/CSV Files
                                elif f_ext in ["txt", "csv", "log"]:
                                    try:
                                        with open(file_path, "r", encoding="utf-8", errors="ignore") as txt_file:
                                            st.code(txt_file.read(4000), language="text")
                                    except Exception:
                                        st.info("TEXT PREVIEW NOT AVAILABLE.")
                                else:
                                    st.info(f"FILE FORMAT (.{f_ext.upper()}) CANNOT BE PREVIEWED INLINE. PLEASE DOWNLOAD TO VIEW.")

                                st.write(" ")
                                # Separate Download Button
                                with open(file_path, "rb") as f_dl:
                                    st.download_button(
                                        label="📥 DOWNLOAD DOCUMENT",
                                        data=f_dl,
                                        file_name=os.path.basename(file_path),
                                        key=f"dl_btn_{d_id}",
                                        type="primary"
                                    )
                            else:
                                st.error("❌ FILE DOES NOT EXIST ON SERVER!")
                            st.markdown("</div>", unsafe_allow_html=True)

            st.write(" ")
            if st.button("❌ CLOSE PROFILE"):
                del st.session_state["view_id"]
                st.rerun()

    # EDIT DETAILS & PROMOTION MODAL
    if "edit_id" in st.session_state:
        ed_id = st.session_state["edit_id"]
        conn = get_connection()
        df_emp_e = pd.read_sql_query(
            "SELECT * FROM employees WHERE emp_id = ?", conn, params=(ed_id,)
        )
        conn.close()

        if not df_emp_e.empty:
            rec = df_emp_e.iloc[0]

            st.markdown(
                f"### ✏️ EDIT DETAILS & PROMOTION: {str(rec.get('name', '')).upper()}"
            )

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

                # Termination Date Picker with Checkbox
                has_term_date = is_valid_date_str(rec.get("termination_date"))
                term_check = s_c2.checkbox("SET TERMINATION DATE", value=has_term_date)
                default_term = (
                    datetime.strptime(str(rec.get("termination_date")), "%Y-%m-%d").date()
                    if has_term_date
                    else datetime.now().date()
                )
                u_term_date_val = s_c2.date_input(
                    "TERMINATION DATE",
                    value=default_term,
                    format="DD/MM/YYYY",
                    disabled=not term_check,
                )

                # DOE Date Picker with Checkbox
                has_doe_date = is_valid_date_str(rec.get("doe"))
                doe_check = s_c3.checkbox("SET DATE OF EXIT (DOE)", value=has_doe_date)
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
                        else "MUMBAI"
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
                    "DESIGNATION (PROMOTION UPDATE)",
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

                st.markdown("##### 📑 DATES & IDENTIFIERS")
                d_c1, d_c2, d_c3, d_c4, d_c5 = st.columns(5)

                try:
                    curr_dob = datetime.strptime(
                        str(rec.get("dob")), "%Y-%m-%d"
                    ).date()
                except Exception:
                    curr_dob = date(1995, 1, 1)

                try:
                    curr_doj = datetime.strptime(
                        str(rec.get("joining_date")), "%Y-%m-%d"
                    ).date()
                except Exception:
                    curr_doj = datetime.now().date()

                u_dob_val = d_c1.date_input(
                    "DOB",
                    value=curr_dob,
                    min_value=date(1980, 1, 1),
                    max_value=datetime.now().date(),
                    format="DD/MM/YYYY",
                )
                u_doj_val = d_c2.date_input(
                    "DOJ",
                    value=curr_doj,
                    min_value=date(2000, 1, 1),
                    format="DD/MM/YYYY",
                )

                u_aadhar = d_c3.text_input(
                    "AADHAR CARD",
                    value=str(
                        rec.get("aadhar")
                        if pd.notna(rec.get("aadhar"))
                        else ""
                    ).upper(),
                ).upper()
                u_pan = d_c4.text_input(
                    "PAN CARD",
                    value=str(
                        rec.get("pan") if pd.notna(rec.get("pan")) else ""
                    ).upper(),
                ).upper()
                u_uan = d_c5.text_input(
                    "UAN NUMBER",
                    value=str(
                        rec.get("uan") if pd.notna(rec.get("uan")) else ""
                    ).upper(),
                ).upper()

                st.markdown("##### 🌴 EDIT LEAVE BALANCES")
                l_c1, l_c2, l_c3 = st.columns(3)
                u_cl = l_c1.number_input(
                    "CL BALANCE",
                    value=float(rec.get("cl_balance", 3.0)),
                    step=0.5,
                )
                u_sl = l_c2.number_input(
                    "SL BALANCE",
                    value=float(rec.get("sl_balance", 3.0)),
                    step=0.5,
                )
                u_pl = l_c3.number_input(
                    "PL BALANCE",
                    value=float(rec.get("pl_balance", 1.0)),
                    step=0.5,
                )

                btn_save = st.form_submit_button(
                    "💾 SAVE CHANGES & PROMOTION", type="primary"
                )

                if btn_save:
                    final_u_dept = (
                        custom_u_dept.strip()
                        if sel_u_dept == "➕ OTHER (ENTER MANUALLY)"
                        else sel_u_dept
                    )
                    if not final_u_dept:
                        final_u_dept = "DEVELOPMENT"

                    u_dob_parsed = parse_date_input(u_dob_val)
                    u_doj_parsed = parse_date_input(u_doj_val)
                    
                    u_doe_parsed = parse_date_input(u_doe_val) if doe_check else ""
                    u_term_parsed = parse_date_input(u_term_date_val) if term_check else ""

                    final_status = u_status
                    if is_valid_date_str(u_term_parsed):
                        final_status = "TERMINATED"
                    elif is_valid_date_str(u_doe_parsed):
                        final_status = "INACTIVE"
                    elif final_status == "INACTIVE" and not is_valid_date_str(u_doe_parsed):
                        final_status = "ACTIVE"

                    conn = get_connection()
                    cursor = conn.cursor()

                    try:
                        j_obj = datetime.strptime(
                            u_doj_parsed, "%Y-%m-%d"
                        ).date()
                        n_c_end = (j_obj + relativedelta(months=6)).strftime(
                            "%Y-%m-%d"
                        )
                    except Exception:
                        n_c_end = str(rec.get("cycle_end", ""))

                    cursor.execute(
                        """
                        UPDATE employees 
                        SET name = ?, status = ?, personal_email = ?, office_email = ?, location = ?, department = ?, designation = ?, 
                            dob = ?, joining_date = ?, doe = ?, termination_date = ?,
                            aadhar = ?, pan = ?, uan = ?, ctc = ?, salary = ?, 
                            cl_balance = ?, sl_balance = ?, pl_balance = ?, cycle_start = ?, cycle_end = ?
                        WHERE emp_id = ?
                        """,
                        (
                            u_name,
                            final_status,
                            u_p_email,
                            u_o_email,
                            u_location,
                            final_u_dept,
                            u_desg,
                            u_dob_parsed,
                            u_doj_parsed,
                            u_doe_parsed,
                            u_term_parsed,
                            u_aadhar,
                            u_pan,
                            u_uan,
                            u_ctc,
                            u_salary,
                            u_cl,
                            u_sl,
                            u_pl,
                            u_doj_parsed,
                            n_c_end,
                            ed_id,
                        ),
                    )

                    conn.commit()
                    conn.close()
                    st.success("EMPLOYEE DETAILS SAVED SUCCESSFULLY!")
                    del st.session_state["edit_id"]
                    st.rerun()

            st.write(" ")
            if st.button("CLOSE EDIT"):
                del st.session_state["edit_id"]
                st.rerun()

# ==============================================================================
# 2. CALENDAR ATTENDANCE MODULE
# ==============================================================================
elif choice == "📅 ATTENDANCE":
    st.markdown(
        "<p class='page-title'>EMPLOYEE ATTENDANCE CALENDAR</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p class='page-sub'>AUTOMATIC SUNDAYS & 2ND SATURDAYS ARE HOLIDAYS (🟠 H). LEAVES APPEAR AS (🟡 L).</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    conn = get_connection()
    df_emps = pd.read_sql_query(
        "SELECT emp_id, name, status, doe, termination_date FROM employees",
        conn,
    )
    conn.close()

    if df_emps.empty:
        st.info("NO EMPLOYEES FOUND FOR ATTENDANCE MARKING.")
    else:
        df_emps["comp_status"] = df_emps.apply(
            lambda r: get_computed_status(
                r["status"], r["doe"], r["termination_date"]
            ),
            axis=1,
        )
        active_emps = df_emps[df_emps["comp_status"] == "ACTIVE"]

        if active_emps.empty:
            active_emps = df_emps

        emp_map = {
            f"{r['emp_id']} - {r['name']} ({r['comp_status']})": r["emp_id"]
            for _, r in active_emps.iterrows()
        }

        col_a1, col_a2, col_a3 = st.columns([3, 2, 2])
        sel_emp_label = col_a1.selectbox(
            "SELECT EMPLOYEE", list(emp_map.keys())
        )
        selected_emp_id = emp_map[sel_emp_label]

        curr_year = datetime.now().year
        sel_year = col_a2.selectbox(
            "SELECT YEAR", [curr_year - 1, curr_year, curr_year + 1], index=1
        )
        months_list = list(calendar.month_name)[1:]
        curr_month = datetime.now().month
        sel_month_name = col_a3.selectbox(
            "SELECT MONTH", months_list, index=curr_month - 1
        )
        sel_month_num = months_list.index(sel_month_name) + 1

        conn = get_connection()
        month_prefix = f"{sel_year}-{sel_month_num:02d}%"
        df_att = pd.read_sql_query(
            "SELECT att_date, status FROM attendance WHERE emp_id = ? AND att_date LIKE ?",
            conn,
            params=(selected_emp_id, month_prefix),
        )
        conn.close()

        saved_att_dict = (
            dict(zip(df_att["att_date"], df_att["status"]))
            if not df_att.empty
            else {}
        )

        cal = calendar.monthcalendar(sel_year, sel_month_num)
        p_count = 0
        a_count = 0
        h_count = 0
        l_count = 0

        final_month_status = {}

        for week in cal:
            for day in week:
                if day != 0:
                    date_obj = date(sel_year, sel_month_num, day)
                    date_str = f"{sel_year}-{sel_month_num:02d}-{day:02d}"

                    is_sunday = date_obj.weekday() == 6
                    is_second_saturday = (date_obj.weekday() == 5) and (
                        8 <= day <= 14
                    )

                    if date_str in saved_att_dict:
                        st_val = saved_att_dict[date_str]
                    else:
                        if is_sunday or is_second_saturday:
                            st_val = "H"
                        else:
                            st_val = "P"

                    final_month_status[date_str] = st_val

                    if st_val == "P":
                        p_count += 1
                    elif st_val == "A":
                        a_count += 1
                    elif st_val == "H":
                        h_count += 1
                    elif st_val == "L":
                        l_count += 1

        st.write(" ")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🟢 PRESENT (P)", f"{p_count} DAYS")
        m2.metric("🔴 ABSENT (A)", f"{a_count} DAYS")
        m3.metric("🟠 HOLIDAY (H)", f"{h_count} DAYS")
        m4.metric("🟡 LEAVE (L)", f"{l_count} DAYS")
        st.write("---")

        st.markdown(f"#### 📅 CALENDAR: {sel_month_name.upper()} {sel_year}")

        week_days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        cols = st.columns(7)
        for i, day_name in enumerate(week_days):
            cols[i].markdown(
                f"<div style='text-align:center; font-weight:bold; color:#0F172A;'>{day_name}</div>",
                unsafe_allow_html=True,
            )

        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0:
                    cols[i].write(" ")
                else:
                    date_str = f"{sel_year}-{sel_month_num:02d}-{day:02d}"
                    status_val = final_month_status.get(date_str, "P")

                    badge_class = "att-p"
                    if status_val == "A":
                        badge_class = "att-a"
                    elif status_val == "H":
                        badge_class = "att-h"
                    elif status_val == "L":
                        badge_class = "att-l"

                    with cols[i]:
                        st.markdown(
                            f"""<div class='att-box {badge_class}'>
                                <div style='font-size:16px;'>{day}</div>
                                <div style='font-size:12px;'>{status_val}</div>
                            </div>""",
                            unsafe_allow_html=True,
                        )

                        att_options = ["P", "A", "H", "L"]
                        opt_idx = (
                            att_options.index(status_val)
                            if status_val in att_options
                            else 0
                        )

                        new_status = st.selectbox(
                            "STATUS",
                            att_options,
                            index=opt_idx,
                            key=f"att_{selected_emp_id}_{date_str}",
                            label_visibility="collapsed",
                        )

                        if new_status != status_val:
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute(
                                "INSERT OR REPLACE INTO attendance (emp_id, att_date, status) VALUES (?, ?, ?)",
                                (selected_emp_id, date_str, new_status),
                            )
                            conn.commit()
                            conn.close()
                            st.rerun()

# ==============================================================================
# 3. ADD NEW / RE-JOIN EMPLOYEE
# ==============================================================================
elif choice == "➕ ADD / RE-JOIN EMPLOYEE":
    st.markdown(
        "<p class='page-title'>ADD NEW / RE-JOIN EMPLOYEE</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p class='page-sub'>REGISTER A NEW JOINER OR PROCESS A RE-JOINING EMPLOYEE RECORD.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    with st.form("add_emp_full_form"):
        st.markdown("#### 👤 PERSONAL & CONTACT DETAILS")
        c1, c2, c3, c4 = st.columns(4)
        emp_id = c1.text_input("EMPLOYEE ID * (E.G. 4821)").upper().strip()
        name = c2.text_input("FULL NAME *").upper().strip()
        p_email = c3.text_input("PERSONAL EMAIL ID *").strip()
        o_email = c4.text_input("OFFICE EMAIL ID").strip()

        c_loc, c_dob, c_stat = st.columns(3)
        emp_location = (
            c_loc.text_input(
                "LOCATION (E.G. MUMBAI, DELHI, REMOTE)", value="MUMBAI"
            )
            .upper()
            .strip()
        )

        dob = c_dob.date_input(
            "DATE OF BIRTH (DOB)",
            value=date(1995, 1, 1),
            min_value=date(1980, 1, 1),
            max_value=datetime.now().date(),
            format="DD/MM/YYYY",
        )

        emp_initial_status = c_stat.selectbox(
            "JOINING TYPE", ["ACTIVE", "RE-JOINED"]
        )

        st.markdown("#### 🏢 JOB & POSITION DETAILS")
        c5, c6, c7 = st.columns(3)

        dept_options = STANDARD_DEPTS + ["➕ OTHER (ENTER MANUALLY)"]
        selected_dept = c5.selectbox("DEPARTMENT", dept_options)
        custom_dept = ""
        if selected_dept == "➕ OTHER (ENTER MANUALLY)":
            custom_dept = c5.text_input("ENTER CUSTOM DEPARTMENT NAME").upper().strip()

        designation = c6.text_input(
            "DESIGNATION", value="SOFTWARE ENGINEER"
        ).upper()

        joining_date = c7.date_input(
            "DATE OF JOINING (DOJ)",
            value=datetime.now().date(),
            min_value=date(2000, 1, 1),
            format="DD/MM/YYYY",
        )

        st.markdown("#### 📑 STATUTORY & IDENTITY DETAILS")
        c8, c9, c10 = st.columns(3)
        aadhar = c8.text_input("AADHAR CARD NUMBER").upper().strip()
        pan = c9.text_input("PAN CARD NUMBER").upper().strip()
        uan = c10.text_input("UAN NUMBER").upper().strip()

        st.markdown("#### 💰 COMPENSATION DETAILS")
        c11, c12 = st.columns(2)
        ctc = c11.number_input("ANNUAL CTC (₹)", min_value=0.0, step=10000.0)
        salary = c12.number_input(
            "MONTHLY IN-HAND SALARY (₹)", min_value=0.0, step=1000.0
        )

        st.markdown("---")
        st.markdown("#### 💻 INITIAL INVENTORY / ASSET ASSIGNMENT (OPTIONAL)")
        inv_col1, inv_col2 = st.columns(2)
        init_item_name = (
            inv_col1.text_input("ITEM NAME (E.G. LAPTOP, MOUSE)").upper().strip()
        )
        init_serial_no = inv_col2.text_input("SERIAL NUMBER").upper().strip()

        st.markdown("---")
        st.markdown("#### 📄 INITIAL DOCUMENTS UPLOAD (MULTIPLE ALLOWED)")
        
        # Multiple Documents Upload Feature Added Here!
        init_doc_files = st.file_uploader(
            "UPLOAD DOCUMENTS (OFFER LETTER, RESUME, PAN, AADHAR ETC.)",
            accept_multiple_files=True
        )

        submit = st.form_submit_button("REGISTER EMPLOYEE", type="primary")

        if submit:
            final_dept = (
                custom_dept
                if selected_dept == "➕ OTHER (ENTER MANUALLY)"
                else selected_dept
            )

            if not emp_id or not name:
                st.error("❌ EMPLOYEE ID AND NAME ARE MANDATORY!")
            elif selected_dept == "➕ OTHER (ENTER MANUALLY)" and not custom_dept:
                st.error("❌ PLEASE ENTER A CUSTOM DEPARTMENT NAME!")
            else:
                conn = get_connection()
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT name FROM employees WHERE emp_id = ?", (emp_id,)
                )
                emp_exist = cursor.fetchone()

                if emp_exist:
                    st.error(
                        f"❌ ERROR: EMPLOYEE ID '{emp_id}' IS ALREADY REGISTERED (NAME: {emp_exist[0]})!"
                    )
                else:
                    duplicate_found = False

                    if p_email:
                        cursor.execute(
                            "SELECT emp_id, name, status FROM employees WHERE personal_email = ?",
                            (p_email,),
                        )
                        mail_exist = cursor.fetchone()
                        if mail_exist and mail_exist[2] == "BLACKLISTED":
                            st.error(
                                f"🚫 WARNING: EMAIL '{p_email}' BELONGS TO A BLACKLISTED EMPLOYEE ({mail_exist[1]})!"
                            )
                            duplicate_found = True

                    if pan and not duplicate_found:
                        cursor.execute(
                            "SELECT emp_id, name, status FROM employees WHERE pan = ?",
                            (pan,),
                        )
                        pan_exist = cursor.fetchone()
                        if pan_exist and pan_exist[2] == "BLACKLISTED":
                            st.error(
                                f"🚫 WARNING: PAN CARD BELONGS TO A BLACKLISTED EMPLOYEE ({pan_exist[1]})!"
                            )
                            duplicate_found = True

                    if not duplicate_found:
                        j_str = joining_date.strftime("%Y-%m-%d")
                        dob_str = dob.strftime("%Y-%m-%d")
                        c_end = (
                            joining_date + relativedelta(months=6)
                        ).strftime("%Y-%m-%d")

                        cursor.execute(
                            """
                            INSERT INTO employees (emp_id, name, status, personal_email, office_email, location, dob, joining_date, doe, termination_date, aadhar, pan, uan, department, designation, ctc, salary, cl_balance, sl_balance, pl_balance, cycle_start, cycle_end)
                            VALUES (?, ?, 'ACTIVE', ?, ?, ?, ?, ?, '', '', ?, ?, ?, ?, ?, ?, ?, 3.0, 3.0, 1.0, ?, ?)
                            """,
                            (
                                emp_id,
                                name,
                                p_email,
                                o_email,
                                (
                                    emp_location
                                    if emp_location
                                    else "WORK FROM OFFICE"
                                ),
                                dob_str,
                                j_str,
                                aadhar,
                                pan,
                                uan,
                                final_dept,
                                designation,
                                ctc,
                                salary,
                                j_str,
                                c_end,
                            ),
                        )

                        if init_item_name:
                            cursor.execute(
                                "INSERT INTO inventory (emp_id, item_name, serial_number, assigned_date, status) VALUES (?, ?, ?, ?, 'ASSIGNED')",
                                (emp_id, init_item_name, init_serial_no, j_str),
                            )

                        # Multiple Documents Save Logic
                        if init_doc_files:
                            os.makedirs("uploads", exist_ok=True)
                            up_date = datetime.now().strftime("%Y-%m-%d")
                            for doc_f in init_doc_files:
                                doc_title = doc_f.name.rsplit('.', 1)[0].upper()
                                f_path = os.path.join("uploads", f"{emp_id}_{doc_f.name}")
                                with open(f_path, "wb") as f_out:
                                    f_out.write(doc_f.getbuffer())

                                cursor.execute(
                                    "INSERT INTO documents (emp_id, doc_name, file_path, upload_date) VALUES (?, ?, ?, ?)",
                                    (emp_id, doc_title, f_path, up_date),
                                )

                        conn.commit()
                        conn.close()
                        st.success(
                            f"✅ EMPLOYEE '{name}' REGISTERED SUCCESSFULLY (STATUS: ACTIVE)!"
                        )

# ==============================================================================
# 4. LEAVE REQUESTS & AUTO ATTENDANCE UPDATE ('L' MARKING)
# ==============================================================================
elif choice == "📊 LEAVE REQUESTS":
    st.markdown(
        "<p class='page-title'>LEAVE REQUESTS & ATTENDANCE AUTO-SYNC</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p class='page-sub'>APPLY LEAVES, DEDUCT BALANCES, AND AUTOMATICALLY MARK 'L' IN ATTENDANCE CALENDAR.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    conn = get_connection()
    df_emps = pd.read_sql_query(
        "SELECT emp_id, name, cl_balance, sl_balance, pl_balance, status, doe, termination_date FROM employees",
        conn,
    )
    conn.close()

    if df_emps.empty:
        st.info("NO EMPLOYEES FOUND FOR LEAVE APPLICATION.")
    else:
        df_emps["comp_status"] = df_emps.apply(
            lambda r: get_computed_status(
                r["status"], r["doe"], r["termination_date"]
            ),
            axis=1,
        )
        valid_emps = df_emps[df_emps["comp_status"] == "ACTIVE"]

        if valid_emps.empty:
            valid_emps = df_emps

        emp_map = {
            f"{row['emp_id']} - {row['name']} ({row['comp_status']})": row[
                "emp_id"
            ]
            for _, row in valid_emps.iterrows()
        }
        selected_emp_label = st.selectbox(
            "SELECT EMPLOYEE", list(emp_map.keys())
        )
        selected_emp_id = emp_map[selected_emp_label]

        sync_leave_cycles(selected_emp_id)

        conn = get_connection()
        curr_emp = pd.read_sql_query(
            "SELECT * FROM employees WHERE emp_id = ?",
            conn,
            params=(selected_emp_id,),
        ).iloc[0]
        conn.close()

        c1, c2, c3 = st.columns(3)
        c1.metric("CASUAL LEAVE (CL)", format_days(curr_emp["cl_balance"]))
        c2.metric("SICK LEAVE (SL)", format_days(curr_emp["sl_balance"]))
        c3.metric("PRIVILEGE LEAVE (PL)", format_days(curr_emp["pl_balance"]))

        st.markdown("---")
        st.markdown("#### 📝 APPLY FOR LEAVE")

        with st.form("leave_application_form"):
            l_type = st.selectbox(
                "SELECT LEAVE TYPE",
                [
                    "CL - CASUAL LEAVE",
                    "SL - SICK LEAVE",
                    "PL - PRIVILEGE LEAVE",
                    "LOP - LOSS OF PAY (UNPAID LEAVE)",
                ],
            )

            date_c1, date_c2 = st.columns(2)
            start_date = date_c1.date_input(
                "LEAVE START DATE",
                value=datetime.now().date(),
                format="DD/MM/YYYY",
            )
            end_date = date_c2.date_input(
                "LEAVE END DATE",
                value=datetime.now().date(),
                format="DD/MM/YYYY",
            )

            leave_reason = st.text_area("REASON FOR LEAVE (OPTIONAL)").strip()

            submit_leave = st.form_submit_button(
                "SUBMIT & MARK 'L' IN ATTENDANCE", type="primary"
            )

            if submit_leave:
                if start_date > end_date:
                    st.error("❌ END DATE CANNOT BE BEFORE START DATE!")
                else:
                    num_days = (end_date - start_date).days + 1

                    if "LOP" in l_type:
                        conn = get_connection()
                        cursor = conn.cursor()
                        curr_d = start_date
                        while curr_d <= end_date:
                            d_str = curr_d.strftime("%Y-%m-%d")
                            cursor.execute(
                                "INSERT OR REPLACE INTO attendance (emp_id, att_date, status) VALUES (?, ?, 'L')",
                                (selected_emp_id, d_str),
                            )
                            curr_d += timedelta(days=1)
                        conn.commit()
                        conn.close()

                        st.success(
                            f"✅ LOP RECORDED FOR {num_days} DAYS & AUTOMATICALLY MARKED AS 'L' IN CALENDAR!"
                        )
                        st.rerun()
                    else:
                        field = (
                            "cl_balance"
                            if "CL" in l_type
                            else (
                                "sl_balance"
                                if "SL" in l_type
                                else "pl_balance"
                            )
                        )
                        current_balance = float(curr_emp[field])

                        if current_balance < num_days:
                            st.error(
                                f"❌ INSUFFICIENT LEAVE BALANCE! REQUIRED: {num_days} DAYS, AVAILABLE: {current_balance} DAYS."
                            )
                        else:
                            new_balance = current_balance - num_days

                            conn = get_connection()
                            cursor = conn.cursor()

                            cursor.execute(
                                f"UPDATE employees SET {field} = ? WHERE emp_id = ?",
                                (new_balance, selected_emp_id),
                            )

                            curr_d = start_date
                            while curr_d <= end_date:
                                d_str = curr_d.strftime("%Y-%m-%d")
                                cursor.execute(
                                    "INSERT OR REPLACE INTO attendance (emp_id, att_date, status) VALUES (?, ?, 'L')",
                                    (selected_emp_id, d_str),
                                )
                                curr_d += timedelta(days=1)

                            conn.commit()
                            conn.close()

                            st.success(
                                f"✅ LEAVE APPROVED! DEDUCTED {num_days} DAYS FROM {l_type.split()[0]}. NEW BALANCE: {new_balance} DAYS. AUTOMATICALLY MARKED AS 'L' IN ATTENDANCE!"
                            )
                            st.rerun()
