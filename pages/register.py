import streamlit as st
from pymongo import MongoClient
import hashlib
from datetime import datetime
from pathlib import Path
import os

st.title("👤 Register Student Account")

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

@st.cache_resource
def get_collections():
    db = get_db()
    if db is None:
        return None, None
    students = db.get_collection("students")
    return db, students

_db, students_col = get_collections()
if _db is None:
    st.error("⚠️ Cannot connect to MongoDB. Please check:")
    st.error("   1. MongoDB is running")
    st.error("   2. Connection string: mongodb://127.0.0.1:27017")
    st.error("   3. Run: python test_mongodb_connection.py to diagnose")
    st.stop()

# Utility
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# Registration form
st.header("Register")
with st.form("register_form"):
    student_id = st.text_input("Student ID (unique)")
    name = st.text_input("Full name")
    password = st.text_input("Password", type="password")
    password2 = st.text_input("Confirm password", type="password")
    extra = st.text_input("Extra info (optional, e.g., class)")
    register = st.form_submit_button("Register")

if register:
    if not student_id.strip():
        st.error("Student ID is required")
    elif not name.strip():
        st.error("Name is required")
    elif not password:
        st.error("Password is required")
    elif password != password2:
        st.error("Passwords do not match")
    else:
        # check uniqueness
        existing = students_col.find_one({"student_id": student_id})
        if existing:
            st.error("Student ID already registered. Use a different ID or login.")
        else:
            doc = {
                "student_id": student_id,
                "name": name,
                "password_hash": hash_password(password),
                "extra": extra,
                "created_at": datetime.utcnow().isoformat()
            }
            try:
                # Use explicit write concern to ensure data is written
                from pymongo import WriteConcern
                students_col_with_wc = students_col.with_options(
                    write_concern=WriteConcern(w=1, wtimeout=5000)
                )
                result = students_col_with_wc.insert_one(doc)
                
                if result.inserted_id:
                    # Verify the document was actually saved
                    verify_doc = students_col.find_one({"_id": result.inserted_id})
                    if verify_doc:
                        st.success(f"✅ Registered successfully! (ID: {result.inserted_id})")
                        st.info("Student data saved and verified in MongoDB. You can now login below.")
                    else:
                        st.warning("⚠️ Document inserted but not found on verification. Check MongoDB.")
                else:
                    st.warning("Registration completed but no ID returned. Check MongoDB connection.")
            except Exception as e:
                st.error(f"❌ Failed to register: {e}")
                st.error("Please check MongoDB connection and try again.")
                import traceback
                st.code(traceback.format_exc())

st.write("---")

# Login form
st.header("Login")
if 'student_auth' not in st.session_state:
    st.session_state.student_auth = False
    st.session_state.student_id = None

if not st.session_state.student_auth:
    with st.form("login_form"):
        login_id = st.text_input("Student ID")
        login_pw = st.text_input("Password", type="password")
        do_login = st.form_submit_button("Login")

    if do_login:
        if not login_id or not login_pw:
            st.error("Provide both Student ID and password")
        else:
            user = students_col.find_one({"student_id": login_id})
            if not user:
                st.error("Unknown Student ID. Please register first.")
            else:
                if hash_password(login_pw) == user.get("password_hash"):
                    st.session_state.student_auth = True
                    st.session_state.student_id = login_id
                    st.success(f"Logged in as {user.get('name')}")
                else:
                    st.error("Invalid password")
else:
    # show student details and logout
    user = students_col.find_one({"student_id": st.session_state.student_id})
    st.success(f"Logged in: {user.get('name')} ({user.get('student_id')})")
    
    # Display profile picture if available
    profile_pic_path = user.get('profile_picture')
    if profile_pic_path and os.path.exists(profile_pic_path):
        try:
            import cv2
            from PIL import Image
            import numpy as np
            
            # Read and display the profile picture
            img = cv2.imread(profile_pic_path)
            if img is not None:
                # Convert BGR to RGB for display
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                st.image(img_rgb, caption=f"Profile Picture - {user.get('name')}", width=200)
        except Exception as e:
            st.info("Profile picture not available")
    else:
        st.info("No profile picture available")
    
    st.write("Extra:", user.get('extra', ''))
    if st.button("Logout"):
        st.session_state.student_auth = False
        st.session_state.student_id = None
        st.rerun()
