# ==============================================================================
# 7. LEAVE TRACKER (WITH LIVE LEAVE BALANCE)
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

        # Fetch balances and active pending count
        conn = get_db_connection()
        bal = pd.read_sql_query("SELECT * FROM leave_balances WHERE emp_id=?", conn, params=(selected_emp['emp_id'],))
        pending_count_df = pd.read_sql_query("SELECT COUNT(*) as p_count FROM leave_requests WHERE emp_id=? AND status='Pending'", conn, params=(selected_emp['emp_id'],))
        conn.close()

        p_count = pending_count_df.iloc[0]['p_count'] if len(pending_count_df) > 0 else 0

        if len(bal) > 0:
            b = bal.iloc[0]
            st.markdown(f"""
            <div style="background-color: #e8f4f8; padding: 12px 15px; border-radius: 5px; border-left: 4px solid #00c0ef; margin-bottom: 15px;">
                <b>📊 {selected_emp['emp_name']} Leave Summary:</b><br>
                • Casual Leave (CL): <b>{b['cl']}</b> &nbsp;|&nbsp; 
                • Sick Leave (SL): <b>{b['sl']}</b> &nbsp;|&nbsp; 
                • Paid Leave (PL): <b>{b['pl']}</b> &nbsp;|&nbsp; 
                • Special Paid Leave: <b>{b['paid_leave']}</b> <br>
                <span style="color: #d9534f; font-weight: bold;">⏳ Pending Requests for Approval: {p_count}</span>
            </div>
            """, unsafe_allow_html=True)

        if days_completed < 90:
            st.error(f"⚠️ **Not Eligible:** Employee ko joining kiye hue 3 months (90 days) nahi hue hain. (Completed: {days_completed} days)")
        else:
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
                    st.rerun()

# ==============================================================================
# 8. LEAVE MANAGEMENT (WITH DELETE OPTION & PENDING STATUS)
# ==============================================================================
elif main_menu == "📑 Leave Management":
    st.markdown("<h2 style='color:#333; font-weight:400;'>Leave Approvals & Management</h2>", unsafe_allow_html=True)
    
    conn = get_db_connection()
    
    # Query to fetch leave requests with pending count for each employee
    df_requests = pd.read_sql_query("""
        SELECT l.id, l.emp_id, e.emp_name, l.leave_type, l.from_date, l.to_date, l.reason, l.status
        FROM leave_requests l
        LEFT JOIN employees e ON l.emp_id = e.emp_id
        ORDER BY l.id DESC
    """, conn)
    
    # Pending leave counts summary
    df_pending_summary = pd.read_sql_query("""
        SELECT e.emp_id, e.emp_name, COUNT(l.id) as pending_leaves
        FROM employees e
        LEFT JOIN leave_requests l ON e.emp_id = l.emp_id AND l.status = 'Pending'
        GROUP BY e.emp_id
        HAVING pending_leaves > 0
    """, conn)
    
    conn.close()
    
    # Top Pending Leaves Summary Card
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
        st.success("🎉 Sabhi employees ki leave requests reviewed hain. Koi pending request nahi hai!")

    st.write("")
    st.markdown("##### 📜 All Leave Requests")
    
    if len(df_requests) == 0:
        st.info("Koi leave request record nahi hai.")
    else:
        for idx, row in df_requests.iterrows():
            status_color = "#f39c12" if row['status'] == 'Pending' else ("#28a745" if row['status'] == 'Approved' else "#dc3545")
            
            with st.expander(f"👤 {row['emp_name'] or 'Unknown'} ({row['emp_id']}) — {row['leave_type']} [{row['status']}]", expanded=(row['status'] == 'Pending')):
                c1, c2, c3 = st.columns([2, 2, 1])
                with c1:
                    st.write(f"**From Date:** {row['from_date']}")
                    st.write(f"**To Date:** {row['to_date']}")
                with c2:
                    st.write(f"**Reason:** {row['reason'] or 'N/A'}")
                    st.markdown(f"**Status:** <span style='color:{status_color}; font-weight:bold;'>{row['status']}</span>", unsafe_allow_html=True)
                
                st.write("")
                btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
                
                # Approve Button
                if row['status'] == 'Pending':
                    if btn_col1.button("✅ Approve", key=f"app_{row['id']}"):
                        conn = get_db_connection()
                        conn.cursor().execute("UPDATE leave_requests SET status='Approved' WHERE id=?", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.toast(f"Leave request approved!")
                        st.rerun()
                        
                    if btn_col2.button("❌ Reject", key=f"rej_{row['id']}"):
                        conn = get_db_connection()
                        conn.cursor().execute("UPDATE leave_requests SET status='Rejected' WHERE id=?", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.toast(f"Leave request rejected!")
                        st.rerun()

                # Delete Button Available for ALL requests
                if btn_col3.button("🗑️ Delete Request", key=f"del_req_{row['id']}"):
                    conn = get_db_connection()
                    conn.cursor().execute("DELETE FROM leave_requests WHERE id=?", (row['id'],))
                    conn.commit()
                    conn.close()
                    st.toast("Leave Request Deleted!")
                    st.rerun()
