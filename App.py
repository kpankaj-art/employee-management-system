from datetime import datetime
import os
import sqlite3
from dateutil.relativedelta import relativedelta
import pandas as pd
import streamlit as st

# ==============================================================================
# DATABASE SETUP & HELPERS
# ==============================================================================


def init_db():
  """SQLite Database Tables create karta hai."""
  conn = sqlite3.connect("employee_management.db")
  cursor = conn.cursor()

  # Employees Table
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            emp_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            joining_date TEXT NOT NULL,
            CL_balance REAL DEFAULT 3.0,
            SL_balance REAL DEFAULT 3.0,
            PL_balance REAL DEFAULT 1.0,
            cycle_start TEXT NOT NULL,
            cycle_end TEXT NOT NULL
        )
    """)

  # Inventory Table (With Return Status)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Emp_ID TEXT,
            Item_Name TEXT,
            serial_number TEXT,
            assigned_date TEXT,
            status TEXT DEFAULT 'Assigned',
            FOREIGN KEY (emp_id) REFERENCES employees (emp_id)
        )
    """)

  # Documents Table
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Emp_ID TEXT,
            Doc_Name TEXT,
            File_path TEXT,
            Upload_date TEXT,
            FOREIGN KEY (emp_id) REFERENCES employees (emp_id)
        )
    """)

  conn.commit()
  conn.close()


def get_connection():
  return sqlite3.connect("employee_management.db")


# Leave Carry Forward Auto-Sync
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

    # 6 Month Carry Forward Addition
    while target_date >= cycle_end:
      CL += 3.0
      SL += 3.0
      PL += 1.0
      new_cycle_start = cycle_end
      cycle_end = new_cycle_start + relativedelta(months=6)

      cursor.execute(
          """
                UPDATE employees 
                SET cl_balance = ?, sl_balance = ?, pl_balance = ?, cycle_start = ?, cycle_end = ?
                WHERE emp_id = ?
            """,
          (
              CL,
              SL,
              PL,
              new_cycle_start.strftime("%Y-%m-%d"),
              cycle_end.strftime("%Y-%m-%d"),
              emp_id,
          ),
      )
      conn.commit()

  conn.close()


# ==============================================================================
# STREAMLIT UI CODE
# ==============================================================================

st.set_page_config(
    page_title="Employee Master Portal", page_icon="👤", layout="wide"
)
init_db()

st.title("👤 Employee Master Search & Management Portal")

# Sidebar Menu
menu = ["Search & Manage Employee", "Add New Employee", "All Employees List"]
choice = st.sidebar.selectbox("Navigation Menu", menu)

# ------------------------------------------------------------------------------
# 1. SEARCH & MANAGE EMPLOYEE (ALL-IN-ONE HUB)
# ------------------------------------------------------------------------------
if choice == "Search & Manage Employee":
  st.subheader("🔎 Search Employee")

  conn = get_connection()
  df_all = pd.read_sql_query("SELECT emp_id, name FROM employees", conn)
  conn.close()

  if df_all.empty:
    st.info(
        "Abhi koi employee registered nahi hai. Sidebar se naya employee add"
        " karein."
    )
  else:
    # Live Search Dropdown / Autocomplete
    emp_options = [
        f"{row['emp_id']} - {row['name']}" for _, row in df_all.iterrows()
    ]
    selected_option = st.selectbox(
        "Type Employee ID or Name to Search:",
        emp_options,
        index=0,
        help="Yahan ID ya Naam type karke select karein",
    )

    selected_emp_id = selected_option.split(" - ")[0]

    # Auto-Sync Leave Cycles on load
    sync_leave_cycles(selected_emp_id)

    # Fetch Fresh Employee Data
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM employees WHERE emp_id = ?", (selected_emp_id,)
    )
    emp_data = cursor.fetchone()
    conn.close()

    emp_id, name, j_date_str, cl, sl, pl, c_start, c_end = emp_data
    joining_date = datetime.strptime(j_date_str, "%Y-%m-%d").date()
    active_date = joining_date + relativedelta(months=3)

    st.markdown("---")

    # HEADER & QUICK EXCEL EXPORT
    col_head1, col_head2 = st.columns([3, 1])
    with col_head1:
      st.markdown(f"## 📌 Dashboard: **{name}** (`{emp_id}`)")
    with col_head2:
      # Direct Excel Export for Searched Employee
      conn = get_connection()
      df_prof = pd.read_sql_query(
          f"SELECT * FROM employees WHERE emp_id = '{emp_id}'", conn
      )
      df_inv = pd.read_sql_query(
          f"SELECT item_name, serial_number, assigned_date, status FROM"
          f" inventory WHERE emp_id = '{emp_id}'",
          conn,
      )
      df_docs = pd.read_sql_query(
          f"SELECT doc_name, file_path, upload_date FROM documents WHERE"
          f" emp_id = '{emp_id}'",
          conn,
      )
      conn.close()

      file_name = f"{emp_id}_{name.replace(' ', '_')}_Report.xlsx"
      with pd.ExcelWriter(file_name, engine="openpyxl") as writer:
        df_prof.to_excel(writer, sheet_name="Profile & Leaves", index=False)
        df_inv.to_excel(writer, sheet_name="Inventory", index=False)
        df_docs.to_excel(writer, sheet_name="Documents", index=False)

      with open(file_name, "rb") as f:
        st.download_button(
            label="📥 Download Excel Report",
            data=f,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    # SECTION 1: PROFILE EDIT & DETAILS
    with st.expander("📝 Edit Employee Profile / Details", expanded=False):
      with st.form("edit_profile_form"):
        new_name = st.text_input("Name", value=name)
        new_jdate = st.date_input("Joining Date", value=joining_date)
        update_btn = st.form_submit_button("Update Profile")

        if update_btn:
          conn = get_connection()
          cursor = conn.cursor()
          j_str = new_jdate.strftime("%Y-%m-%d")
          new_c_end = (new_jdate + relativedelta(months=6)).strftime("%Y-%m-%d")

          cursor.execute(
              """
                        UPDATE employees 
                        SET name = ?, joining_date = ?, cycle_start = ?, cycle_end = ?
                        WHERE emp_id = ?
                    """,
              (new_name, j_str, j_str, new_c_end, emp_id),
          )
          conn.commit()
          conn.close()
          st.success("Profile Updated Successfully!")
          st.rerun()

    # SECTION 2: LEAVE MANAGEMENT
    st.markdown("### 🌴 Leave Management")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Casual Leave (CL)", f"{cl} Days")
    m2.metric("Sick Leave (SL)", f"{sl} Days")
    m3.metric("Privilege Leave (PL)", f"{pl} Days")
    m4.metric("Leave Active Status", "Active" if datetime.now().date() >= active_date else f"Active from {active_date}")

    with st.form("apply_leave_form"):
      c1, c2, c3 = st.columns(3)
      l_type = c1.selectbox("Leave Type", ["CL", "SL", "PL"])
      l_days = c2.number_input("Days", min_value=0.5, max_value=15.0, step=0.5)
      l_date = c3.date_input("Leave Date", value=datetime.now())

      apply_btn = st.form_submit_button("Apply & Deduct Leave")

      if apply_btn:
        if l_date < active_date:
          st.error(f"❌ Cannot apply! Employee 3-month probation period ends on: {active_date}")
        else:
          conn = get_connection()
          cursor = conn.cursor()
          col_map = {"CL": "cl_balance", "SL": "sl_balance", "PL": "pl_balance"}
          cursor.execute(f"SELECT {col_map[l_type]} FROM employees WHERE emp_id = ?", (emp_id,))
          curr_bal = cursor.fetchone()[0]

          if curr_bal >= l_days:
            cursor.execute(f"UPDATE employees SET {col_map[l_type]} = ? WHERE emp_id = ?", (curr_bal - l_days, emp_id))
            conn.commit()
            conn.close()
            st.success(f"✅ Approved! Remaining {l_type}: {curr_bal - l_days}")
            st.rerun()
          else:
            st.error(f"❌ Insufficient Balance! Available {l_type}: {curr_bal}")
            conn.close()

    st.markdown("---")

    # SECTION 3: INVENTORY & DOCUMENTS SIDE-BY-SIDE
    col_inv, col_doc = st.columns(2)

    # INVENTORY BOX
    with col_inv:
      st.markdown("### 💻 Inventory Management")

      with st.form("add_inv_form"):
        inv_name = st.text_input("Item Name (e.g. Laptop)")
        inv_sr = st.text_input("Serial Number")
        inv_btn = st.form_submit_button("Assign Inventory")

        if inv_btn and inv_name and inv_sr:
          conn = get_connection()
          cursor = conn.cursor()
          cursor.execute(
              "INSERT INTO inventory (emp_id, item_name, serial_number, assigned_date, status) VALUES (?, ?, ?, ?, 'Assigned')",
              (emp_id, inv_name, inv_sr, datetime.now().strftime("%Y-%m-%d"))
          )
          conn.commit()
          conn.close()
          st.success("Item Assigned!")
          st.rerun()

      # Display & Return Inventory
      conn = get_connection()
      df_i = pd.read_sql_query(f"SELECT id, item_name, serial_number, assigned_date, status FROM inventory WHERE emp_id = '{emp_id}'", conn)
      conn.close()

      if not df_i.empty:
        st.dataframe(df_i[["item_name", "serial_number", "assigned_date", "status"]], use_container_width=True)

        # Return Item Option
        assigned_items = df_i[df_i['status'] == 'Assigned']
        if not assigned_items.empty:
          item_to_return = st.selectbox("Select Item to Return / Mark Returned", assigned_items['id'].tolist(), format_func=lambda x: f"{df_i.loc[df_i['id']==x, 'item_name'].values[0]} ({df_i.loc[df_i['id']==x, 'serial_number'].values[0]})")
          if st.button("Mark as Returned"):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE inventory SET status = 'Returned' WHERE id = ?", (item_to_return,))
            conn.commit()
            conn.close()
            st.success("Item marked as Returned!")
            st.rerun()
      else:
        st.caption("No inventory assigned yet.")

    # DOCUMENTS BOX
    with col_doc:
      st.markdown("### 📄 Documents Management")

      with st.form("add_doc_form"):
        d_name = st.text_input("Doc Name (e.g. Aadhar)")
        d_file = st.file_uploader("Choose File")
        d_btn = st.form_submit_button("Upload Document")

        if d_btn and d_name and d_file:
          os.makedirs("uploads", exist_ok=True)
          f_path = os.path.join("uploads", f"{emp_id}_{d_file.name}")
          with open(f_path, "wb") as f:
            f.write(d_file.getbuffer())

          conn = get_connection()
          cursor = conn.cursor()
          cursor.execute(
              "INSERT INTO documents (emp_id, doc_name, file_path, upload_date) VALUES (?, ?, ?, ?)",
              (emp_id, d_name, f_path, datetime.now().strftime("%Y-%m-%d"))
          )
          conn.commit()
          conn.close()
          st.success("Document Uploaded!")
          st.rerun()

      # Display Docs
      conn = get_connection()
      df_d = pd.read_sql_query(f"SELECT doc_name, file_path, upload_date FROM documents WHERE emp_id = '{emp_id}'", conn)
      conn.close()

      if not df_d.empty:
        st.dataframe(df_d, use_container_width=True)
      else:
        st.caption("No documents uploaded yet.")

# ------------------------------------------------------------------------------
# 2. ADD NEW EMPLOYEE
# ------------------------------------------------------------------------------
elif choice == "Add New Employee":
  st.subheader("➕ Register New Employee")

  with st.form("add_emp_main"):
    emp_id = st.text_input("Employee ID (e.g. EMP001)")
    name = st.text_input("Full Name")
    joining_date = st.date_input("Joining Date", value=datetime.now())

    submit = st.form_submit_button("Save Employee")

    if submit:
      if not emp_id or not name:
        st.error("Emp ID aur Name dono zaroori hain!")
      else:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT emp_id FROM employees WHERE emp_id = ?", (emp_id,))
        if cursor.fetchone():
          st.error(f"Emp ID {emp_id} pehle se maujood hai!")
        else:
          j_str = joining_date.strftime("%Y-%m-%d")
          c_end = (joining_date + relativedelta(months=6)).strftime("%Y-%m-%d")
          cursor.execute(
              """
                INSERT INTO employees (emp_id, name, joining_date, cl_balance, sl_balance, pl_balance, cycle_start, cycle_end)
                VALUES (?, ?, ?, 3.0, 3.0, 1.0, ?, ?)
              """,
              (emp_id, name, j_str, j_str, c_end)
          )
          conn.commit()
          st.success(f"Employee {name} registered successfully!")
        conn.close()

# ------------------------------------------------------------------------------
# 3. ALL EMPLOYEES LIST
# ------------------------------------------------------------------------------
elif choice == "All Employees List":
  st.subheader("📋 Master Directory")
  conn = get_connection()
  df = pd.read_sql_query("SELECT * FROM employees", conn)
  conn.close()
  st.dataframe(df, use_container_width=True)
