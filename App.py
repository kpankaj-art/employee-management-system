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
      "department": "TEXT DEFAULT 'DEVELOPMENT'",
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
    return datetime.strptime(str(date_str), "%Y-%m-%d").strftime("%d/%m/%Y")
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


def sync_leave_cycles(emp_id, target_date_str=None):
  if not target_date_str:
    target_date = datetime.now().date()
  else:
    try:
      target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    except:
      target_date = datetime.now().date()

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
      except:
        pass

  cursor.execute("DELETE FROM inventory WHERE emp_id = ?", (emp_id,))
  cursor.execute("DELETE FROM documents WHERE emp_id = ?", (emp_id,))
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
menu = ["👥 EMPLOYEES", "➕ ADD EMPLOYEE", "📊 LEAVE REQUESTS"]
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

    filtered_df = df_all_emp.copy()
    if search_query:
      filtered_df = filtered_df[
          filtered_df["name"]
          .astype(str)
          .str.contains(search_query, case=False, na=False)
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
          filtered_df["department"].astype(str).str.upper() == dept_filter
      ]

    st.write(" ")
    st.markdown("### 📋 EMPLOYEE MASTER DIRECTORY")

    for _, row in filtered_df.iterrows():
      emp_id = str(row["emp_id"]).upper()
      name = str(row.get("name", "")).upper()
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
      j_date = format_date_display(row.get("joining_date", ""))

      sync_leave_cycles(emp_id)

      with st.container():
        c_id, c_name, c_dept, c_desg, c_date, c_act1, c_act2, c_act3 = (
            st.columns([1.2, 2.8, 2.2, 2.8, 1.8, 0.8, 0.8, 0.8])
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

        if c_act3.button("🗑️", key=f"d_{emp_id}", help="DELETE EMPLOYEE"):
          st.session_state["confirm_del_id"] = emp_id

        st.divider()

  # DELETE CONFIRMATION MODAL
  if "confirm_del_id" in st.session_state:
    del_emp_id = st.session_state["confirm_del_id"]
    st.warning(
        f"⚠️ ARE YOU SURE YOU WANT TO PERMANENTLY DELETE EMPLOYEE ID:"
        f" **{del_emp_id}**?"
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

      try:
        j_obj = datetime.strptime(
            str(emp_rec["joining_date"]), "%Y-%m-%d"
        ).date()
        act_date = j_obj + relativedelta(months=3)
        is_act = datetime.now().date() >= act_date
      except:
        act_date = "N/A"
        is_act = True

      st.markdown(
          f"### 👤 PROFILE: {str(emp_rec.get('name', '')).upper()} ({str(emp_rec.get('emp_id', '')).upper()})"
      )

      col1, col2, col3 = st.columns(3)
      col1.write(
          f"**DEPARTMENT:**"
          f" {str(emp_rec.get('department') if pd.notna(emp_rec.get('department')) else 'N/A').upper()}"
      )
      col1.write(
          f"**DESIGNATION:**"
          f" {str(emp_rec.get('designation') if pd.notna(emp_rec.get('designation')) else 'N/A').upper()}"
      )
      col1.write(
          f"**DOB:**"
          f" {format_date_display(emp_rec.get('dob') if pd.notna(emp_rec.get('dob')) else 'N/A')}"
      )

      col2.write(
          f"**DOJ:**"
          f" {format_date_display(emp_rec.get('joining_date') if pd.notna(emp_rec.get('joining_date')) else 'N/A')}"
      )
      col2.write(
          f"**DOE:**"
          f" {format_date_display(emp_rec.get('doe')) if pd.notna(emp_rec.get('doe')) and str(emp_rec.get('doe')).strip() != '' else 'ACTIVE'}"
      )

      try:
        ctc_val = float(emp_rec.get("ctc", 0.0))
      except:
        ctc_val = 0.0
      col2.write(f"**CTC:** ₹{ctc_val:,.2f}")

      col3.write(
          f"**AADHAR:**"
          f" {str(emp_rec.get('aadhar') if pd.notna(emp_rec.get('aadhar')) else 'N/A').upper()}"
      )
      col3.write(
          f"**PAN:**"
          f" {str(emp_rec.get('pan') if pd.notna(emp_rec.get('pan')) else 'N/A').upper()}"
      )
      col3.write(
          f"**UAN:**"
          f" {str(emp_rec.get('uan') if pd.notna(emp_rec.get('uan')) else 'N/A').upper()}"
      )

      st.write("---")
      m1, m2, m3, m4 = st.columns(4)
      m1.metric("STATUS", "ACTIVE ✅" if is_act else "PROBATION ⏳")
      m2.metric("CL BALANCE", format_days(emp_rec.get("cl_balance", 0)))
      m3.metric("SL BALANCE", format_days(emp_rec.get("sl_balance", 0)))
      m4.metric("PL BALANCE", format_days(emp_rec.get("pl_balance", 0)))

      t1, t2 = st.tabs(["💻 ASSIGNED INVENTORY", "📄 DOCUMENTS VAULT"])

      # INVENTORY TAB WITH DELETE OPTION
      with t1:
        if df_inv.empty:
          st.info("NO INVENTORY ASSIGNED YET.")
        else:
          for _, inv_row in df_inv.iterrows():
            i_col1, i_col2, i_col3, i_col4 = st.columns([3, 3, 2, 1])
            i_col1.write(f"**ITEM:** {str(inv_row['item_name']).upper()}")
            i_col2.write(
                f"**SERIAL:**"
                f" {str(inv_row['serial_number'] if inv_row['serial_number'] else 'N/A').upper()}"
            )
            i_col3.write(
                f"**DATE:** {format_date_display(inv_row['assigned_date'])}"
            )

            if i_col4.button(
                "🗑️", key=f"del_inv_{inv_row['id']}", help="DELETE INVENTORY ITEM"
            ):
              conn = get_connection()
              cursor = conn.cursor()
              cursor.execute(
                  "DELETE FROM inventory WHERE id = ?", (inv_row["id"],)
              )
              conn.commit()
              conn.close()
              st.success("INVENTORY ITEM DELETED!")
              st.rerun()

      # DOCUMENTS TAB WITH VIEW & DELETE OPTION
      with t2:
        if df_docs.empty:
          st.info("NO DOCUMENTS UPLOADED YET.")
        else:
          for _, doc_row in df_docs.iterrows():
            d_col1, d_col2, d_col3, d_col4 = st.columns([3, 2, 1, 1])
            d_col1.write(f"**DOC:** {str(doc_row['doc_name']).upper()}")
            d_col2.write(
                f"**DATE:** {format_date_display(doc_row['upload_date'])}"
            )

            file_path = doc_row["file_path"]
            if file_path and os.path.exists(file_path):
              with open(file_path, "rb") as f:
                d_col3.download_button(
                    "👁️ VIEW",
                    f,
                    file_name=os.path.basename(file_path),
                    key=f"dl_doc_{doc_row['id']}",
                )
            else:
              d_col3.write("FILE MISSING")

            if d_col4.button(
                "🗑️", key=f"del_doc_{doc_row['id']}", help="DELETE DOCUMENT"
            ):
              if file_path and os.path.exists(file_path):
                try:
                  os.remove(file_path)
                except:
                  pass
              conn = get_connection()
              cursor = conn.cursor()
              cursor.execute(
                  "DELETE FROM documents WHERE id = ?", (doc_row["id"],)
              )
              conn.commit()
              conn.close()
              st.success("DOCUMENT DELETED!")
              st.rerun()

      st.write(" ")
      if st.button("❌ CLOSE PROFILE"):
        del st.session_state["view_id"]
        st.rerun()

  # EDIT DETAILS MODAL
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
          f"### ✏️ EDIT COMPLETE DETAILS: {str(rec.get('name', '')).upper()}"
      )

      with st.form("edit_emp_form_full"):
        e_c1, e_c2, e_c3 = st.columns(3)

        u_name = e_c1.text_input(
            "FULL NAME", value=str(rec.get("name", "")).upper()
        ).upper()

        existing_dept = str(
            rec.get("department")
            if pd.notna(rec.get("department"))
            else "DEVELOPMENT"
        ).upper()
        edit_dept_options = STANDARD_DEPTS + ["➕ OTHER (ENTER MANUALLY)"]
        dept_idx = (
            edit_dept_options.index(existing_dept)
            if existing_dept in edit_dept_options
            else 0
        )

        sel_u_dept = e_c2.selectbox(
            "DEPARTMENT", edit_dept_options, index=dept_idx
        )
        custom_u_dept = ""
        if sel_u_dept == "➕ OTHER (ENTER MANUALLY)":
          custom_u_dept = e_c2.text_input(
              "ENTER CUSTOM DEPARTMENT NAME", value=existing_dept
          ).upper()

        u_desg = e_c3.text_input(
            "DESIGNATION",
            value=str(
                rec.get("designation")
                if pd.notna(rec.get("designation"))
                else "SOFTWARE ENGINEER"
            ).upper(),
        ).upper()

        try:
          curr_dob = datetime.strptime(
              str(rec.get("dob")), "%Y-%m-%d"
          ).date()
        except:
          curr_dob = date(1995, 1, 1)

        try:
          curr_doj = datetime.strptime(
              str(rec.get("joining_date")), "%Y-%m-%d"
          ).date()
        except:
          curr_doj = datetime.now().date()

        u_dob_val = e_c1.date_input(
            "DOB (DD/MM/YYYY)",
            value=curr_dob,
            min_value=date(1980, 1, 1),
            max_value=datetime.now().date(),
            format="DD/MM/YYYY",
        )
        u_doj_val = e_c2.date_input(
            "DOJ (DD/MM/YYYY)",
            value=curr_doj,
            min_value=date(2000, 1, 1),
            format="DD/MM/YYYY",
        )
        u_doe_str = e_c3.text_input(
            "DOE (YYYY-MM-DD / EMPTY)",
            value=str(rec.get("doe") if pd.notna(rec.get("doe")) else ""),
        )

        u_aadhar = e_c1.text_input(
            "AADHAR CARD",
            value=str(
                rec.get("aadhar") if pd.notna(rec.get("aadhar")) else ""
            ).upper(),
        ).upper()
        u_pan = e_c2.text_input(
            "PAN CARD",
            value=str(
                rec.get("pan") if pd.notna(rec.get("pan")) else ""
            ).upper(),
        ).upper()
        u_uan = e_c3.text_input(
            "UAN NUMBER",
            value=str(
                rec.get("uan") if pd.notna(rec.get("uan")) else ""
            ).upper(),
        ).upper()

        try:
          c_val = float(rec.get("ctc", 0.0))
        except:
          c_val = 0.0
        try:
          s_val = float(rec.get("salary", 0.0))
        except:
          s_val = 0.0

        u_ctc = e_c1.number_input("CTC (ANNUAL)", value=c_val)
        u_salary = e_c2.number_input("IN-HAND SALARY (MONTHLY)", value=s_val)

        st.markdown("##### 🌴 EDIT LEAVE BALANCES")
        l_c1, l_c2, l_c3 = st.columns(3)
        u_cl = l_c1.number_input(
            "CL BALANCE", value=float(rec.get("cl_balance", 3.0)), step=0.5
        )
        u_sl = l_c2.number_input(
            "SL BALANCE", value=float(rec.get("sl_balance", 3.0)), step=0.5
        )
        u_pl = l_c3.number_input(
            "PL BALANCE", value=float(rec.get("pl_balance", 1.0)), step=0.5
        )

        btn_save = st.form_submit_button("💾 SAVE CHANGES", type="primary")

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
          u_doe_parsed = parse_date_input(u_doe_str)

          conn = get_connection()
          cursor = conn.cursor()

          try:
            j_obj = datetime.strptime(u_doj_parsed, "%Y-%m-%d").date()
            n_c_end = (j_obj + relativedelta(months=6)).strftime("%Y-%m-%d")
          except:
            n_c_end = str(rec.get("cycle_end", ""))

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
                  final_u_dept,
                  u_desg,
                  u_dob_parsed,
                  u_doj_parsed,
                  u_doe_parsed,
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
          st.success("DETAILS UPDATED SUCCESSFULLY!")
          del st.session_state["edit_id"]
          st.rerun()

      # ADD NEW INVENTORY / DOCUMENT SECTION INSIDE EDIT
      st.markdown("---")
      st.markdown("##### ➕ ADD ADDITIONAL INVENTORY / DOCUMENT")
      e_tab1, e_tab2 = st.tabs(
          ["💻 ADD INVENTORY ITEM", "📄 UPLOAD NEW DOCUMENT"]
      )

      with e_tab1:
        with st.form("add_inv_in_edit"):
          e_inv_item = st.text_input("ITEM NAME (E.G. LAPTOP)").upper().strip()
          e_inv_serial = st.text_input("SERIAL NUMBER").upper().strip()
          if st.form_submit_button("ASSIGN NEW ITEM"):
            if e_inv_item:
              conn = get_connection()
              cursor = conn.cursor()
              cursor.execute(
                  "INSERT INTO inventory (emp_id, item_name, serial_number,"
                  " assigned_date, status) VALUES (?, ?, ?, ?, 'ASSIGNED')",
                  (
                      ed_id,
                      e_inv_item,
                      e_inv_serial,
                      datetime.now().strftime("%Y-%m-%d"),
                  ),
              )
              conn.commit()
              conn.close()
              st.success("NEW INVENTORY ADDED!")
              st.rerun()
            else:
              st.error("PLEASE ENTER ITEM NAME!")

      with e_tab2:
        with st.form("add_doc_in_edit"):
          e_doc_title = (
              st.text_input("DOCUMENT TITLE (E.G. AADHAR CARD)").upper().strip()
          )
          e_doc_file = st.file_uploader("CHOOSE FILE")
          if st.form_submit_button("UPLOAD NEW FILE"):
            if e_doc_title and e_doc_file:
              os.makedirs("uploads", exist_ok=True)
              f_path = os.path.join("uploads", f"{ed_id}_{e_doc_file.name}")
              with open(f_path, "wb") as f:
                f.write(e_doc_file.getbuffer())
              conn = get_connection()
              cursor = conn.cursor()
              cursor.execute(
                  "INSERT INTO documents (emp_id, doc_name, file_path,"
                  " upload_date) VALUES (?, ?, ?, ?)",
                  (
                      ed_id,
                      e_doc_title,
                      f_path,
                      datetime.now().strftime("%Y-%m-%d"),
                  ),
              )
              conn.commit()
              conn.close()
              st.success("NEW DOCUMENT SAVED!")
              st.rerun()
            else:
              st.error("PLEASE ENTER TITLE AND CHOOSE A FILE!")

      st.write(" ")
      if st.button("CLOSE EDIT"):
        del st.session_state["edit_id"]
        st.rerun()

# ==============================================================================
# 2. ADD NEW EMPLOYEE (WITH INTEGRATED INVENTORY & DOCUMENTS)
# ==============================================================================
elif choice == "➕ ADD EMPLOYEE":
  st.markdown(
      "<p class='page-title'>ADD NEW EMPLOYEE</p>", unsafe_allow_html=True
  )
  st.divider()

  with st.form("add_emp_full_form"):
    st.markdown("#### 👤 PERSONAL DETAILS")
    c1, c2, c3 = st.columns(3)
    emp_id = c1.text_input("EMPLOYEE ID * (E.G. 4821)").upper().strip()
    name = c2.text_input("FULL NAME *").upper().strip()

    dob = c3.date_input(
        "DATE OF BIRTH (DOB)",
        value=date(1995, 1, 1),
        min_value=date(1980, 1, 1),
        max_value=datetime.now().date(),
        format="DD/MM/YYYY",
    )

    st.markdown("#### 🏢 JOB & POSITION DETAILS")
    c4, c5, c6 = st.columns(3)

    dept_options = STANDARD_DEPTS + ["➕ OTHER (ENTER MANUALLY)"]
    selected_dept = c4.selectbox("DEPARTMENT", dept_options)
    custom_dept = ""
    if selected_dept == "➕ OTHER (ENTER MANUALLY)":
      custom_dept = c4.text_input(
          "ENTER CUSTOM DEPARTMENT NAME"
      ).upper().strip()

    designation = c5.text_input(
        "DESIGNATION", value="SOFTWARE ENGINEER"
    ).upper()

    joining_date = c6.date_input(
        "DATE OF JOINING (DOJ)",
        value=datetime.now().date(),
        min_value=date(2000, 1, 1),
        format="DD/MM/YYYY",
    )

    st.markdown("#### 📑 STATUTORY & IDENTITY DETAILS")
    c7, c8, c9 = st.columns(3)
    aadhar = c7.text_input("AADHAR CARD NUMBER").upper().strip()
    pan = c8.text_input("PAN CARD NUMBER").upper().strip()
    uan = c9.text_input("UAN NUMBER").upper().strip()

    st.markdown("#### 💰 COMPENSATION DETAILS")
    c10, c11 = st.columns(2)
    ctc = c10.number_input("ANNUAL CTC (₹)", min_value=0.0, step=10000.0)
    salary = c11.number_input(
        "MONTHLY IN-HAND SALARY (₹)", min_value=0.0, step=1000.0
    )

    st.markdown("---")
    st.markdown("#### 💻 INITIAL INVENTORY / ASSET ASSIGNMENT (OPTIONAL)")
    inv_col1, inv_col2 = st.columns(2)
    init_item_name = inv_col1.text_input(
        "ITEM NAME (E.G. LAPTOP, MOUSE)"
    ).upper().strip()
    init_serial_no = inv_col2.text_input("SERIAL NUMBER").upper().strip()

    st.markdown("---")
    st.markdown("#### 📄 INITIAL DOCUMENT UPLOAD (OPTIONAL)")
    doc_col1, doc_col2 = st.columns(2)
    init_doc_name = doc_col1.text_input(
        "DOCUMENT TITLE (E.G. OFFER LETTER, AADHAR)"
    ).upper().strip()
    init_doc_file = doc_col2.file_uploader("UPLOAD FILE")

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

        cursor.execute("SELECT name FROM employees WHERE emp_id = ?", (emp_id,))
        emp_exist = cursor.fetchone()

        if emp_exist:
          st.error(
              f"❌ ERROR: EMPLOYEE ID '{emp_id}' IS ALREADY REGISTERED (NAME:"
              f" {emp_exist[0]})!"
          )
        else:
          duplicate_found = False

          if pan:
            cursor.execute(
                "SELECT emp_id, name FROM employees WHERE pan = ?", (pan,)
            )
            pan_exist = cursor.fetchone()
            if pan_exist:
              st.error(
                  f"❌ ERROR: PAN CARD '{pan}' IS ALREADY REGISTERED WITH EMP"
                  f" ID: {pan_exist[0]} ({pan_exist[1]})!"
              )
              duplicate_found = True

          if aadhar and not duplicate_found:
            cursor.execute(
                "SELECT emp_id, name FROM employees WHERE aadhar = ?", (aadhar,)
            )
            aadhar_exist = cursor.fetchone()
            if aadhar_exist:
              st.error(
                  f"❌ ERROR: AADHAR CARD '{aadhar}' IS ALREADY REGISTERED WITH"
                  f" EMP ID: {aadhar_exist[0]} ({aadhar_exist[1]})!"
              )
              duplicate_found = True

          if not duplicate_found:
            j_str = joining_date.strftime("%Y-%m-%d")
            dob_str = dob.strftime("%Y-%m-%d")
            c_end = (joining_date + relativedelta(months=6)).strftime(
                "%Y-%m-%d"
            )

            # Insert Employee Record
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
                    final_dept,
                    designation,
                    ctc,
                    salary,
                    j_str,
                    c_end,
                ),
            )

            # Insert Inventory if entered
            if init_item_name:
              cursor.execute(
                  "INSERT INTO inventory (emp_id, item_name, serial_number,"
                  " assigned_date, status) VALUES (?, ?, ?, ?, 'ASSIGNED')",
                  (emp_id, init_item_name, init_serial_no, j_str),
              )

            # Upload & Insert Document if selected
            if init_doc_name and init_doc_file:
              os.makedirs("uploads", exist_ok=True)
              f_path = os.path.join("uploads", f"{emp_id}_{init_doc_file.name}")
              with open(f_path, "wb") as f:
                f.write(init_doc_file.getbuffer())
              cursor.execute(
                  "INSERT INTO documents (emp_id, doc_name, file_path,"
                  " upload_date) VALUES (?, ?, ?, ?)",
                  (emp_id, init_doc_name, f_path, j_str),
              )

            conn.commit()
            st.success(
                f"✅ EMPLOYEE '{name}' ({emp_id}) REGISTERED SUCCESSFULLY!"
            )

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

      try:
        j_obj = datetime.strptime(
            str(emp_rec["joining_date"]), "%Y-%m-%d"
        ).date()
        act_date = j_obj + relativedelta(months=3)
      except:
        act_date = datetime.now().date()

      st.info(
          f"PROBATION END DATE (3 MONTHS RULE): **{format_date_display(act_date.strftime('%Y-%m-%d'))}**"
      )

      st.write("### CURRENT BALANCE:")
      b_c1, b_c2, b_c3 = st.columns(3)
      b_c1.metric("CL BALANCE", format_days(emp_rec.get("cl_balance", 0)))
      b_c2.metric("SL BALANCE", format_days(emp_rec.get("sl_balance", 0)))
      b_c3.metric("PL BALANCE", format_days(emp_rec.get("pl_balance", 0)))

      with st.form("apply_leave_form"):
        col1, col2, col3 = st.columns(3)
        l_type = col1.selectbox("LEAVE TYPE", ["CL", "SL", "PL"])
        l_days = col2.number_input(
            "DAYS", min_value=0.5, max_value=15.0, step=0.5
        )
        l_date = col3.date_input(
            "LEAVE DATE (DD/MM/YYYY)",
            value=datetime.now().date(),
            format="DD/MM/YYYY",
        )

        btn_apply = st.form_submit_button("DEDUCT LEAVE", type="primary")

        if btn_apply:
          if l_date < act_date:
            st.error(
                "❌ REJECTED! PROBATION ACTIVE TILL"
                f" {format_date_display(act_date.strftime('%Y-%m-%d'))}"
            )
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
            res = cursor.fetchone()

            if res and res[0] is not None:
              curr_b = float(res[0])
              if curr_b >= l_days:
                cursor.execute(
                    f"UPDATE employees SET {col_map[l_type]} = ? WHERE emp_id"
                    " = ?",
                    (curr_b - l_days, sel_emp_id),
                )
                conn.commit()
                conn.close()
                st.success(
                    f"✅ LEAVE DEDUCTED! REMAINING {l_type}:"
                    f" {format_days(curr_b - l_days)}"
                )
                st.rerun()
              else:
                st.error(
                    f"❌ INSUFFICIENT BALANCE! AVAILABLE {l_type}:"
                    f" {format_days(curr_b)}"
                )
                conn.close()
            else:
              conn.close()
              st.error("EMPLOYEE RECORD NOT FOUND!")
