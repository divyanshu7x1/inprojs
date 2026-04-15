# ----------------------- Recognition-only UI (uses pre-trained data files) -----------------------
# Place this after your mark_attendance() and DB setup in app.py
import streamlit as st
import subprocess
import sys
from pathlib import Path
import csv
import pandas as pd
import matplotlib.pyplot as plt
import hashlib
from pymongo import MongoClient
from datetime import datetime, timezone
import json

st.set_page_config(
    page_title="Mark Attendance",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS styles
st.markdown("""
<style>
    /* Main title styling */
    .main-title {
        font-family: 'Helvetica Neue', sans-serif;
        font-size: 42px;
        font-weight: bold;
        background: linear-gradient(45deg, #1e3799, #0984e3);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 20px 0;
        margin-bottom: 10px;
    }
    
    /* Subtitle styling */
    .subtitle {
        font-family: 'Arial', sans-serif;
        color: #555;
        font-size: 18px;
        text-align: center;
        font-style: italic;
        margin-bottom: 30px;
    }
    
    /* Section headers */
    .stMarkdown h2 {
        font-family: 'Helvetica Neue', sans-serif;
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 8px;
        margin-top: 30px;
    }
    
    /* Success messages */
    .stSuccess {
        font-family: 'Arial', sans-serif;
        font-weight: 500;
    }
    
    /* Dataframe styling */
    .dataframe {
        font-family: 'Arial', sans-serif;
        border-radius: 10px;
        border: 1px solid #ddd;
    }
    
    /* Button styling */
    .stButton button {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 500;
        border-radius: 20px;
        padding: 2px 15px;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    /* Form fields */
    .stTextInput input, .stSelectbox select {
        border-radius: 8px;
        border: 1px solid #ddd;
        padding: 8px;
    }
    
    /* Divider styling */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #3498db, transparent);
        margin: 30px 0;
    }
</style>
""", unsafe_allow_html=True)

# Main title with icon
st.markdown('<h1 class="main-title">📋 Mark Attendance</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Advanced Face Recognition & Attendance Management</p>', unsafe_allow_html=True)


# --- MongoDB helper ---
MONGO_URI = "mongodb://127.0.0.1:27017"
DB_NAME = "attendance_db"

def get_db():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        client.server_info()
        return client[DB_NAME]
    except Exception as e:
        st.error(f"Cannot connect to MongoDB at {MONGO_URI}: {e}")
        return None

db = get_db()
if db is None:                              #database connection  check
    st.stop()

students_col = db.get_collection('students')

                                                                 
if 'student_auth' not in st.session_state:
    st.session_state.student_auth = False
    st.session_state.student_id = None

if not st.session_state.student_auth:
    st.markdown("""
    <div style="background-color: #f0f8ff; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h3 style="color: #2c3e50; font-family: 'Helvetica Neue', sans-serif; margin-bottom: 15px;">
            👋 Student Login
        </h3>
    </div>
    """, unsafe_allow_html=True)

    with st.form("student_login", clear_on_submit=True):
        login_id = st.text_input("Student ID", placeholder="Enter your student ID")
        login_pw = st.text_input("Password", type="password", placeholder="Enter your password")
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            submitted = st.form_submit_button("Login", use_container_width=True)

    if submitted:
        if not login_id or not login_pw:
            st.error("Provide both Student ID and password")
        else:
            user = students_col.find_one({"student_id": login_id})
            if not user:
                st.error("Unknown Student ID. Please register first on the Register page.")
            else:
                pw_hash = hashlib.sha256(login_pw.encode('utf-8')).hexdigest()
                if pw_hash == user.get('password_hash'):
                    st.session_state.student_auth = True
                    st.session_state.student_id = login_id
                    st.success(f"Logged in as {user.get('name')}")
                else:
                    st.error("Invalid password")

    st.info("If you don't have an account, go to the Register page to sign up.")
    st.stop()
else:
    user = students_col.find_one({"student_id": st.session_state.student_id})
    st.success(f"Logged in: {user.get('name')} ({st.session_state.student_id})")
    if st.button("Logout"):
        st.session_state.student_auth = False
        st.session_state.student_id = None
        st.rerun()

    # Show Take attendance button to authenticated students
    if st.button("Take attendance"):
        try:
            CREATE_NO_WINDOW = 0x08000000
            python_exe = sys.executable or 'python'
            script_path = Path(__file__).parent / 'test.py'
            # Pass the logged-in student's name as an argument
            student_name = user.get('name', '')
            proc = subprocess.Popen(
                [python_exe, str(script_path), '--student-name', student_name],
                creationflags=CREATE_NO_WINDOW
            )
            st.success(f"Launched test.py (pid={proc.pid}). The camera window should open directly.")
            st.info(f"Only {student_name} can mark attendance. Use the camera window to press 'o' to save attendance or 'q' to quit.")
        except Exception as e:
            st.error(f"Failed to launch test.py: {e}")


def load_attendance_records():
    """Read attendance CSV(s) and return list of records as dicts with keys: NAME, DATE, TIME, STATUS."""
    files = []
    root_file = Path("Attendance_29-01-2024.csv")
    if root_file.exists():
        files.append(root_file)
    att_dir = Path("Attendance")
    if att_dir.exists() and att_dir.is_dir():
        files.extend(sorted(att_dir.glob("*.csv")))

    records = []
    for fp in files:
        try:
            with open(fp, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header row
                for row in reader:
                    if not row:
                        continue
                    # Normalize rows with 3 or 4 columns
                    if len(row) == 4:
                        name, date_col, time_col, status = row
                    elif len(row) == 3:
                        name, time_col, status = row
                        date_col = fp.stem
                    else:
                        # fallback
                        name = row[0]
                        date_col = row[1] if len(row) > 1 else ''
                        time_col = row[2] if len(row) > 2 else ''
                        status = row[3] if len(row) > 3 else ''
                    records.append({"NAME": name, "DATE": date_col, "TIME": time_col, "STATUS": status})
        except Exception:
            continue
    return records


st.markdown('<hr>', unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; padding: 20px;">
    <h2 style="color: #2c3e50; font-family: 'Helvetica Neue', sans-serif; margin-bottom: 10px;">
        📊 Dashboard
    </h2>
    <p style="color: #666; font-family: Arial, sans-serif; font-size: 16px;">
        Real-time attendance records and analytics. Track attendance patterns and generate insights.
    </p>
</div>
""", unsafe_allow_html=True)

records = load_attendance_records()                          #reading data
if not records:
    st.info("No attendance records found. Take attendance first.")
else:
    df = pd.DataFrame(records)
    # normalize STATUS casing
    if 'STATUS' in df.columns:
        df['STATUS'] = df['STATUS'].astype(str).str.strip()
    # date filter
    dates = sorted(df['DATE'].dropna().unique())
    date_choice = st.selectbox("Filter by date", options=["All"] + dates, index=0)
    if date_choice == "All":
        filtered = df
    else:
        filtered = df[df['DATE'] == date_choice]

    st.subheader("Records")
    # Style the dataframe with colors
    def color_status(row):
        status = str(row['STATUS']).strip().lower()
        if 'present' in status:
            return [''] * 3 + ['background-color: #90EE90']  # light green
        elif 'absent' in status:
            return [''] * 3 + ['background-color: #FFB6C1']  # light red
        return [''] * 4  # no color
    
    styled_df = filtered[['NAME', 'DATE', 'TIME', 'STATUS']].style.apply(color_status, axis=1)
    st.dataframe(styled_df)

    # Summary counts
    status_counts = filtered['STATUS'].value_counts().to_dict()
    labels = list(status_counts.keys())
    sizes = list(status_counts.values())

    if sizes:
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)
        ax.axis('equal')
        st.subheader("Attendance summary")
        st.pyplot(fig)

    # Simple present/absent counts if those labels exist
    present = 0
    absent = 0
    for k, v in status_counts.items():
        kl = k.strip().lower()
        if 'present' in kl:
            present += v
        if 'absent' in kl:
            absent += v
    st.write(f"Present: {present}  —  Absent: {absent}")

    # Button to mark missing students as absent for the selected date
    if date_choice != "All":
        if st.button("Mark missing students as Absent for selected date"):
            # load known student list from data/names.pkl
            names_path = Path('data') / 'names.pkl'
            if not names_path.exists():
                st.error("No student list found (data/names.pkl). Collect faces with add_faces.py first.")
            else:
                try:
                    import pickle
                    all_names = pickle.load(open(names_path, 'rb'))
                    all_set = set(str(n).strip() for n in all_names)
                except Exception as e:
                    st.error(f"Failed to load student names: {e}")
                    all_set = set()

                # names already marked on this date
                marked_set = set(str(n).strip() for n in filtered['NAME'].tolist())
                missing = sorted(list(all_set - marked_set))
                if not missing:
                    st.success("No missing students — everyone already marked for this date.")
                else:
                    attendance_file = Path('Attendance_29-01-2024.csv')
                    # detect columns in existing file
                    cols = 0
                    if attendance_file.exists():
                        try:
                            with open(attendance_file, 'r', encoding='utf-8') as fr:
                                first = fr.readline()
                                cols = first.count(',') + 1 if first else 0
                        except Exception:
                            cols = 0
                    else:
                        cols = 4

                    written = 0
                    mongo_written = 0
                    file_exists = attendance_file.exists()
                    try:
                        current_time_str = datetime.now().strftime('%H:%M:%S')
                        current_datetime = datetime.now()
                        
                        # Save to MongoDB
                        attendance_col = db.get_collection('attendance')
                        for nm in missing:
                            try:
                                attendance_doc = {
                                    "student_name": nm,
                                    "date": date_choice,
                                    "time": current_time_str,
                                    "status": "Absent",
                                    "timestamp": current_datetime,
                                    "created_at": datetime.now(timezone.utc),
                                    "marked_by": "admin"
                                }
                                attendance_col.insert_one(attendance_doc)                            #sends data
                                mongo_written += 1
                            except Exception as e:
                                st.warning(f"Failed to save {nm} to MongoDB: {e}")
                        
                        # Also save to CSV (backup)
                        with open(attendance_file, 'a', newline='', encoding='utf-8') as fw:
                            writer = csv.writer(fw)
                            # if file didn't exist, write header
                            if not file_exists:
                                writer.writerow(['NAME','DATE','TIME','STATUS'])
                            # Use current time for each entry
                            for nm in missing:
                                writer.writerow([nm, date_choice, current_time_str, 'Absent'])
                                written += 1
                        
                        success_msg = f"Marked {written} students as Absent for {date_choice}."
                        if mongo_written > 0:
                            success_msg += f" ({mongo_written} saved to MongoDB)"
                        st.success(success_msg)
                    except Exception as e:
                        st.error(f"Failed to write absent entries: {e}")


# --- Admin-only Records management ---
st.write('\n')
st.markdown("""
<div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #2c3e50;">
    <h2 style="color: #2c3e50; font-family: 'Helvetica Neue', sans-serif; margin: 0;">
        🔐 Admin Control Panel
    </h2>
    <p style="color: #666; margin-top: 10px; font-family: Arial, sans-serif;">
        Secure administrative interface for managing attendance records and system settings.
    </p>
</div>
""", unsafe_allow_html=True)

TEACHERS_FILE = Path('teachers.json')

def load_teachers():
    if not TEACHERS_FILE.exists():
        return {}
    try:
        return json.loads(TEACHERS_FILE.read_text(encoding='utf-8'))
    except Exception:
        return {}

teachers = load_teachers()

if 'admin_auth' not in st.session_state:
    st.session_state.admin_auth = False
    st.session_state.admin_user = None

if not st.session_state.admin_auth:                                                     # admin login 
    st.subheader('Admin Login')
    col1, col2 = st.columns(2)
    with col1:
        admin_id = st.text_input('Admin ID')
    with col2:
        admin_pw = st.text_input('Password', type='password')
    if st.button('Admin Login'):
        if admin_id == 'admin' and admin_pw == 'admin':
            st.session_state.admin_auth = True
            st.session_state.admin_user = 'admin'
            # persist admin into teachers.json if not present
            try:
                teachers['admin'] = {'name':'Administrator','password_hash':hashlib.sha256('admin'.encode()).hexdigest(),'is_admin':True}
                TEACHERS_FILE.write_text(json.dumps(teachers, indent=2), encoding='utf-8')
            except Exception:
                pass
            st.success('Admin logged in')
        else:
            info = teachers.get(admin_id)
            if not info or not info.get('is_admin'):
                st.error('Unknown admin ID or not an admin')
            else:
                pw_hash = hashlib.sha256(admin_pw.encode('utf-8')).hexdigest()
                if pw_hash == info.get('password_hash'):
                    st.session_state.admin_auth = True
                    st.session_state.admin_user = admin_id
                    st.success(f"Admin {info.get('name')} logged in")
                else:
                    st.error('Invalid password')
    st.stop()

# admin authenticated
st.success(f"Admin: {st.session_state.admin_user}")

ATT_FILE = Path('Attendance_29-01-2024.csv')

def load_attendance_df():
    cols = ['NAME','DATE','TIME','STATUS']
    if not ATT_FILE.exists():
        return pd.DataFrame(columns=cols)
    try:
        df = pd.read_csv(ATT_FILE)
        for c in cols:
            if c not in df.columns:
                df[c] = ''
        return df[cols]
    except Exception:
        try:
            df = pd.read_csv(ATT_FILE, header=None)
            df.columns = cols[:len(df.columns)]
            for c in cols:
                if c not in df.columns:
                    df[c] = ''
            return df[cols]
        except Exception:
            return pd.DataFrame(columns=cols)


def save_attendance_df(df):
    try:
        df.to_csv(ATT_FILE, index=False)
        return True, None
    except Exception as e:
        return False, str(e)


df_att = load_attendance_df()

st.subheader('Records')
st.write('Use this section to view and manipulate attendance records. Actions are recorded to the main CSV file.')

if df_att.empty:
    st.info('No attendance records yet.')
else:
    # Color code present/absent rows
    def color_status(row):
        status = str(row['STATUS']).strip().lower()
        if 'present' in status:
            return [''] * 3 + ['background-color: #90EE90']  # light green
        elif 'absent' in status:
            return [''] * 3 + ['background-color: #FFB6C1']  # light red
        return [''] * 4  # no color
    
    styled_df = df_att.style.apply(color_status, axis=1)
    st.dataframe(styled_df)

st.write('---')

# Row selection for removal
if not df_att.empty:
    choices = [f"{i}: {r['NAME']} | {r['DATE']} | {r['TIME']} | {r['STATUS']}" for i, r in df_att.iterrows()]
else:
    choices = []

remove_sel = st.multiselect('Select rows to remove', options=choices)
if st.button('Remove selected rows') and remove_sel:
    idxs = [int(s.split(':', 1)[0]) for s in remove_sel]
    df_att = df_att.drop(index=idxs).reset_index(drop=True)
    ok, err = save_attendance_df(df_att)
    if ok:
        st.success('Selected rows removed')
        st.rerun()
    else:
        st.error(f'Failed to save: {err}')

st.write('---')

# Update or add status for a student/date
st.subheader('Mark Present/Absent or Add Entry')
all_names = sorted(df_att['NAME'].dropna().unique().tolist())
name_choice = st.selectbox('Student name', options=['--select--'] + all_names)
date_input = st.text_input('Date (dd-mm-YYYY)', value=datetime.now().strftime('%d-%m-%Y'))
status_choice = st.selectbox('Status', options=['Present', 'Absent'])
if st.button('Apply status'):
    if name_choice == '--select--':
        st.error('Pick a student name')
    else:
        # Always use current timestamp for new entries
        current_time = datetime.now().strftime('%H:%M:%S')
        current_datetime = datetime.now()
        
        # Save to MongoDB first
        mongo_saved = False
        try:
            from pymongo import WriteConcern
            attendance_col = db.get_collection('attendance')
            attendance_col_with_wc = attendance_col.with_options(
                write_concern=WriteConcern(w=1, wtimeout=5000)
            )
            
            # Check if entry exists for this name and date
            existing = attendance_col.find_one({
                "student_name": name_choice,
                "date": date_input
            })
            
            entry_time = current_time if status_choice.lower() == 'present' else ''
            
            if existing:
                # Update existing entry
                result = attendance_col_with_wc.update_one(
                    {"student_name": name_choice, "date": date_input},
                    {
                        "$set": {
                            "status": status_choice,
                            "time": entry_time,
                            "timestamp": current_datetime,
                            "updated_at": datetime.now(timezone.utc),
                            "marked_by": "admin"
                        }
                    }
                )
                if result.modified_count > 0:
                    # Verify update
                    verify = attendance_col.find_one({
                        "student_name": name_choice,
                        "date": date_input,
                        "status": status_choice
                    })
                    if verify:
                        mongo_saved = True
                        st.info(f"✅ Updated in MongoDB: {result.modified_count} record(s) - Verified")
                    else:
                        st.warning("⚠️ Update completed but verification failed")
            else:
                # Create new entry
                attendance_doc = {
                    "student_name": name_choice,
                    "date": date_input,
                    "time": entry_time,
                    "status": status_choice,
                    "timestamp": current_datetime,
                    "created_at": datetime.now(timezone.utc),
                    "marked_by": "admin"
                }
                result = attendance_col_with_wc.insert_one(attendance_doc)
                if result.inserted_id:
                    # Verify the document was actually saved
                    verify_doc = attendance_col.find_one({"_id": result.inserted_id})
                    if verify_doc:
                        mongo_saved = True
                        st.info(f"✅ Saved to MongoDB (ID: {result.inserted_id}) - Verified")
                    else:
                        st.warning("⚠️ Document inserted but not found on verification")
        except Exception as e:
            st.error(f"❌ Failed to save to MongoDB: {e}")
            import traceback
            st.code(traceback.format_exc())
        
        # Also update CSV (backup)
        # find any existing row for that name+date
        mask = (df_att['NAME'] == name_choice) & (df_att['DATE'] == date_input)
        if mask.any():
            df_att.loc[mask, 'STATUS'] = status_choice
            # Update time only for 'Present' status
            if status_choice.lower() == 'present':
                df_att.loc[mask, 'TIME'] = current_time
        else:
            # For new entries, always include current time (will be empty string for Absent)
            entry_time = current_time if status_choice.lower() == 'present' else ''
            df_att = pd.concat([df_att, pd.DataFrame([{
                'NAME': name_choice,
                'DATE': date_input,
                'TIME': entry_time,
                'STATUS': status_choice
            }])], ignore_index=True)
        ok, err = save_attendance_df(df_att)
        if ok:
            st.success('Attendance updated (saved to MongoDB and CSV)')
            st.rerun()
        else:
            st.error(f'Failed to save: {err}')

st.write('---')

# Bulk mark missing (admin) - reuse earlier logic but operate on df_att
if st.button('Mark missing students as Absent for a date (admin)'):
    names_path = Path('data') / 'names.pkl'
    if not names_path.exists():
        st.error('No student list found (data/names.pkl).')
    else:
        try:
            import pickle
            all_names = pickle.load(open(names_path, 'rb'))
            all_set = set(str(n).strip() for n in all_names)
        except Exception as e:
            st.error(f'Failed to load student names: {e}')
            all_set = set()
        date_to_mark = st.text_input('Date to mark (dd-mm-YYYY)', value=datetime.now().strftime('%d-%m-%Y'))
        marked_set = set(str(n).strip() for n in df_att[df_att['DATE'] == date_to_mark]['NAME'].tolist())
        missing = sorted(list(all_set - marked_set))
        if not missing:
            st.success('No missing students for that date')
        else:
            # Get current time once for all entries
            current_time = datetime.now().strftime('%H:%M:%S')
            for nm in missing:
                df_att = pd.concat([df_att, pd.DataFrame([{
                    'NAME': nm,
                    'DATE': date_to_mark,
                    'TIME': '',  # Empty for Absent
                    'STATUS': 'Absent'
                }])], ignore_index=True)
            ok, err = save_attendance_df(df_att)
            if ok:
                st.success(f'Marked {len(missing)} students as Absent for {date_to_mark}')
                st.rerun()
            else:
                st.error(f'Failed to save: {err}')