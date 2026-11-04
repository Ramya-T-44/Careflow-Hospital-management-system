🏥 CareFlow - Hospital Management System

CareFlow is an end-to-end Hospital Management System built with Streamlit, Python, and SQL Server (ODBC). It features role-based access control (RBAC), patient record management, appointment booking, room allocation, admission tracking, disease analytics, and automated billing generation.

✨ Key Features

🛡️ Role-Based Access Control (RBAC)

Admin: Manage, add, and remove system users (Doctors, Receptionists, Administrators).

Doctor: View assigned patients, inspect full patient histories, track treatment timelines, and log new medical records.

Receptionist: Register new patients, schedule appointments matching doctor specialties with patient conditions, manage room assignments/admissions, and process billing.

📊 Interactive Analytics & Dashboard

High-level KPI metrics (Total Patients, Doctors, Active Appointments, Admitted Patients).

Visual distribution chart analyzing patient diseases.

📋 Comprehensive Clinical Workflow

Multi-field patient records (Age, Blood Group, Medical History, Contact Info).

Dynamic availability updates for hospital rooms upon appointment/admission creation.

Patient history timeline tracking previous diagnoses, treatments, and appointments.

Automated billing calculation based on room type and service history.

🛠️ Tech Stack

Frontend / Dashboard Framework: Streamlit

Backend / Programming Language: Python 3.x

Database: Microsoft SQL Server

Database Driver: pyodbc (ODBC Driver 17 for SQL Server)

Data Manipulation: pandas

🗄️ Database Architecture

To run this application, set up a SQL Server database named careflow_system containing the following tables:

Users: Stores authentication details, full names, roles, and contacts.

DoctorMst: Stores doctor-specific details and specialties (linked to Users).

PatientMst: Stores patient personal info, medical history, and blood group.

RoomMst: Tracks room types, pricing, and available counts.

Appointment: Tracks patient appointments with assigned doctors and rooms.

Admission: Tracks patient admission dates and current status (Admitted / Discharged).

MedicalRecord: Stores diagnosis log history per doctor and patient.

🚀 Getting Started

1. Prerequisites

Ensure you have the following installed:

Python 3.8+

Microsoft SQL Server

ODBC Driver 17 for SQL Server

2. Installation

Clone the repository:

git clone https://github.com/your-username/careflow-hospital-system.git
cd careflow-hospital-system


Install the required Python packages:

pip install streamlit pyodbc pandas


3. Database Configuration

Ensure your local SQL Server instance is running and accessible via Windows Authentication (Trusted_Connection=yes), or adjust the connection string in app.py:

def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=careflow_system;"
        "Trusted_Connection=yes;"
    )


4. Run the Application

Launch the Streamlit web app:

streamlit run app.py
