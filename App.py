import os
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta
import streamlit as st

# ==============================================================================
# DATABASE SETUP
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
            status TEXT DEFAULT 'ontime',
            dob TEXT,
            joining_date TEXT NOT NULL,
            time_in TEXT DEFAULT '09:00 AM',
            time_out TEXT DEFAULT '06:00 PM',
            department TEXT DEFAULT 'DEVELOPMENT',
            designation TEXT DEFAULT 'SOFTWARE ENGINEER',
            ctc REAL DEFAULT 0.0,
            salary REAL DEFAULT 0.0
        )
    """
    )

    # Insert sample data if empty
    cursor.execute("SELECT COUNT(*) FROM employees")
    if cursor.fetchone()[0] == 0:
        sample_data = [
            ("LVO541238690", "King Bob", "2018-07-12", "11:56 PM", "12:00 AM", "ontime"),
            ("XRF342606719", "Bob King", "2018-07-12", "11:54 PM", "12:00 AM", "ontime"),
            ("VFT157620346", "Jack Hammer", "2018-07-12", "11:52 PM", "12:00 AM", "ontime"),
            ("ZTC714069832", "Logan Paul", "2018-07-12", "11:50 PM", "12:00 AM", "ontime"),
            ("BVH081749553", "Dave Dela Cruz", "2018-07-12", "11:46 PM", "12:00 AM", "ontime"),
            ("AEI036154829", "Alex Cohen", "2018-07-12", "01:57 PM", "12:00 AM", "late"),
            ("HSP067892134", "Nokia Grey", "2018-07-11", "06:21 PM", "12:00 AM", "late"),
            ("MGZ312906745", "Emily JK", "2018-07-11", "06:20 PM", "12:00 AM", "late"),
            ("CAB835624170", "Batang Pogi", "2018-07-11", "06:19 PM", "12:00 AM", "late"),
            ("IOV153842976", "Sophia Iwan", "2018-07-11", "06:18 PM", "12:00 AM", "late"),
        ]
        cursor.executemany(
            """
            INSERT INTO employees (emp_id, name, joining_date, time_in, time_out, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            sample_data
        )

    conn.commit()
    conn.close()

def get_connection():
    conn = sqlite3.connect("employee_management.db")
    return conn

# ==============================================================================
# UI CONFIG & EXACT STYLING
# ==============================================================================
st.set_page_config(
    page_title="Payroll and Attendance System",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

# Custom CSS matching exact Image (AdminLTE Dark Sidebar + Teal Topbar)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Source Sans Pro', 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
        background-color: #ECF0F5 !important;
    }
    
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}

    /* Sidebar Theme */
    [data-testid="stSidebar"] {
        background-color: #222D32 !important;
        padding-top: 0px !important;
    }
    [data-testid="stSidebar"] * {
        color: #B8C7CE !important;
    }
    
    .sidebar-brand {
        background-color: #008D4C;
        padding: 15px 20px;
        color: #FFFFFF !important;
        font-size: 20px;
        font-weight: 700;
        text-align: center;
        letter-spacing: 0.5px;
    }

    .profile-card {
        padding: 15px;
        display: flex;
        align-items: center;
        gap: 12px;
        background: #222D32;
    }
    .profile-avatar {
        width: 45px;
        height: 45px;
        border-radius: 50%;
        background-color: #F39C12;
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
        font-size: 11px;
    }

    .sidebar-section-header {
        color: #4B646F !important;
        background: #1A2226;
        padding: 8px 25px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
    }

    /* Top Navigation Bar */
    .top-header-bar {
        background-color: #00A65A;
        padding: 12px 20px;
        margin: -60px -60px 15px -60px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: white;
    }
    .top-header-title {
        font-size: 18px;
        font-weight: 600;
    }
    .top-header-user {
        font-size: 14px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Status Badges */
    .badge-ontime {
        background-color: #F39C12;
        color: white;
        padding: 2px 8px;
        border-radius: 3px;
        font-size: 11px;
        font-weight: 600;
    }
    .badge-late {
        background-color: #DD4B39;
        color: white;
        padding: 2px 8px;
        border-radius: 3px;
        font-size: 11px;
        font-weight: 600;
    }

    /* Custom Table Styling */
    .table-container {
        background: #FFFFFF;
        border-top: 3px solid #D2D6DE;
        border-radius: 3px;
        padding: 15px;
        box-shadow: 0 1px 1px rgba(0,0,0,0.1);
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Top Bar Header
st.markdown(
    """
    <div class="top-header-bar">
        <div class="top-header-title">☰ &nbsp; Payroll and Attendance System</div>
        <div class="top-header-user">
            <span style="background-color:#F39C12; width:26px; height:26px; border-radius:50%; display:inline-block; text-align:center; line-height:26px; font-weight:bold; font-size:12px;">A</span>
            Welcome Admin
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

# Sidebar Setup
st.sidebar.markdown('<div class="sidebar-brand">Payroll</div>', unsafe_allow_html=True)
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

st.sidebar.markdown('<div class="sidebar-section-header">REPORTS</div>', unsafe_allow_html=True)
st.sidebar.radio("REPORTS_NAV", ["📊 Dashboard"], label_visibility="collapsed")

st.sidebar.markdown('<div class="sidebar-section-header">MANAGE</div>', unsafe_allow_html=True)
menu = st.sidebar.radio(
    "MANAGE_NAV",
    ["📅 Attendance", "👥 Employees", "💳 Deductions", "💼 Positions"],
    label_visibility="collapsed"
)

st.sidebar.markdown('<div class="sidebar-section-header">PRINTABLES</div>', unsafe_allow_html=True)
st.sidebar.radio("PRINT_NAV", ["📄 Payroll", "🕒 Schedule"], label_visibility="collapsed")

# ==============================================================================
# MAIN WORKSPACE (ATTENDANCE DASHBOARD)
# ==============================================================================
if menu == "📅 Attendance":
    # Title & Breadcrumb
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.markdown("<h2 style='margin:0; color:#333; font-weight:400;'>Payroll and Attendance System</h2>", unsafe_allow_html=True)
    with col_t2:
        st.markdown("<p style='text-align:right; color:#777; font-size:12px;'>🏠 Home &nbsp;•&nbsp; Attendance</p>", unsafe_allow_html=True)

    st.write("")

    # Card Wrap
    with st.container():
        # Action Bar (+ New, Show entries, Search)
        btn_col, show_col, space_col, search_col = st.columns([1.5, 2, 3, 2.5])
        
        with btn_col:
            st.button("＋ New", type="primary", use_container_width=True)
            
        with show_col:
            st.selectbox("Show entries", [10, 25, 50, 100], label_visibility="collapsed")

        with search_col:
            search_query = st.text_input("Search", "", placeholder="Search:", label_visibility="collapsed")

        st.write("")

        # Fetch Data
        conn = get_connection()
        df = pd.read_sql_query("SELECT * FROM employees", conn)
        conn.close()

        if search_query:
            df = df[
                df["name"].str.contains(search_query, case=False, na=False) |
                df["emp_id"].str.contains(search_query, case=False, na=False)
            ]

        # Table Header
        h1, h2, h3, h4, h5, h6 = st.columns([2, 2.5, 2.5, 2.5, 2.5, 3])
        h1.markdown("**Date**")
        h2.markdown("**Employee ID**")
        h3.markdown("**Name**")
        h4.markdown("**Time In**")
        h5.markdown("**Time Out**")
        h6.markdown("**Tools**")
        st.markdown("<hr style='margin:5px 0px 15px 0px; border-color:#EEEEEE;'>", unsafe_allow_html=True)

        # Table Rows
        for _, row in df.iterrows():
            r1, r2, r3, r4, r5, r6 = st.columns([2, 2.5, 2.5, 2.5, 2.5, 3])

            # Format Date
            try:
                d_fmt = datetime.strptime(row["joining_date"], "%Y-%m-%d").strftime("%b %d, %Y")
            except:
                d_fmt = row["joining_date"]

            r1.write(d_fmt)
            r2.write(f"`{row['emp_id']}`")
            r3.write(row["name"])

            # Time In with Badge
            status_badge = f"<span class='badge-ontime'>ontime</span>" if row["status"] == "ontime" else f"<span class='badge-late'>late</span>"
            r4.markdown(f"{row['time_in']} &nbsp; {status_badge}", unsafe_allow_html=True)
            r5.write(row["time_out"])

            # Tools Buttons
            b_edit, b_del = r6.columns(2)
            b_edit.button("📝 Edit", key=f"edit_{row['emp_id']}", use_container_width=True)
            b_del.button("🗑️ Delete", key=f"del_{row['emp_id']}", use_container_width=True)

            st.markdown("<hr style='margin:8px 0px; border-color:#F4F4F4;'>", unsafe_allow_html=True)

        # Pagination Footer
        f_col1, f_col2 = st.columns([2, 1])
        f_col1.caption(f"Showing 1 to {len(df)} of {len(df)} entries")

else:
    st.info("Aap side menu se baki pages access kar sakte hain.")
