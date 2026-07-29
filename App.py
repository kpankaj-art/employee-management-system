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
            department TEXT DEFAULT 'Engineering',
            job_title TEXT DEFAULT 'Software Engineer',
            joining_date TEXT NOT NULL,
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
            status TEXT DEFAULT 'Assigned',
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
# UI CONFIGURATION & CUSTOM CSS (MATCHING THE IMAGE DESIGN)
# ==============================================================================

st.set_page_config(
    page_title="Happy HR Portal",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

# CSS styling for Dark Navy Sidebar & Clean Light Body
st.markdown(
    """
    <style>
    /* Dark Theme Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #0F172A !important;
        color: #F8FAFC !important;
    }
    [data-testid="stSidebar"] * {
        color: #E2E8F0 !important;
    }
    
    /* Main Area Styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Clean Table Header Styling */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    
    .page-title {
        font-size: 28px;
        font-weight: 700;
        color: #0F172A;
        margin: 0;
    }
    
    .page-sub {
        font-size: 14px;
        color: #64748B;
        margin-top: 4px;
    }
    
    /* Card Styles */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    }
    
    /* Primary Action Buttons */
    div.stButton > button[kind="primary"] {
        background-color: #0284C7 !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# SIDEBAR NAVIGATION
# ==============================================================================
st.sidebar.markdown(
    "<h2 style='color:#38BDF8 !important; margin-bottom: 20px;'>✨ Happy"
    " HR</h2>",
    unsafe_allow_html=True,
)

st.sidebar.markdown("<p style='color:#94A3B8 !important; font-size:12px;'>MAIN MENU</p>", unsafe_allow_html=True)
menu = ["👥 Employees", "➕ Add Employee", "📊 Leave Requests", "💼 Inventory & Assets"]
choice = st.sidebar.radio("Navigation", menu, label_visibility="collapsed")

st.sidebar.markdown("<br><hr style='border-color:#1E293B;'><br>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='color:#94A3B8 !important; font-size:12px;'>TEAMS</p>", unsafe_allow_html=True)
st.sidebar.markdown("🟣 Engineering<br>🔵 Product Design<br>🟡 Marketing<br>🟢 Operations", unsafe_allow_html=True)

# ==============================================================================
# 1. EMPLOYEES LIST VIEW (SAME AS IMAGE DESIGN)
# ==============================================================================
if choice == "👥 Employees":

  # Top Bar Layout
  col_title, col_actions = st.columns([3, 2])

  with col_title:
    st.markdown("<p class='page-title'>Employees</p>", unsafe_allow_html=True)
    st.markdown(
        "<p class='page-sub'>Manage and view the complete list of employees"
        " within the organization.</p>",
        unsafe_allow_html=True,
    )

  with col_actions:
    st.write(" ")
    btn_col1, btn_col2 = st.columns(2)

    # Global Export Button
    conn = get_connection()
    df_all_emp = pd.read_sql_query("SELECT * FROM employees", conn)
    conn.close()

    with btn_col1:
      if not df_all_emp.empty:
        file_name = "All_Employees_Report.xlsx"
        with pd.ExcelWriter(file_name, engine="openpyxl") as writer:
          df_all_emp.to_excel(writer, sheet_name="Employees", index=False)
        with open(file_name, "rb") as f:
          st.download_button(
              "📤 Export Data",
              f,
              file_name=file_name,
              mime=(
                  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
              ),
              use_container_width=True,
          )

    with btn_col2:
      if st.button("➕ Add Employee", type="primary", use_container_width=True):
        st.session_state["nav"] = "➕ Add Employee"
        st.rerun()

  st.divider()

  if df_all_emp.empty:
    st.info("Abhi koi employee registered nahi hai. Sidebar se add karein.")
  else:
    # Filter Controls (Like Image)
    f_col1, f_col2, f_col3 = st.columns([2, 2, 3])
    search_query = f_col1.text_input(
        "🔎 Search",
        placeholder="Search Employees by Name, ID...",
        label_visibility="collapsed",
    )
    dept_filter = f_col2.selectbox(
        "Department",
        ["All Departments"] + list(df_all_emp["department"].unique()),
        label_visibility="collapsed",
    )

    # Filter Query
    filtered_df = df_all_emp.copy()
    if search_query:
      filtered_df = filtered_df[
          filtered_df["name"].str.contains(search_query, case=False)
          | filtered_df["emp_id"].str.contains(search_query, case=False)
      ]
    if dept_filter != "All Departments":
      filtered_df = filtered_df[filtered_df["department"] == dept_filter]

    st.write(" ")

    # TABLE DISPLAY WITH ACTIONS
    st.markdown("### 📋 Employee Master Directory")

    for _, row in filtered_df.iterrows():
      emp_id = row["emp_id"]
      name = row["name"]
      dept = row["department"]
      title = row["job_title"]
      j_date = row["joining_date"]

      # Auto Sync Leave Cycles
      sync_leave_cycles(emp_id)

      # Row Box Design
      with st.container():
        c_id, c_name, c_dept, c_title, c_date, c_act1, c_act2 = st.columns(
            [1.5, 3, 2.5, 3, 2, 1, 1]
        )

        c_id.markdown(f"**`{emp_id}`**")
        c_name.markdown(f"**{name}**")
        c_dept.markdown(f"🟢 {dept}")
        c_title.markdown(f"{title}")
        c_date.markdown(f"{j_date}")

        # View Details Popup Action Button
        if c_act1.button("👁️", key=f"view_{emp_id}", help="View Details"):
          st.session_state["selected_emp_view"] = emp_id

        # Edit Profile Popup Action Button
        if c_act2.button("✏️", key=f"edit_{emp_id}", help="Edit Employee"):
          st.session_state["selected_emp_edit"] = emp_id

        st.divider()

  # ------------------------------------------------------------------------------
  # ACTION MODAL 1: VIEW DETAILS (LEAVES, INVENTORY, DOCS)
  # ------------------------------------------------------------------------------
  if "selected_emp_view" in st.session_state:
    v_id = st.session_state["selected_emp_view"]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE emp_id = ?", (v_id,))
    emp_rec = cursor.fetchone()

    df_inv = pd.read_sql_query(
        f"SELECT * FROM inventory WHERE emp_id = '{v_id}'", conn
    )
    df_docs = pd.read_sql_query(
        f"SELECT * FROM documents WHERE emp_id = '{v_id}'", conn
    )
    conn.close()

    if emp_rec:
      e_id, e_name, e_dept, e_job, e_jdate, cl, sl, pl, _, _ = emp_rec
      j_obj = datetime.strptime(e_jdate, "%Y-%m-%d").date()
      act_date = j_obj + relativedelta(months=3)
      is_act = datetime.now().date() >= act_date

      @st.dialog(f"👤 Employee Details - {e_name} ({e_id})")
      def show_view_modal():
        st.markdown(f"**Department:** {e_dept} | **Job Title:** {e_job}")
        st.markdown(f"**Joining Date:** {e_jdate}")
        st.write("---")

        # Leave KPI
        st.markdown("#### 🌴 Leave Balances")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Status", "Active ✅" if is_act else "Probation ⏳")
        m2.metric("CL Balance", f"{cl} Days")
        m3.metric("SL Balance", f"{sl} Days")
        m4.metric("PL Balance", f"{pl} Days")

        st.write("---")
        t1, t2 = st.tabs(["💻 Assigned Inventory", "📄 Documents"])

        with t1:
          if not df_inv.empty:
            st.dataframe(
                df_inv[
                    ["item_name", "serial_number", "assigned_date", "status"]
                ],
                use_container_width=True,
            )
          else:
            st.info("No inventory items assigned.")

        with t2:
          if not df_docs.empty:
            st.dataframe(
                df_docs[["doc_name", "file_path", "upload_date"]],
                use_container_width=True,
            )
          else:
            st.info("No documents uploaded.")

        if st.button("Close"):
          del st.session_state["selected_emp_view"]
          st.rerun()

      show_view_modal()

  # ------------------------------------------------------------------------------
  # ACTION MODAL 2: EDIT EMPLOYEE DETAILS
  # ------------------------------------------------------------------------------
  if "selected_emp_edit" in st.session_state:
    ed_id = st.session_state["selected_emp_edit"]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE emp_id = ?", (ed_id,))
    rec = cursor.fetchone()
    conn.close()

    if rec:
      (
          e_id,
          e_name,
          e_dept,
          e_job,
          e_jdate,
          cl,
          sl,
          pl,
          c_start,
          c_end,
      ) = rec
      j_obj = datetime.strptime(e_jdate, "%Y-%m-%d").date()

      @st.dialog(f"✏️ Edit Details - {e_name}")
      def show_edit_modal():
        with st.form("modal_edit_form"):
          u_name = st.text_input("Full Name", value=e_name)
          u_dept = st.selectbox(
              "Department",
              [
                  "Engineering",
                  "Product Design",
                  "Marketing",
                  "Operations",
                  "Finance",
              ],
              index=[
                  "Engineering",
                  "Product Design",
                  "Marketing",
                  "Operations",
                  "Finance",
              ].index(e_dept)
              if e_dept
              in [
                  "Engineering",
                  "Product Design",
                  "Marketing",
                  "Operations",
                  "Finance",
              ]
              else 0,
          )
          u_job = st.text_input("Job Title", value=e_job)
          u_jdate = st.date_input("Joining Date", value=j_obj)

          st.markdown("##### Adjust Leave Balances")
          col_l1, col_l2, col_l3 = st.columns(3)
          u_cl = col_l1.number_input("CL", value=float(cl), step=0.5)
          u_sl = col_l2.number_input("SL", value=float(sl), step=0.5)
          u_pl = col_l3.number_input("PL", value=float(pl), step=0.5)

          btn_save = st.form_submit_button("Save Changes", type="primary")

          if btn_save:
            conn = get_connection()
            cursor = conn.cursor()
            j_str = u_jdate.strftime("%Y-%m-%d")
            n_c_end = (u_jdate + relativedelta(months=6)).strftime("%Y-%m-%d")

            cursor.execute(
                """
                            UPDATE employees 
                            SET name = ?, department = ?, job_title = ?, joining_date = ?, cl_balance = ?, sl_balance = ?, pl_balance = ?, cycle_start = ?, cycle_end = ?
                            WHERE emp_id = ?
                        """,
                (
                    u_name,
                    u_dept,
                    u_job,
                    j_str,
                    u_cl,
                    u_sl,
                    u_pl,
                    j_str,
                    n_c_end,
                    ed_id,
                ),
            )

            conn.commit()
            conn.close()
            st.success("Updated Successfully!")
            del st.session_state["selected_emp_edit"]
            st.rerun()

      show_edit_modal()

# ==============================================================================
# 2. ADD NEW EMPLOYEE
# ==============================================================================
elif choice == "➕ Add Employee":
  st.markdown("<p class='page-title'>Add New Employee</p>", unsafe_allow_html=True)
  st.divider()

  with st.form("add_emp_design_form"):
    c1, c2 = st.columns(2)
    emp_id = c1.text_input("Employee ID (e.g., 4821)")
    name = c2.text_input("Full Name (e.g., Aditya Ravi)")

    c3, c4 = st.columns(2)
    dept = c3.selectbox(
        "Department",
        ["Engineering", "Product Design", "Marketing", "Operations", "Finance"],
    )
    job_title = c4.text_input("Job Title", value="Software Engineer")

    joining_date = st.date_input("Date of Joining", value=datetime.now())

    submit = st.form_submit_button("Register Employee", type="primary")

    if submit:
      if not emp_id or not name:
        st.error("Employee ID aur Name dono required hain!")
      else:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT emp_id FROM employees WHERE emp_id = ?", (emp_id,)
        )
        if cursor.fetchone():
          st.error(f"Emp ID {emp_id} pehle se registered hai!")
        else:
          j_str = joining_date.strftime("%Y-%m-%d")
          c_end = (joining_date + relativedelta(months=6)).strftime("%Y-%m-%d")

          cursor.execute(
              """
                INSERT INTO employees (emp_id, name, department, job_title, joining_date, cl_balance, sl_balance, pl_balance, cycle_start, cycle_end)
                VALUES (?, ?, ?, ?, ?, 3.0, 3.0, 1.0, ?, ?)
              """,
              (emp_id, name, dept, job_title, j_str, j_str, c_end),
          )
          conn.commit()
          st.success(f"Employee '{name}' ({emp_id}) successfully registered!")
        conn.close()

# ==============================================================================
# 3. LEAVE REQUESTS
# ==============================================================================
elif choice == "📊 Leave Requests":
  st.markdown(
      "<p class='page-title'>Leave Applications</p>", unsafe_allow_html=True
  )
  st.divider()

  conn = get_connection()
  df_emp = pd.read_sql_query("SELECT emp_id, name FROM employees", conn)
  conn.close()

  if df_emp.empty:
    st.info("Pehle employee add karein.")
  else:
    emp_dict = {f"{r['emp_id']} - {r['name']}": r['emp_id'] for _, r in df_emp.iterrows()}
    sel_emp_str = st.selectbox("Select Employee", list(emp_dict.keys()))
    sel_emp_id = emp_dict[sel_emp_str]

    sync_leave_cycles(sel_emp_id)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE emp_id = ?", (sel_emp_id,))
    emp_rec = cursor.fetchone()
    conn.close()

    _, e_name, _, _, e_jdate, cl, sl, pl, _, _ = emp_rec
    j_obj = datetime.strptime(e_jdate, "%Y-%m-%d").date()
    act_date = j_obj + relativedelta(months=3)

    st.info(f"Probation End Date (3 Months Rule): {act_date}")

    with st.form("apply_leave_form_design"):
      col1, col2, col3 = st.columns(3)
      l_type = col1.selectbox("Leave Type", ["CL", "SL", "PL"])
      l_days = col2.number_input("Days", min_value=0.5, max_value=15.0, step=0.5)
      l_date = col3.date_input("Leave Date", value=datetime.now())

      btn_apply = st.form_submit_button("Deduct Leave", type="primary")

      if btn_apply:
        if l_date < act_date:
          st.error(f"❌ Rejected! Probation active till {act_date}")
        else:
          col_map = {"CL": "cl_balance", "SL": "sl_balance", "PL": "pl_balance"}
          conn = get_connection()
          cursor = conn.cursor()
          cursor.execute(f"SELECT {col_map[l_type]} FROM employees WHERE emp_id = ?", (sel_emp_id,))
          curr_b = cursor.fetchone()[0]

          if curr_b >= l_days:
            cursor.execute(f"UPDATE employees SET {col_map[l_type]} = ? WHERE emp_id = ?", (curr_b - l_days, sel_emp_id))
            conn.commit()
            conn.close()
            st.success(f"✅ Leave Deducted! Remaining {l_type}: {curr_b - l_days}")
            st.rerun()
          else:
            st.error(f"❌ Insufficient Balance! Available {l_type}: {curr_b}")
            conn.close()

# ==============================================================================
# 4. INVENTORY & ASSETS
# ==============================================================================
elif choice == "💼 Inventory & Assets":
  st.markdown(
      "<p class='page-title'>Inventory & Document Portal</p>",
      unsafe_allow_html=True,
  )
  st.divider()

  conn = get_connection()
  df_emp = pd.read_sql_query("SELECT emp_id, name FROM employees", conn)
  conn.close()

  if not df_emp.empty:
    emp_dict = {f"{r['emp_id']} - {r['name']}": r['emp_id'] for _, r in df_emp.iterrows()}
    sel_emp_str = st.selectbox("Select Employee for Assets/Docs", list(emp_dict.keys()))
    sel_emp_id = emp_dict[sel_emp_str]

    col_inv, col_doc = st.columns(2)

    with col_inv:
      st.markdown("#### 💻 Assign Inventory Item")
      with st.form("inv_form"):
        item_name = st.text_input("Item Name (e.g. Laptop)")
        serial_no = st.text_input("Serial Number")
        if st.form_submit_button("Assign Asset", type="primary"):
          conn = get_connection()
          cursor = conn.cursor()
          cursor.execute("INSERT INTO inventory (emp_id, item_name, serial_number, assigned_date, status) VALUES (?, ?, ?, ?, 'Assigned')", (sel_emp_id, item_name, serial_no, datetime.now().strftime("%Y-%m-%d")))
          conn.commit()
          conn.close()
          st.success("Asset Assigned!")
          st.rerun()

    with col_doc:
      st.markdown("#### 📄 Upload Document")
      with st.form("doc_form"):
        doc_name = st.text_input("Document Title")
        doc_file = st.file_uploader("Upload Document")
        if st.form_submit_button("Upload Doc", type="primary"):
          if doc_name and doc_file:
            os.makedirs("uploads", exist_ok=True)
            f_path = os.path.join("uploads", f"{sel_emp_id}_{doc_file.name}")
            with open(f_path, "wb") as f:
              f.write(doc_file.getbuffer())
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO documents (emp_id, doc_name, file_path, upload_date) VALUES (?, ?, ?, ?)", (sel_emp_id, doc_name, f_path, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            st.success("Document Saved!")
            st.rerun()
