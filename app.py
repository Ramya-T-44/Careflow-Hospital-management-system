import streamlit as st
import pyodbc
import pandas as pd
from datetime import date

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="CareFlow Hospital", layout="wide")

# ---------------- SAFE TYPE ----------------
def safe(x):
    return x.item() if hasattr(x, "item") else x

# ---------------- UI ----------------
st.markdown("""
<style>
body { background-color: #f4f7fb; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e3a8a, #2563eb);
    color: white;
}
[data-testid="stSidebar"] * { color: white !important; }

.header {
    font-size: 28px;
    font-weight: bold;
    color: #1e3a8a;
}

.card {
    padding: 20px;
    border-radius: 15px;
    background: white;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.1);
    transition: 0.3s;
    animation: fadeIn 0.5s ease-in;
}
.card:hover { transform: scale(1.03); }

@keyframes fadeIn {
    from {opacity: 0; transform: translateY(10px);}
    to {opacity: 1; transform: translateY(0);}
}

.stButton>button {
    background: linear-gradient(90deg, #2563eb, #1e40af);
    color: white;
    border-radius: 10px;
    height: 45px;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# ---------------- DB CONNECTION ----------------
def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=careflow_system;"
        "Trusted_Connection=yes;"
    )
# ---------------- DB HELPER ----------------
def execute_query(query, params=(), fetch=False):
    conn = get_connection()
    cur = conn.cursor()

    # ✅ convert all params safely
    clean_params = tuple(safe(p) for p in params)

    cur.execute(query, clean_params)

    data = None
    if fetch:
        data = cur.fetchall()

    conn.commit()
    conn.close()
    return data


def fetch_df(query, params=()):
    conn = get_connection()
    clean_params = tuple(safe(p) for p in params)
    df = pd.read_sql(query, conn, params=clean_params)
    conn.close()
    return df

# ---------------- LOGIN ----------------
def login():
    st.markdown("<h1 style='text-align:center;'>🏥 CareFlow Login</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)

        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")

        if st.button("Login"):
            conn = get_connection()
            df = pd.read_sql(
                "SELECT * FROM Users WHERE username=? AND password=?",
                conn, params=[user, pwd]
            )

            if not df.empty:
                st.session_state["logged_in"] = True
                st.session_state["user_id"] = int(df.iloc[0]["user_id"])
                st.session_state["role"] = df.iloc[0]["role"]
                st.session_state["username"] = df.iloc[0]["username"]
                st.rerun()
            else:
                st.error("Invalid credentials")

            conn.close()

        st.markdown('</div>', unsafe_allow_html=True)

# ---------------- LOGOUT ----------------
def logout():
    st.session_state.clear()
    st.rerun()

# ---------------- DASHBOARD ----------------
def dashboard():
    conn = get_connection()
    p = pd.read_sql("SELECT COUNT(*) c FROM PatientMst", conn)["c"][0]
    d = pd.read_sql("SELECT COUNT(*) c FROM DoctorMst", conn)["c"][0]
    a = pd.read_sql("SELECT COUNT(*) c FROM Appointment", conn)["c"][0]
    adm = pd.read_sql("SELECT COUNT(*) c FROM Admission WHERE status='Admitted'", conn)["c"][0]

    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(f"<div class='card'><h3>👨‍⚕️ Patients</h3><h1>{p}</h1></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='card'><h3>🩺 Doctors</h3><h1>{d}</h1></div>", unsafe_allow_html=True)
    col3.markdown(f"<div class='card'><h3>📅 Appointments</h3><h1>{a}</h1></div>", unsafe_allow_html=True)
    col4.markdown(f"<div class='card'><h3>🏥 Admitted Patients</h3><h1>{adm}</h1></div>", unsafe_allow_html=True)

    st.subheader("📊 Disease Distribution")
    df = pd.read_sql("SELECT disease FROM PatientMst", conn)
    if not df.empty and 'disease' in df.columns:
        data = df['disease'].value_counts().reset_index()
        data.columns = ['Disease', 'Patients']
        st.bar_chart(data.set_index('Disease')[['Patients']], use_container_width=True)
    else:
        st.warning("No disease data available")
    conn.close()

# ---------------- ADMIN ----------------
# ---------------- ADMIN PANEL ----------------
def admin_panel():
    st.subheader("👨‍💼 Admin Panel")
    conn = get_connection()

    tab1, tab2 = st.tabs(["View/Delete Users", "Add User"])

    # -------- VIEW + DELETE INDIVIDUAL USERS --------
    with tab1:
        users = pd.read_sql("SELECT user_id, username, role, full_name, mobile FROM Users", conn)

        if not users.empty:
            st.dataframe(users)

            # Select a user to delete
            user_display = users.apply(
                lambda x: f"{x['username']} ({x['role']}) - ID:{x['user_id']}", axis=1
            )
            selected = st.selectbox("Select User to Delete", user_display)
            user_id = int(users.iloc[user_display[user_display == selected].index[0]]["user_id"])

            # Prevent deleting yourself
            if user_id == st.session_state["user_id"]:
                st.warning("❌ You cannot delete your own account")
            else:
                if st.button("Delete Selected User"):
                    try:
                        cur = conn.cursor()
                        # Delete doctor entry first if any
                        cur.execute("DELETE FROM DoctorMst WHERE user_id=?", (user_id,))
                        # Then delete user
                        cur.execute("DELETE FROM Users WHERE user_id=?", (user_id,))
                        conn.commit()
                        st.success("User deleted successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
        else:
            st.info("No users found")

    # -------- ADD USER --------
    with tab2:
        username = st.text_input("Username")
        password = st.text_input("Password")
        role = st.selectbox("Role", ["Admin", "Doctor", "Receptionist"])
        name = st.text_input("Full Name")
        mobile = st.text_input("Mobile Number")

        if role == "Doctor":
            speciality = st.text_input("Speciality")

        if st.button("Add User"):
            if not (mobile.isdigit() and len(mobile) == 10):
                st.error("Enter valid 10-digit mobile number")
            else:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO Users (username, password, role, full_name, mobile)
                    OUTPUT INSERTED.user_id
                    VALUES (?, ?, ?, ?, ?)
                """, (username, password, role, name, mobile))

                user_id = cur.fetchone()[0]

                if role == "Doctor":
                    cur.execute("""
                        INSERT INTO DoctorMst (user_id, speciality, mobile)
                        VALUES (?, ?, ?)
                    """, (user_id, speciality, mobile))

                conn.commit()
                st.success("User added successfully")

    conn.close()
# ---------------- DOCTOR ----------------
def doctor_panel():
    st.title("👨‍⚕️ Doctor Panel")
    username = st.session_state.get("username")
    if not username:
        st.error("Please login first")
        return

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Get Doctor ID
        cur.execute("""
            SELECT d.DID
            FROM DoctorMst d
            JOIN Users u ON d.user_id = u.user_id
            WHERE u.username = ?
        """, (username,))
        doc = cur.fetchone()
        if not doc:
            st.error("Doctor not found")
            return
        DID = doc[0]

        # 🔍 SEARCH PATIENT
        search = st.text_input("🔍 Search Patient (Name / Phone)")

        if search:
            cur.execute("""
                SELECT PID, name FROM PatientMst
                WHERE name LIKE ? OR phone LIKE ?
            """, (f"%{search}%", f"%{search}%"))
        else:
            cur.execute("SELECT PID, name FROM PatientMst")

        patients = cur.fetchall()

        if not patients:
            st.warning("No patients available")
            return

        patient_dict = {f"{p[1]} (ID: {p[0]})": p[0] for p in patients}
        selected_patient = st.selectbox("Select Patient", list(patient_dict.keys()))
        PID = patient_dict[selected_patient]

        # ✅ FULL PATIENT DETAILS
        cur.execute("""
            SELECT name, age, phone, blood_group, disease, medical_history
            FROM PatientMst WHERE PID=?
        """, (PID,))
        pdata = cur.fetchone()

        if pdata:
            st.markdown(f"""
            <div class='card'>
            <h3>📋 Patient Full Details</h3>
            Name: {pdata[0]}<br>
            Age: {pdata[1]}<br>
            Phone: {pdata[2]}<br>
            Blood Group: {pdata[3]}<br>
            Disease: {pdata[4]}<br>
            History: {pdata[5]}
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # ✅ PREVIOUS APPOINTMENTS
        st.subheader("📅 Previous Appointments")
        appointments = pd.read_sql("""
            SELECT appointment_date, status
            FROM Appointment
            WHERE PID=? AND DID=?
            ORDER BY appointment_date DESC
        """, conn, params=[PID, DID])

        if not appointments.empty:
            st.dataframe(appointments)
        else:
            st.info("No appointments found")

        st.divider()

        # ✅ MEDICAL RECORDS
        st.subheader("📋 Medical Records")
        records = pd.read_sql("""
            SELECT record_id, diagnosis, treatment, notes
            FROM MedicalRecord
            WHERE PID=? AND DID=?
        """, conn, params=[PID, DID])

        if not records.empty:
            st.dataframe(records)
        else:
            st.info("No records found")

        st.divider()

        # ✅ TIMELINE (AUTO HISTORY)
        st.subheader("🕒 Patient History Timeline")

        timeline = pd.read_sql("""
            SELECT appointment_date AS date, 'Appointment' AS type, status AS detail
            FROM Appointment WHERE PID=?

            UNION ALL

            SELECT GETDATE() AS date, 'Medical Record', diagnosis
            FROM MedicalRecord WHERE PID=?
        """, conn, params=[PID, PID])

        if not timeline.empty:
            timeline = timeline.sort_values(by="date", ascending=False)
            for _, row in timeline.iterrows():
                st.markdown(f"""
                <div class='card'>
                <b>{row['type']}</b><br>
                Date: {row['date']}<br>
                Detail: {row['detail']}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No timeline data")

        st.divider()

        # ➕ ADD RECORD
        st.subheader("➕ Add Medical Record")
        diagnosis = st.text_input("Diagnosis")
        treatment = st.text_input("Treatment")
        notes = st.text_area("Notes")

        if st.button("Add Record"):
            if diagnosis and treatment:
                cur.execute("""
                    INSERT INTO MedicalRecord (PID, DID, diagnosis, treatment, notes)
                    VALUES (?, ?, ?, ?, ?)
                """, (PID, DID, diagnosis, treatment, notes))
                conn.commit()
                st.success("Record added successfully")
                st.rerun()
            else:
                st.warning("Please fill required fields")

    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        conn.close()
# ---------------- RECEPTIONIST ----------------
def receptionist_panel():
    st.subheader("📋 Reception Panel")

    tab1, tab2, tab3, tab4 = st.tabs([
        "➕ Add Patient", 
        "📅 Book Appointment", 
        "🏥 Admit/Discharge", 
        "💰 Billing"
    ])

    # ---------------- Add Patient ----------------
    with tab1:
        name = st.text_input("Patient Name")
        address = st.text_input("Address")
        disease = st.text_input("Disease")
        age = st.number_input("Age", min_value=0, step=1)
        blood_group = st.text_input("Blood Group")
        phone = st.text_input("Phone (10 digits)")

        if st.button("Add Patient"):
            if not name.strip():
                st.error("Patient name required")
            elif age <= 0:
                st.error("Enter valid age")
            elif not (phone.isdigit() and len(phone) == 10):
                st.error("Phone must be 10 digits")
            else:
                execute_query("""
                    INSERT INTO PatientMst 
                    (name, address, disease, age, blood_group, phone)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, address, disease, int(age), blood_group, phone))

                st.success("Patient added successfully")

    # ---------------- Book Appointment ----------------
    with tab2:
        patients = fetch_df("SELECT PID, name, disease FROM PatientMst")

        if not patients.empty:
            p_display = patients.apply(lambda x: f"{x['name']} (ID:{x['PID']})", axis=1)
            selected = st.selectbox("Select Patient", p_display)

            row = patients.iloc[p_display[p_display == selected].index[0]]
            pid = int(row["PID"])
            disease = row["disease"]

            st.info(f"Patient Disease: {disease}")

            doctors = fetch_df("""
                SELECT d.DID, u.full_name, d.speciality
                FROM DoctorMst d
                JOIN Users u ON d.user_id = u.user_id
                WHERE d.speciality LIKE ?
            """, (f"%{disease}%",))

            if not doctors.empty:
                doc_display = doctors.apply(lambda x: f"{x['full_name']} ({x['speciality']})", axis=1)
                selected_doc = st.selectbox("Select Doctor", doc_display)

                drow = doctors.iloc[doc_display[doc_display == selected_doc].index[0]]
                did = int(drow["DID"])

                rooms = fetch_df("SELECT RID FROM RoomMst WHERE available_rooms > 0")

                if not rooms.empty:
                    rid = int(st.selectbox("Select Room", rooms["RID"]))
                    date_input = st.date_input("Select Date")

                    if st.button("Book Appointment"):
                        execute_query(
                            "UPDATE RoomMst SET available_rooms = available_rooms - 1 WHERE RID=?",
                            (rid,)
                        )

                        execute_query("""
                            INSERT INTO Appointment (PID, DID, RID, appointment_date, status)
                            VALUES (?, ?, ?, ?, 'Booked')
                        """, (pid, did, rid, date_input))

                        st.success("Appointment booked successfully")
                else:
                    st.warning("No rooms available")
            else:
                st.warning("No matching doctor available")

        else:
            st.warning("No patients available")

    # ---------------- Admit / Discharge ----------------
    with tab3:
        st.subheader("🏥 Admit or Discharge Patient")

        admissions = fetch_df("""
            SELECT a.admission_id, p.name, r.room_type, a.status
            FROM Admission a
            JOIN PatientMst p ON a.PID = p.PID
            JOIN RoomMst r ON a.RID = r.RID
        """)

        if not admissions.empty:
            options = admissions.apply(
                lambda x: f"{x['name']} (Room: {x['room_type']}) - {x['status']}", axis=1
            )

            selected = st.selectbox("Select Admission", options)
            adm_id = int(admissions.iloc[options[options == selected].index[0]]["admission_id"])

            if st.button("Discharge Patient"):
                execute_query("""
                    UPDATE Admission 
                    SET status='Discharged', discharge_date=GETDATE() 
                    WHERE admission_id=?
                """, (adm_id,))

                st.success("Patient discharged successfully")

        else:
            st.info("No admissions found")

        st.divider()

        # ➕ Admit Patient
        st.subheader("➕ Admit Patient")

        patients = fetch_df("""
            SELECT PID, name FROM PatientMst 
            WHERE PID NOT IN (
                SELECT PID FROM Admission WHERE status='Admitted'
            )
        """)

        if not patients.empty:
            p_display = patients.apply(lambda x: f"{x['name']} (ID:{x['PID']})", axis=1)
            selected = st.selectbox("Select Patient to Admit", p_display)

            pid = int(patients.iloc[p_display[p_display == selected].index[0]]["PID"])

            rooms = fetch_df("SELECT RID FROM RoomMst WHERE available_rooms > 0")

            if not rooms.empty:
                rid = int(st.selectbox("Select Room", rooms["RID"]))
                admit_date = st.date_input("Admit Date")

                if st.button("Admit Patient"):
                    execute_query(
                        "UPDATE RoomMst SET available_rooms = available_rooms - 1 WHERE RID=?",
                        (rid,)
                    )

                    execute_query("""
                        INSERT INTO Admission (PID, RID, admit_date, status)
                        VALUES (?, ?, ?, 'Admitted')
                    """, (pid, rid, admit_date))

                    st.success("Patient admitted successfully")
            else:
                st.warning("No rooms available")
        else:
            st.warning("No patients available")

    # ---------------- Billing ----------------
    with tab4:
        st.subheader("💰 Generate Bill")

        appointments = fetch_df("""
            SELECT a.AID, p.PID, p.name, rm.room_type, rm.price, a.status
            FROM Appointment a
            JOIN PatientMst p ON a.PID = p.PID
            JOIN RoomMst rm ON a.RID = rm.RID
        """)

        if not appointments.empty:
            p_display = appointments.apply(
                lambda x: f"{x['name']} (PID:{x['PID']})", axis=1
            )

            selected = st.selectbox("Select Patient", p_display)
            selected_pid = int(appointments.iloc[p_display[p_display == selected].index[0]]["PID"])

            patient_apps = appointments[appointments["PID"] == selected_pid]

            if st.button("Generate Bill"):
                st.dataframe(patient_apps)
                total = float(patient_apps["price"].sum())
                st.success(f"Total Bill: ₹{total}")
        else:
            st.warning("No appointments found")    

    conn.close()
# ---------------- CHANGE PASSWORD ----------------
def change_password():
    st.subheader("🔑 Change Password")
    username = st.session_state.get("username", "")
    old_password = st.text_input("Old Password", type="password")
    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    if st.button("Update Password"):
        if new_password != confirm_password:
            st.error("New passwords do not match!")
            return
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE username=? AND password=?", (username, old_password))
        user = cursor.fetchone()
        if user:
            cursor.execute("UPDATE Users SET password=? WHERE username=?", (new_password, username))
            conn.commit()
            st.success("Password updated successfully!")
        else:
            st.error("Old password is incorrect")
        conn.close()

# ---------------- MAIN ----------------
def main():
    st.sidebar.title("🏥 CareFlow")
    st.sidebar.markdown(f"👤 **{st.session_state.get('username','')}**  \n🛡️ Role: **{st.session_state.get('role','')}**")
    if st.sidebar.button("🚪 Logout"):
        logout()
    menu = st.sidebar.radio("Navigation", [
        "🏠 Dashboard",
        "👨‍💼 Admin",
        "🩺 Doctor",
        "📋 Reception",
        "🔐 Change Password"
    ])
    st.markdown('<div class="header">🏥 CareFlow Hospital Dashboard</div>', unsafe_allow_html=True)
    if menu == "🏠 Dashboard":
        dashboard()
    elif menu == "👨‍💼 Admin" and st.session_state["role"] == "Admin":
        admin_panel()
    elif menu == "🩺 Doctor" and st.session_state["role"] == "Doctor":
        doctor_panel()
    elif menu == "📋 Reception" and st.session_state["role"] == "Receptionist":
        receptionist_panel()
    elif menu == "🔐 Change Password":
        change_password()
    else:
        st.warning("Access Denied")

# ---------------- START ----------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if not st.session_state["logged_in"]:
    login()
else:
    main()