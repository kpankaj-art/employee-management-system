from datetime import datetime
import os
import sqlite3
from dateutil.relativedelta import relativedelta
import pandas as pd
import streamlit as st

# ==============================================================================
# DATABASE SETUP & LOGIC
# ==============================================================================


def init_db():
  """SQLite Database Tables create karta hai."""
  conn = sqlite3.connect("employee_management.db")
  cursor = conn.cursor()

  # Employee Master Table
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            emp_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            joining_date TEXT NOT NULL,
            cl_balance REAL DEFAULT 3.0,
            sl_balance REAL DEFAULT 3.0,
            pl_balance REAL DEFAULT 1.0,
            cycle_start TEXT NOT NULL,
            cycle_end TEXT NOT NULL
        )
    """)

  # Inventory Table
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT,
            item_name TEXT,
            serial_number TEXT,
            assigned_date TEXT,
            FOREIGN KEY (emp_id) REFERENCES employees (emp_id)
        )
    """)

  # Documents Table
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT,
            doc_name TEXT,
            file_path TEXT,
            upload_date TEXT,
            FOREIGN KEY (emp_id) REFERENCES employees (emp_id)
        )
    """)

  conn.commit()
  conn.close()


def get_connection():
  return sqlite3.connect("employee_management.db")


# Helper: Check and Carry Forward Leave Cycle
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

    # Agar current date/leave date cycle end date ko cross kar chuki hai
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
# STREAMLIT UI CODE
# ==============================================================================

st.set_page_config(
    page_title="Employee Management System", page_icon="🏢", layout="wide"
)
init_db()

st.title("🏢 Employee, Leave & Inventory Management System")

# Sidebar Menu
menu = [
    "Dashboard / All Employees",
    "Add New Employee",
    "Leave Management",
    "Inventory & Documents",
    "Export to Excel",
]
choice = st.sidebar.selectbox("Navigation Menu", menu)

# ------------------------------------------------------------------------------
# 1. DASHBOARD / ALL EMPLOYEES
# ------------------------------------------------------------------------------
if choice == "Dashboard / All Employees":
  st.subheader("👥 Employee Directory & Status")

  conn = get_connection()
  df_emp = pd.read_sql_query("SELECT * FROM employees", conn)
  conn.close()

  if df_emp.empty:
    st.info("Abhi koi employee registered nahi hai. Sidebar se naya employee add karein.")
  else:
    st.dataframe(df_emp, use_container_width=True)

# ------------------------------------------------------------------------------
# 2. ADD NEW EMPLOYEE
# ------------------------------------------------------------------------------
elif choice == "Add New Employee":
  st.subheader("➕ Add New Employee")

  with st.form("add_emp_form"):
    emp_id = st.text_input("Employee ID (e.g., EMP001)")
    name = st.text_input("Full Name")
    joining_date = st.date_input("Joining Date", value=datetime.now())

    submit = st.form_submit_button("Register Employee")

    if submit:
      if not emp_id or not name:
        st.error("Kripya Emp ID aur Name dono fill karein!")
      else:
        conn = get_connection()
        cursor = conn.cursor()

        # Check existing ID
        cursor.execute(
            "SELECT emp_id FROM employees WHERE emp_id = ?", (emp_id,)
        )
        if cursor.fetchone():
          st.error(f"Emp ID {emp_id} pehle se exist karti hai!")
        else:
          j_date = joining_date.strftime("%Y-%m-%d")
          c_start = j_date
          c_end = (joining_date + relativedelta(months=6)).strftime("%Y-%m-%d")

          cursor.execute(
              """
                        INSERT INTO employees (emp_id, name, joining_date, cl_balance, sl_balance, pl_balance, cycle_start, cycle_end)
                        VALUES (?, ?, ?, 3.0, 3.0, 1.0, ?, ?)
                    """,
              (emp_id, name, j_date, c_start, c_end),
          )
          conn.commit()
          st.success(
              f"Employee {name} ({emp_id}) successfully register ho gaye!"
          )
        conn.close()

# ------------------------------------------------------------------------------
# 3. LEAVE MANAGEMENT
# ------------------------------------------------------------------------------
elif choice == "Leave Management":
  st.subheader("🌴 Leave Application & Rules")

  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute("SELECT emp_id, name, joining_date FROM employees")
  emp_list = cursor.fetchall()
  conn.close()

  if not emp_list:
    st.warning("Pehle kisi employee ko register karein.")
  else:
    emp_dict = {f"{row[0]} - {row[1]}": row for row in emp_list}
    selected_emp_str = st.selectbox("Select Employee", list(emp_dict.keys()))
    selected_emp = emp_dict[selected_emp_str]

    emp_id, emp_name, j_date_str = (
        selected_emp[0],
        selected_emp[1],
        selected_emp[2],
    )
    j_date = datetime.strptime(j_date_str, "%Y-%m-%d").date()

    # Rule Details
    active_date = j_date + relativedelta(months=3)
    st.info(
        f"📌 **Joining Date:** {j_date} | **Leave Activation Date (3 Months"
        f" Rule):** {active_date}"
    )

    # Check Leaves Form
    with st.form("apply_leave_form"):
      leave_type = st.selectbox("Leave Type", ["CL", "SL", "PL"])
      days = st.number_input(
          "Number of Days", min_value=0.5, max_value=30.0, step=0.5
      )
      apply_date = st.date_input("Leave Date", value=datetime.now())

      apply_btn = st.form_submit_button("Apply Leave")

      if apply_btn:
        app_date = apply_date

        # Rule 1: 3-Month Probation Check
        if app_date < active_date:
          st.error(
              f"❌ **Leave Rejected:** Employee joining date se 3 mahine"
              f" complete nahi hue hain. Activation date: {active_date}"
          )
        else:
          # Auto-update 6-month cycle carry forward
          sync_leave_cycles(emp_id, app_date.strftime("%Y-%m-%d"))

          # Fetch updated balance
          conn = get_connection()
          cursor = conn.cursor()
          col_map = {"CL": "cl_balance", "SL": "sl_balance", "PL": "pl_balance"}
          cursor.execute(
              f"SELECT {col_map[leave_type]} FROM employees WHERE emp_id = ?",
              (emp_id,),
          )
          current_bal = cursor.fetchone()[0]

          # Rule 2: Balance Check
          if current_bal >= days:
            new_bal = current_bal - days
            cursor.execute(
                f"UPDATE employees SET {col_map[leave_type]} = ? WHERE emp_id"
                " = ?",
                (new_bal, emp_id),
            )
            conn.commit()
            st.success(
                f"✅ **Leave Approved!** Remaining {leave_type} Balance:"
                f" {new_bal}"
            )
          else:
            st.error(
                f"❌ **Insufficient Balance!** Available {leave_type}:"
                f" {current_bal}"
            )

          conn.close()

# ------------------------------------------------------------------------------
# 4. INVENTORY & DOCUMENTS
# ------------------------------------------------------------------------------
elif choice == "Inventory & Documents":
  st.subheader("📦 Inventory & Document Records")

  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute("SELECT emp_id, name FROM employees")
  emp_list = cursor.fetchall()
  conn.close()

  if not emp_list:
    st.warning("Pehle kisi employee ko register karein.")
  else:
    emp_dict = {f"{row[0]} - {row[1]}": row[0] for row in emp_list}
    selected_emp_str = st.selectbox(
        "Select Employee to Manage Data", list(emp_dict.keys())
    )
    emp_id = emp_dict[selected_emp_str]

    col1, col2 = st.columns(2)

    # Inventory Section
    with col1:
      st.markdown("### 💻 Assign Inventory")
      item_name = st.text_input("Item Name (e.g., Laptop, Mobile)")
      serial_no = st.text_input("Serial Number")
      if st.button("Assign Item"):
        if item_name and serial_no:
          conn = get_connection()
          cursor = conn.cursor()
          cursor.execute(
              """
                        INSERT INTO inventory (emp_id, item_name, serial_number, assigned_date)
                        VALUES (?, ?, ?, ?)
                    """,
              (
                  emp_id,
                  item_name,
                  serial_no,
                  datetime.now().strftime("%Y-%m-%d"),
              ),
          )
          conn.commit()
          conn.close()
          st.success("Inventory Assign ho gayi!")
        else:
          st.error("Sabhi fields fill karein!")

      # Display assigned inventory
      conn = get_connection()
      df_inv = pd.read_sql_query(
          f"SELECT item_name, serial_number, assigned_date FROM inventory"
          f" WHERE emp_id = '{emp_id}'",
          conn,
      )
      conn.close()
      st.markdown("**Assigned Items:**")
      st.dataframe(df_inv, use_container_width=True)

    # Document Section
    with col2:
      st.markdown("### 📄 Documents Tracking")
      doc_name = st.text_input("Document Name (e.g., Aadhar, Resume)")
      doc_file = st.file_uploader("Upload File")

      if st.button("Save Document Record"):
        if doc_name and doc_file:
          # Save file locally in 'uploads' directory
          os.makedirs("uploads", exist_ok=True)
          file_path = os.path.join("uploads", f"{emp_id}_{doc_file.name}")
          with open(file_path, "wb") as f:
            f.write(doc_file.getbuffer())

          conn = get_connection()
          cursor = conn.cursor()
          cursor.execute(
              """
                        INSERT INTO documents (emp_id, doc_name, file_path, upload_date)
                        VALUES (?, ?, ?, ?)
                    """,
              (
                  emp_id,
                  doc_name,
                  file_path,
                  datetime.now().strftime("%Y-%m-%d"),
              ),
          )
          conn.commit()
          conn.close()
          st.success("Document Upload ho gaya!")
        else:
          st.error("Document Name aur File dono provide karein!")

      # Display documents
      conn = get_connection()
      df_doc = pd.read_sql_query(
          f"SELECT doc_name, file_path, upload_date FROM documents WHERE"
          f" emp_id = '{emp_id}'",
          conn,
      )
      conn.close()
      st.markdown("**Uploaded Documents:**")
      st.dataframe(df_doc, use_container_width=True)

# ------------------------------------------------------------------------------
# 5. EXPORT TO EXCEL
# ------------------------------------------------------------------------------
elif choice == "Export to Excel":
  st.subheader("📥 Export Employee Data to Excel")

  conn = get_connection()
  cursor = conn.cursor()
  cursor.execute("SELECT emp_id, name FROM employees")
  emp_list = cursor.fetchall()
  conn.close()

  if not emp_list:
    st.warning("Koi data export karne ke liye nahi hai.")
  else:
    emp_dict = {f"{row[0]} - {row[1]}": row[0] for row in emp_list}
    selected_emp_str = st.selectbox(
        "Select Employee for Excel Download", list(emp_dict.keys())
    )
    emp_id = emp_dict[selected_emp_str]

    if st.button("Generate Excel File"):
      conn = get_connection()

      # Fetch Dataframes
      df_profile = pd.read_sql_query(
          f"SELECT * FROM employees WHERE emp_id = '{emp_id}'", conn
      )
      df_inv = pd.read_sql_query(
          "SELECT item_name, serial_number, assigned_date FROM inventory WHERE"
          f" emp_id = '{emp_id}'",
          conn,
      )
      df_docs = pd.read_sql_query(
          "SELECT doc_name, file_path, upload_date FROM documents WHERE emp_id"
          f" = '{emp_id}'",
          conn,
      )

      conn.close()

      file_name = f"{emp_id}_Full_Report.xlsx"

      # Write sheets
      with pd.ExcelWriter(file_name, engine="openpyxl") as writer:
        df_profile.to_excel(
            writer, sheet_name="Profile & Leaves", index=False
        )
        df_inv.to_excel(writer, sheet_name="Inventory", index=False)
        df_docs.to_excel(writer, sheet_name="Documents", index=False)

      with open(file_name, "rb") as f:
        st.download_button(
            label="⬇️ Download Excel File",
            data=f,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )