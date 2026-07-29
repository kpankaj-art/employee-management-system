from datetime import datetime
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
            department TEXT DEFAULT 'ENGINEERING',
            designation TEXT DEFAULT 'SOFTWARE ENGINEER',
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
      "dob": "TEXT",
      "doe": "TEXT",
      "aadhar": "TEXT",
      "pan": "TEXT",
      "uan": "TEXT",
      "department": "TEXT DEFAULT 'ENGINEERING'",
      "designation": "TEXT DEFAULT 'SOFTWARE ENGINEER'",
      "ctc": "REAL DEFAULT 0.0",
      "salary": "REAL DEFAULT 0.0",
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
  return sqlite3.connect("employee_management.db")


def sync_leave_cycles(emp_id, target_date_str=None):
  if not target_date_str:
    target_date = datetime.now().date()
  else:
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()

  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute(
      "SELECT cl_balance, sl_balance, pl_balance, cycle_start, cycle_end FROM"
      " employees WHERE emp_id = ?",
      (emp_id,),
  )
  row = cursor.fetchone()

  if row:
    cl, sl, pl, cycle_start_str, cycle_end_str = row
    if cycle_end_str:
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

  conn.close()


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
    [data-testid="stSidebar"] {
        background-color: #0F172A !important;
        color: #F8FAFC !important;
    }
    [data-testid="stSidebar"] * {
        color: #E2E8F0 !important;
    }
    .main .block-container {
        padding-top: 2rem;
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
    </style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# SIDEBAR NAVIGATION
# ==============================================================================
st.sidebar.markdown(
    "<h2 style='color:#38BDF8 !important; margin-bottom: 20px;'>✨ HAPPY"
    " HR</h2>",
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    "<p style='color:#94A3B8 !important; font-size:12px;'>MAIN MENU</p>",
    unsafe_allow_html=True,
)
menu = [
    "👥 EMPLOYEES",
    "➕ ADD EMPLOYEE",
    "📊 LEAVE REQUESTS",
    "💼 INVENTORY & ASSETS",
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
        "<p class='page-sub'>MANAGE AND VIEW COMPLETE EMPLOYEE DETAILS WITHIN"
        " THE ORGANIZATION.</p>",
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
          df_all_emp.to_excel(writer, sheet_name="EMPLOYEES", index=False)
        with open(file_name, "rb") as f:
          st.download_button(
              "📤 EXPORT DATA",
              f,
              file_name=file_name,
              mime=(
                  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
              ),
              use_container_width=True,
          )

  st.divider()

  if df_all_emp.empty:
    st.info("NO EMPLOYEE REGISTERED YET. ADD FROM SIDEBAR.")
  else:
    f_col1, f_col2 = st.columns([2, 2])
    search_query = f_col1.text_input(
        "🔎 SEARCH",
        placeholder="SEARCH BY NAME, EMP ID, PAN, AADHAR, UAN...",
        label_visibility="collapsed",
    )

    dept_list = ["ALL DEPARTMENTS"] + [
        str(x).upper() for x in df_all_emp["department"].dropna().unique()
    ]
    dept_filter = f_col2.selectbox(
        "DEPARTMENT", dept_list, label_visibility="collapsed"
    )

    filtered_df = df_all_emp.copy()
    if search_query:
      filtered_df = filtered_df[
          filtered_df["name"].str.contains(search_query, case=False, na=False)
          | filtered_df["emp_id"]
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
          filtered_df["department"].str.upper() == dept_filter
      ]

    st.write(" ")
    st.markdown("### 📋 EMPLOYEE MASTER DIRECTORY")

    for _, row in filtered_df.iterrows():
      emp_id = str(row["emp_id"]).upper()
      name = str(row["name"]).upper()
      dept = str(row.get("department", "ENGINEERING")).upper()
      designation = str(row.get("designation", "SOFTWARE ENGINEER")).upper()
      j_date = str(row["joining_date"]).upper()

      sync_leave_cycles(emp_id)

      with st.container():
        c_id, c_name, c_dept, c_desg, c_date, c_act1, c_act2 = st.columns(
            [1.5, 3, 2.5, 3, 2, 1, 1]
        )

        c_id.markdown(f"**`{emp_id}`**")
        c_name.markdown(f"**{name}**")
        c_dept.markdown(f"🟢 {dept}")
        c_desg.markdown(f"{designation}")
        c_date.markdown(f"{j_date}")

        if c_act1.button("👁️", key=f"v_{emp_id}", help="VIEW PROFILE"):
          st.session_state["view_id"] = emp_id

        if c_act2.button("✏️", key=f"e_{emp_id}", help="EDIT DETAILS"):
          st.session_state["edit_id"] = emp_id

        st.divider()

  # VIEW MODAL POPUP
  if "view_id" in st.session_state:
    v_id = st.session_state["view_id"]
    conn = get_connection()
    df_emp_v = pd.read_sql_query(
        f"SELECT * FROM employees WHERE emp_id = '{v_id}'", conn
    )
    df_inv = pd.read_sql_query(
        f"SELECT * FROM inventory WHERE emp_id = '{v_id}'", conn
    )
    df_docs = pd.read_sql_query(
        f"SELECT * FROM documents WHERE emp_id = '{v_id}'", conn
    )
    conn.close()

    if not df_emp_v.empty:
      emp_rec = df_emp_v.iloc[0]
      j_obj = datetime.strptime(emp_rec["joining_date"], "%Y-%m-%d").date()
      act_date = j_obj + relativedelta(months=3)
      is_act = datetime.now().date() >= act_date

      st.markdown(
          f"### 👤 PROFILE: {str(emp_rec['name']).upper()} ({str(emp_rec['emp_id']).upper()})"
      )

      col1, col2, col3 = st.columns(3)
      col1.write(
          f"**DEPARTMENT:** {str(emp_rec.get('department', 'N/A')).upper()}"
      )
      col1.write(
          f"**DESIGNATION:** {str(emp_rec.get('designation', 'N/A')).upper()}"
      )
      col1.write(f"**DOB:** {str(emp_rec.get('dob', 'N/A')).upper()}")

      col2.write(f"**DOJ:** {str(emp_rec.get('joining_date', 'N/A')).upper()}")
      col2.write(f"**DOE:** {str(emp_rec.get('doe', 'ACTIVE')).upper()}")
      col2.write(f"**CTC:** ₹{emp_rec.get('ctc', 0.0):,.2f}")

      col3.write(f"**AADHAR:** {str(emp_rec.get('aadhar', 'N/A')).upper()}")
      col3.write(f"**PAN:** {str(emp_rec.get('pan', 'N/A')).upper()}")
      col3.write(f"**UAN:** {str(emp_rec.get('uan', 'N/A')).upper()}")

      st.write("---")
      m1, m2, m3, m4 = st.columns(4)
      m1.metric("STATUS", "ACTIVE ✅" if is_act else "PROBATION ⏳")
      m2.metric("CL BALANCE", f"{emp_rec['cl_balance']} DAYS")
      m3.metric("SL BALANCE", f"{emp_rec['sl_balance']} DAYS")
      m4.metric("PL BALANCE", f"{emp_rec['pl_balance']} DAYS")

      t1, t2 = st.tabs(["💻 ASSIGNED INVENTORY", "📄 DOCUMENTS VAULT"])
      with t1:
        st.dataframe(df_inv, use_container_width=True)
      with t2:
        st.dataframe(df_docs, use_container_width=True)

      if st.button("❌ CLOSE PROFILE"):
        del st.session_state["view_id"]
        st.rerun()

  # EDIT MODAL POPUP
  if "edit_id" in st.session_state:
    ed_id = st.session_state["edit_id"]
    conn = get_connection()
    df_emp_e = pd.read_sql_query(
        f"SELECT * FROM employees WHERE emp_id = '{ed_id}'", conn
    )
    conn.close()

    if not df_emp_e.empty:
      rec = df_emp_e.iloc[0]

      st.markdown(
          f"### ✏️ EDIT COMPLETE DETAILS: {str(rec['name']).upper()}"
      )

      with st.form("edit_emp_form_full"):
        e_c1, e_c2, e_c3 = st.columns(3)

        u_name = e_c1.text_input(
            "FULL NAME", value=str(rec["name"]).upper()
        ).upper()
        u_dept = e_c2.text_input(
            "DEPARTMENT",
            value=str(rec.get("department", "ENGINEERING")).upper(),
        ).upper()
        u_desg = e_c3.text_input(
            "DESIGNATION",
            value=str(rec.get("designation", "SOFTWARE ENGINEER")).upper(),
        ).upper()

        u_dob = e_c1.text_input(
            "DOB (YYYY-MM-DD)", value=str(rec.get("dob", ""))
        )
        u_doj = e_c2.text_input("DOJ (YYYY-MM-DD)", value=str(rec["joining_date"]))
        u_doe = e_c3.text_input(
            "DOE (YYYY-MM-DD / EMPTY)", value=str(rec.get("doe", ""))
        )

        u_aadhar = e_c1.text_input(
            "AADHAR CARD", value=str(rec.get("aadhar", "")).upper()
        ).upper()
        u_pan = e_c2.text_input(
            "PAN CARD", value=str(rec.get("pan", "")).upper()
        ).upper()
        u_uan = e_c3.text_input(
            "UAN NUMBER", value=str(rec.get("uan", "")).upper()
        ).upper()

        u_ctc = e_c1.number_input(
            "CTC (ANNUAL)", value=float(rec.get("ctc", 0.0))
        )
        u_salary = e_c2.number_input(
            "IN-HAND SALARY (MONTHLY)", value=float(rec.get("salary", 0.0))
        )

        st.markdown("##### 🌴 EDIT LEAVE BALANCES")
        l_c1, l_c2, l_c3 = st.columns(3)
        u_cl = l_c1.number_input(
            "CL BALANCE", value=float(rec["cl_balance"]), step=0.5
        )
        u_sl = l_c2.number_input(
            "SL BALANCE", value=float(rec["sl_balance"]), step=0.5
        )
        u_pl = l_c3.number_input(
            "PL BALANCE", value=float(rec["pl_balance"]), step=0.5
        )

        btn_save = st.form_submit_button("💾 SAVE CHANGES", type="primary")

        if btn_save:
          conn = get_connection()
          cursor = conn.cursor()

          try:
            j_obj = datetime.strptime(u_doj, "%Y-%m-%d").date()
            n_c_end = (j_obj + relativedelta(months=6)).strftime("%Y-%m-%d")
          except:
            n_c_end = rec["cycle_end"]

          cursor.execute(
              """
                        UPDATE employees 
                        SET name = ?, department = ?, designation = ?, dob = ?, joining_date = ?, doe = ?, 
                            aadhar = ?, pan = ?, uan = ?, ctc = ?, salary = ?, 
                            cl_balance = ?, sl_balance = ?, pl_balance = ?, cycle_start = ?, cycle_end = ?
                        WHERE emp_id = ?
                    """,
              (
                  u_name,
                  u_dept,
                  u_desg,
                  u_dob,
                  u_doj,
                  u_doe,
                  u_aadhar,
                  u_pan,
                  u_uan,
                  u_ctc,
                  u_salary,
                  u_cl,
                  u_sl,
                  u_pl,
                  u_doj,
                  n_c_end,
                  ed_id,
              ),
          )

          conn.commit()
          conn.close()
          st.success("DETAILS UPDATED SUCCESSFULLY!")
          del st.session_state["edit_id"]
          st.rerun()

      if st.button("CANCEL"):
        del st.session_state["edit_id"]
        st.rerun()

# ==============================================================================
# 2. ADD NEW EMPLOYEE
# ==============================================================================
elif choice == "➕ ADD EMPLOYEE":
  st.markdown(
      "<p class='page-title'>ADD NEW EMPLOYEE</p>", unsafe_allow_html=True
  )
  st.divider()

  with st.form("add_emp_full_form"):
    st.markdown("#### 👤 PERSONAL DETAILS")
    c1, c2, c3 = st.columns(3)
    emp_id = c1.text_input("EMPLOYEE ID * (E.G. 4821)").upper()
    name = c2.text_input("FULL NAME *").upper()
    dob = c3.date_input("DATE OF BIRTH (DOB)")

    st.markdown("#### 🏢 JOB & POSITION DETAILS")
    c4, c5, c6 = st.columns(3)
    dept = c4.selectbox(
        "DEPARTMENT",
        ["ENGINEERING", "PRODUCT DESIGN", "MARKETING", "OPERATIONS", "FINANCE"],
    )
    designation = c5.text_input(
        "DESIGNATION", value="SOFTWARE ENGINEER"
    ).upper()
    joining_date = c6.date_input("DATE OF JOINING (DOJ)")

    st.markdown("#### 📑 STATUTORY & IDENTITY DETAILS")
    c7, c8, c9 = st.columns(3)
    aadhar = c7.text_input("AADHAR CARD NUMBER").upper()
    pan = c8.text_input("PAN CARD NUMBER").upper()
    uan = c9.text_input("UAN NUMBER").upper()

    st.markdown("#### 💰 COMPENSATION DETAILS")
    c10, c11 = st.columns(2)
    ctc = c10.number_input("ANNUAL CTC (₹)", min_value=0.0, step=10000.0)
    salary = c11.number_input(
        "MONTHLY IN-HAND SALARY (₹)", min_value=0.0, step=1000.0
    )

    submit = st.form_submit_button("REGISTER EMPLOYEE", type="primary")

    if submit:
      if not emp_id or not name:
        st.error("EMPLOYEE ID AND NAME ARE MANDATORY!")
      else:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT emp_id FROM employees WHERE emp_id = ?", (emp_id,)
        )
        if cursor.fetchone():
          st.error(f"EMP ID {emp_id} IS ALREADY REGISTERED!")
        else:
          j_str = joining_date.strftime("%Y-%m-%d")
          dob_str = dob.strftime("%Y-%m-%d")
          c_end = (joining_date + relativedelta(months=6)).strftime("%Y-%m-%d")

          cursor.execute(
              """
                INSERT INTO employees (emp_id, name, dob, joining_date, doe, aadhar, pan, uan, department, designation, ctc, salary, cl_balance, sl_balance, pl_balance, cycle_start, cycle_end)
                VALUES (?, ?, ?, ?, '', ?, ?, ?, ?, ?, ?, ?, 3.0, 3.0, 1.0, ?, ?)
              """,
              (
                  emp_id,
                  name,
                  dob_str,
                  j_str,
                  aadhar,
                  pan,
                  uan,
                  dept,
                  designation,
                  ctc,
                  salary,
                  j_str,
                  c_end,
              ),
          )
          conn.commit()
          st.success(f"EMPLOYEE '{name}' ({emp_id}) REGISTERED SUCCESSFULLY!")
        conn.close()

# ==============================================================================
# 3. LEAVE REQUESTS
# ==============================================================================
elif choice == "📊 LEAVE REQUESTS":
  st.markdown(
      "<p class='page-title'>LEAVE APPLICATIONS</p>", unsafe_allow_html=True
  )
  st.divider()

  conn = get_connection()
  df_emp = pd.read_sql_query("SELECT emp_id, name FROM employees", conn)
  conn.close()

  if df_emp.empty:
    st.info("PLEASE ADD AN EMPLOYEE FIRST.")
  else:
    emp_dict = {
        f"{str(r['emp_id']).upper()} - {str(r['name']).upper()}": str(
            r["emp_id"]
        ).upper()
        for _, r in df_emp.iterrows()
    }
    sel_emp_str = st.selectbox("SELECT EMPLOYEE", list(emp_dict.keys()))
    sel_emp_id = emp_dict[sel_emp_str]

    sync_leave_cycles(sel_emp_id)

    conn = get_connection()
    df_target_emp = pd.read_sql_query(
        f"SELECT * FROM employees WHERE emp_id = '{sel_emp_id}'", conn
    )
    conn.close()

    if not df_target_emp.empty:
      emp_rec = df_target_emp.iloc[0]
      j_obj = datetime.strptime(emp_rec["joining_date"], "%Y-%m-%d").date()
      act_date = j_obj + relativedelta(months=3)

      st.info(f"PROBATION END DATE (3 MONTHS RULE): **{act_date}**")

      with st.form("apply_leave_form"):
        col1, col2, col3 = st.columns(3)
        l_type = col1.selectbox("LEAVE TYPE", ["CL", "SL", "PL"])
        l_days = col2.number_input(
            "DAYS", min_value=0.5, max_value=15.0, step=0.5
        )
        l_date = col3.date_input("LEAVE DATE", value=datetime.now())

        btn_apply = st.form_submit_button("DEDUCT LEAVE", type="primary")

        if btn_apply:
          if l_date < act_date:
            st.error(f"❌ REJECTED! PROBATION ACTIVE TILL {act_date}")
          else:
            col_map = {
                "CL": "cl_balance",
                "SL": "sl_balance",
                "PL": "pl_balance",
            }
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT {col_map[l_type]} FROM employees WHERE emp_id = ?",
                (sel_emp_id,),
            )
            curr_b = cursor.fetchone()[0]

            if curr_b >= l_days:
              cursor.execute(
                  f"UPDATE employees SET {col_map[l_type]} = ? WHERE emp_id ="
                  " ?",
                  (curr_b - l_days, sel_emp_id),
              )
              conn.commit()
              conn.close()
              st.success(
                  f"✅ LEAVE DEDUCTED! REMAINING {l_type}: {curr_b - l_days}"
              )
              st.rerun()
            else:
              st.error(
                  f"❌ INSUFFICIENT BALANCE! AVAILABLE {l_type}: {curr_b}"
              )
              conn.close()

# ==============================================================================
# 4. INVENTORY & ASSETS
# ==============================================================================
elif choice == "💼 INVENTORY & ASSETS":
  st.markdown(
      "<p class='page-title'>INVENTORY & DOCUMENT PORTAL</p>",
      unsafe_allow_html=True,
  )
  st.divider()

  conn = get_connection()
  df_emp = pd.read_sql_query("SELECT emp_id, name FROM employees", conn)
  conn.close()

  if not df_emp.empty:
    emp_dict = {
        f"{str(r['emp_id']).upper()} - {str(r['name']).upper()}": str(
            r["emp_id"]
        ).upper()
        for _, r in df_emp.iterrows()
    }
    sel_emp_str = st.selectbox(
        "SELECT EMPLOYEE FOR ASSETS/DOCS", list(emp_dict.keys())
    )
    sel_emp_id = emp_dict[sel_emp_str]

    col_inv, col_doc = st.columns(2)

    with col_inv:
      st.markdown("#### 💻 ASSIGN INVENTORY ITEM")
      with st.form("inv_form"):
        item_name = st.text_input("ITEM NAME (E.G. LAPTOP)").upper()
        serial_no = st.text_input("SERIAL NUMBER").upper()
        if st.form_submit_button("ASSIGN ASSET", type="primary"):
          conn = get_connection()
          cursor = conn.cursor()
          cursor.execute(
              "INSERT INTO inventory (emp_id, item_name, serial_number,"
              " assigned_date, status) VALUES (?, ?, ?, ?, 'ASSIGNED')",
              (
                  sel_emp_id,
                  item_name,
                  serial_no,
                  datetime.now().strftime("%Y-%m-%d"),
              ),
          )
          conn.commit()
          conn.close()
          st.success("ASSET ASSIGNED!")
          st.rerun()

    with col_doc:
      st.markdown("#### 📄 UPLOAD DOCUMENT")
      with st.form("doc_form"):
        doc_name = st.text_input("DOCUMENT TITLE").upper()
        doc_file = st.file_uploader("UPLOAD DOCUMENT")
        if st.form_submit_button("UPLOAD DOC", type="primary"):
          if doc_name and doc_file:
            os.makedirs("uploads", exist_ok=True)
            f_path = os.path.join("uploads", f"{sel_emp_id}_{doc_file.name}")
            with open(f_path, "wb") as f:
              f.write(doc_file.getbuffer())
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO documents (emp_id, doc_name, file_path,"
                " upload_date) VALUES (?, ?, ?, ?)",
                (
                    sel_emp_id,
                    doc_name,
                    f_path,
                    datetime.now().strftime("%Y-%m-%d"),
                ),
            )
            conn.commit()
            conn.close()
            st.success("DOCUMENT SAVED!")
            st.rerun()
