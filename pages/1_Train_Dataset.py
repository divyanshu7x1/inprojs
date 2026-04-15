import streamlit as st
import cv2
import numpy as np
import pickle
import os
import json
import hashlib
from pathlib import Path

st.title("📚 Train Student data (Admin Only)")

# --- simple teacher auth using teachers.json ---
TEACHERS_FILE = Path(__file__).parent.parent / 'teachers.json'

def load_teachers():
    if not TEACHERS_FILE.exists():
        return {}
    try:
        return json.loads(TEACHERS_FILE.read_text(encoding='utf-8'))
    except Exception:
        return {}

teachers = load_teachers()

if 'auth' not in st.session_state:
    st.session_state.auth = False
    st.session_state.user = None

if not st.session_state.auth:
    st.subheader("Admin login")
    col1, col2 = st.columns(2)
    with col1:
        user_id = st.text_input("ID")
    with col2:
        password = st.text_input("Password", type='password')

    if st.button("Login"):
        if not user_id:
            st.error("Enter an ID")
        else:
            # special-case default admin credentials: admin/admin
            if user_id == 'admin' and password == 'admin':
                st.session_state.auth = True
                st.session_state.user = 'admin'
                st.success("Logged in as admin")
                # Ensure teachers.json contains the admin entry (persist credentials hash)
                try:
                    admin_entry = {
                        "name": "Administrator",
                        "password_hash": hashlib.sha256(password.encode('utf-8')).hexdigest(),
                        "is_admin": True
                    }
                    teachers_file = TEACHERS_FILE
                    data = {}
                    if teachers_file.exists():
                        try:
                            data = json.loads(teachers_file.read_text(encoding='utf-8'))
                        except Exception:
                            data = {}
                    data['admin'] = admin_entry
                    teachers_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
                except Exception:
                    # non-fatal: continue even if we can't write the file
                    pass
            else:
                info = teachers.get(user_id)
                if not info:
                    st.error("Unknown ID")
                else:
                    # require account to be admin
                    if not info.get('is_admin'):
                        st.error("Only admin users can access this page")
                    else:
                        # compare sha256 hash of password
                        pw_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
                        if pw_hash == info.get('password_hash'):
                            st.session_state.auth = True
                            st.session_state.user = user_id
                            st.success(f"Logged in as {info.get('name')}")
                        else:
                            st.error("Invalid password")

    st.stop()

# If authenticated, show training UI
st.success(f"Authenticated: {st.session_state.user}")

DATA_DIR = Path("data")
FACES_PATH = DATA_DIR / "faces_data.pkl"
NAMES_PATH = DATA_DIR / "names.pkl"
PROFILES_DIR = DATA_DIR / "profiles"
DATA_DIR.mkdir(parents=True, exist_ok=True)
PROFILES_DIR.mkdir(parents=True, exist_ok=True)

facedetect = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

name = st.text_input("Enter the student name to capture:")
capture_btn = st.button("Start Capturing Faces")

if capture_btn:
    if not name.strip():
        st.error("Please enter a valid name before capturing.")
    else:
        st.info("Starting webcam... press 'q' in the preview window to stop.")
        video = cv2.VideoCapture(0)
        if not video.isOpened():
            st.error("Could not access camera. Please check if the camera is connected and not being used by another application.")
        else:
            faces_data = []
            profile_picture = None  # Store one good face image for profile picture
            i = 0
            profile_captured = False

            while True:
                ret, frame = video.read()
                if not ret:
                    st.error("Could not read frame from camera.")
                    break

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = facedetect.detectMultiScale(gray, 1.3, 5)

                for (x, y, w, h) in faces:
                    crop_img = frame[y:y + h, x:x + w, :]
                    resized_img = cv2.resize(crop_img, (50, 50))
                    flattened_img = resized_img.flatten()

                    if len(faces_data) < 100 and i % 10 == 0:
                        faces_data.append(flattened_img)
                        
                        # Save a profile picture when we have about 30-50 samples (good quality)
                        # Use a larger size (200x200) for better profile picture quality
                        if not profile_captured and len(faces_data) >= 30:
                            # Save a larger version for profile picture
                            profile_picture = cv2.resize(crop_img, (200, 200))
                            profile_captured = True

                    i += 1
                    cv2.putText(frame, str(len(faces_data)), (50, 50),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 255), 1)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (50, 50, 255), 1)

                cv2.imshow("Training Student Data - Press 'q' to exit", frame)
                k = cv2.waitKey(1)
                if k == ord('q') or len(faces_data) == 100:
                    break

            video.release()
            cv2.destroyAllWindows()

            # Check if any faces were collected
            if len(faces_data) == 0:
                st.error("No faces collected. Please try again.")
            else:
                faces_data = np.asarray(faces_data).reshape(len(faces_data), -1)

                # Save profile picture
                profile_path = None
                if profile_picture is not None:
                    # Sanitize name for filename (remove special characters)
                    safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
                    safe_name = safe_name.replace(' ', '_')
                    profile_filename = f"{safe_name}.jpg"
                    profile_path = PROFILES_DIR / profile_filename
                    
                    # Save the profile picture
                    cv2.imwrite(str(profile_path), profile_picture)
                    st.info(f"📸 Profile picture saved: {profile_filename}")

                # Save data
                if not os.path.exists(FACES_PATH):
                    with open(FACES_PATH, 'wb') as f:
                        pickle.dump(faces_data, f)
                    with open(NAMES_PATH, 'wb') as f:
                        pickle.dump([name] * len(faces_data), f)
                else:
                    with open(FACES_PATH, 'rb') as f:
                        existing_faces = pickle.load(f)
                    with open(NAMES_PATH, 'rb') as f:
                        existing_names = pickle.load(f)

                    updated_faces = np.concatenate((existing_faces, faces_data), axis=0)
                    updated_names = existing_names + [name] * len(faces_data)

                    with open(FACES_PATH, 'wb') as f:
                        pickle.dump(updated_faces, f)
                    with open(NAMES_PATH, 'wb') as f:
                        pickle.dump(updated_names, f)

                # Update MongoDB with profile picture path if available
                if profile_path:
                    try:
                        from pymongo import MongoClient
                        MONGO_URI = "mongodb://127.0.0.1:27017"
                        DB_NAME = "attendance_db"
                        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
                        db = client[DB_NAME]
                        students_col = db["students"]
                        
                        # Update student record with profile picture path
                        # Try to find by name first
                        students_col.update_many(
                            {"name": name},
                            {"$set": {"profile_picture": str(profile_path)}}
                        )
                        st.info("Profile picture path saved to MongoDB")
                    except Exception as e:
                        st.warning(f"Could not update MongoDB with profile picture: {e}")

                st.success(f"✅ Successfully trained student data for {name}")
