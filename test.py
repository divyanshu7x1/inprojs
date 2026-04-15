import cv2
import pickle
import numpy as np
import os
import csv
import time
import sys
import argparse
from datetime import datetime
from sklearn.neighbors import KNeighborsClassifier
from win32com.client import Dispatch
from pymongo import MongoClient

# Parse command line arguments
parser = argparse.ArgumentParser(description='Face Recognition Attendance System')
parser.add_argument('--student-name', type=str, default='', 
                    help='Name of the logged-in student (required for attendance marking)')
args = parser.parse_args()

LOGGED_IN_STUDENT_NAME = args.student_name.strip() if args.student_name else None

# Speak using text-to-speech
def speak(text):
    speaker = Dispatch("SAPI.SpVoice")
    speaker.Speak(text)

# Load face data and names
try:
    with open('data/faces_data.pkl', 'rb') as f:
        FACES = pickle.load(f)
except FileNotFoundError:
    print("Error: data/faces_data.pkl not found. Please register a student first using add_faces.py or the Register a Student page.")
    exit(1)

try:
    with open('data/names.pkl', 'rb') as f:
        LABELS = pickle.load(f)
except FileNotFoundError:
    print("Error: data/names.pkl not found. Please register a student first using add_faces.py or the Register a Student page.")
    exit(1)

# Check if data is empty
if len(FACES) == 0 or len(LABELS) == 0:
    print("Error: No face data found. Please register a student first.")
    exit(1)

# Make sure the shapes match
if len(FACES) != len(LABELS):
    print(f"Mismatch: {len(FACES)} faces vs {len(LABELS)} names")
    LABELS = LABELS[:len(FACES)]  # Fix the mismatch
    with open('data/names.pkl', 'wb') as f:
        pickle.dump(LABELS, f)

print('Shape of Faces matrix -->', FACES.shape)

# Train the model
knn = KNeighborsClassifier(n_neighbors=5)
knn.fit(FACES, LABELS)

# Use OpenCV's internal Haar cascade path
facedetect = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Start webcam
video = cv2.VideoCapture(0)
if not video.isOpened():
    print("Error: Could not access camera. Please check if the camera is connected and not being used by another application.")
    exit(1)

# Make sure attendance folder exists
if not os.path.exists("Attendance"):
    os.makedirs("Attendance")

COL_NAMES = ['NAME', 'DATE', 'TIME', 'STATUS']  # Added 'DATE' and 'STATUS' columns

# MongoDB configuration
MONGO_URI = "mongodb://127.0.0.1:27017"
DB_NAME = "attendance_db"
STUDENTS_COL = "students"
ATTENDANCE_COL = "attendance"

def get_mongo_db():
    """Get MongoDB database connection"""
    try:
        client = MongoClient(
            MONGO_URI, 
            serverSelectionTimeoutMS=5000
        )
        client.server_info()  # Test connection
        print(f"✅ MongoDB connected: {MONGO_URI}")
        print(f"✅ Database: {DB_NAME}")
        return client[DB_NAME]
    except Exception as e:
        print(f"❌ ERROR: Could not connect to MongoDB: {e}")
        print(f"   URI: {MONGO_URI}")
        print(f"   Database: {DB_NAME}")
        print(f"   Please check if MongoDB is running.")
        return None

def has_marked_attendance_recently(name, attendance_file, hours=24):
    """
    Check if a student has marked attendance within the specified hours (default 24).
    Checks both MongoDB and CSV file.
    Returns True if attendance was marked within the time window, False otherwise.
    """
    current_time = datetime.now()
    
    # First, check MongoDB (primary source)
    db = get_mongo_db()
    if db is not None:
        try:
            attendance_col = db[ATTENDANCE_COL]
            # Find the most recent 'Present' attendance for this student
            recent_attendance = attendance_col.find_one(
                {
                    "student_name": name,
                    "status": "Present"
                },
                sort=[("timestamp", -1)]  # Get most recent first
            )
            
            if recent_attendance:
                attendance_datetime = recent_attendance.get("timestamp")
                if attendance_datetime:
                    # Calculate time difference
                    time_diff = current_time - attendance_datetime
                    hours_diff = time_diff.total_seconds() / 3600
                    
                    # Check if within the specified hours window
                    if hours_diff < hours and hours_diff >= 0:
                        return True
        except Exception as e:
            print(f"Error checking MongoDB attendance: {e}")
    
    # Fallback: Check CSV file if MongoDB check didn't find anything
    if not os.path.exists(attendance_file):
        return False
    
    try:
        with open(attendance_file, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader, None)  # Skip header
            
            for row in reader:
                if len(row) < 4:
                    continue
                
                student_name = row[0].strip()
                date_str = row[1].strip()
                time_str = row[2].strip()
                status = row[3].strip() if len(row) > 3 else ''
                
                # Only check 'Present' status entries
                if student_name.lower() == name.lower() and status.lower() == 'present':
                    try:
                        # Parse date and time
                        # Date format: dd-mm-yyyy, Time format: HH:MM:SS
                        date_obj = datetime.strptime(date_str, "%d-%m-%Y")
                        time_obj = datetime.strptime(time_str, "%H:%M:%S").time()
                        
                        # Combine date and time
                        attendance_datetime = datetime.combine(date_obj.date(), time_obj)
                        
                        # Calculate time difference
                        time_diff = current_time - attendance_datetime
                        hours_diff = time_diff.total_seconds() / 3600
                        
                        # Check if within the specified hours window
                        if hours_diff < hours and hours_diff >= 0:
                            return True
                    except (ValueError, IndexError) as e:
                        # Skip rows with invalid date/time format
                        continue
        
        return False
    except Exception as e:
        print(f"Error checking CSV attendance: {e}")
        return False

attendance_file = "Attendance_29-01-2024.csv"
detected_name = None  # Store the last detected name

# Display restriction status
if LOGGED_IN_STUDENT_NAME:
    print(f"\n🔒 ATTENDANCE RESTRICTION ENABLED")
    print(f"   Only {LOGGED_IN_STUDENT_NAME} can mark attendance.")
    print(f"   The system will verify that the detected face matches the logged-in student.\n")
else:
    print("\n⚠️  No student restriction - anyone can mark attendance.\n")

while True:
    ret, frame = video.read()
    if not ret:
        print("Error: Could not read frame from camera.")
        break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = facedetect.detectMultiScale(gray, 1.3, 5)

    # Reset detected name at the start of each frame
    detected_name = None

    for (x, y, w, h) in faces:
        crop_img = frame[y:y+h, x:x+w]
        resized_img = cv2.resize(crop_img, (50, 50)).flatten().reshape(1, -1)
        output = knn.predict(resized_img)
        name = str(output[0])
        detected_name = name  # Store the detected name

        # Draw UI on frame
        cv2.rectangle(frame, (x, y), (x+w, y+h), (50, 50, 255), 2)
        cv2.rectangle(frame, (x, y-40), (x+w, y), (50, 50, 255), -1)
        cv2.putText(frame, name, (x, y-10), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
        
        # Show match status if logged-in student restriction is enabled
        if LOGGED_IN_STUDENT_NAME:
            if detected_name.lower().strip() == LOGGED_IN_STUDENT_NAME.lower().strip():
                # Match - show green indicator
                cv2.putText(frame, "MATCH", (x+w+10, y+20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            else:
                # No match - show red indicator
                cv2.putText(frame, "NO MATCH", (x+w+10, y+20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # Display logged-in student info on frame if restriction is enabled
    if LOGGED_IN_STUDENT_NAME:
        cv2.putText(frame, f"Logged in: {LOGGED_IN_STUDENT_NAME}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    cv2.imshow("Face Recognition Attendance", frame)

    k = cv2.waitKey(1)
    if k == ord('o'):
        if detected_name is None:
            speak("No face detected")
            print("\n⚠️  No face detected. Please position yourself in front of the camera.\n")
            cv2.putText(frame, "No face detected!", (50, 100), 
                       cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
            cv2.imshow("Face Recognition Attendance", frame)
            cv2.waitKey(2000)  # Show message for 2 seconds
        else:
            # Check if logged-in student restriction is enabled
            if LOGGED_IN_STUDENT_NAME:
                # Verify that detected face matches the logged-in student
                if detected_name.lower().strip() != LOGGED_IN_STUDENT_NAME.lower().strip():
                    speak("Access denied. Face does not match logged in student")
                    print(f"\n❌ ACCESS DENIED!")
                    print(f"   Detected face: {detected_name}")
                    print(f"   Logged in as: {LOGGED_IN_STUDENT_NAME}")
                    print(f"   Only {LOGGED_IN_STUDENT_NAME} can mark attendance.\n")
                    cv2.putText(frame, "Access Denied!", (50, 100), 
                               cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
                    cv2.putText(frame, f"Only {LOGGED_IN_STUDENT_NAME}", (50, 140), 
                               cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 0, 255), 2)
                    cv2.imshow("Face Recognition Attendance", frame)
                    cv2.waitKey(3000)  # Show message for 3 seconds
                    continue  # Skip attendance marking
            
            # Use logged-in student name for 24-hour check if restriction is enabled
            name_for_check = LOGGED_IN_STUDENT_NAME if LOGGED_IN_STUDENT_NAME else detected_name
            
            # Check if student has already marked attendance within 24 hours
            if has_marked_attendance_recently(name_for_check, attendance_file, hours=24):
                speak("Attendance already marked within 24 hours")
                print(f"\n⚠️  {name_for_check} has already marked attendance within the last 24 hours.")
                print("   Please wait before marking attendance again.\n")
                # Show message on the frame
                cv2.putText(frame, "Already marked!", (50, 100), 
                           cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
                cv2.imshow("Face Recognition Attendance", frame)
                cv2.waitKey(2000)  # Show message for 2 seconds
            else:
                # Get current timestamp
                ts = time.time()
                current_datetime = datetime.now()
                date = current_datetime.strftime("%d-%m-%Y")
                timestamp = current_datetime.strftime("%H:%M:%S")
                
                # Use logged-in student name if restriction is enabled (for consistency)
                # Otherwise use detected name
                student_name_for_attendance = LOGGED_IN_STUDENT_NAME if LOGGED_IN_STUDENT_NAME else detected_name
                
                # Mark attendance as 'Present'
                status = 'Present'
                attendance = [student_name_for_attendance, date, timestamp, status]
                
                exists = os.path.isfile(attendance_file)
                
                speak("Attendance Taken..")
                time.sleep(1)

                # Save to MongoDB (primary storage)
                print(f"\n💾 Attempting to save attendance to MongoDB...")
                print(f"   Student: {student_name_for_attendance}")
                print(f"   Date: {date}")
                print(f"   Time: {timestamp}")
                
                db = get_mongo_db()
                mongo_saved = False
                if db is not None:
                    try:
                        from pymongo import WriteConcern
                        attendance_col = db[ATTENDANCE_COL]
                        print(f"✅ Collection '{ATTENDANCE_COL}' accessed")
                        
                        attendance_col_with_wc = attendance_col.with_options(
                            write_concern=WriteConcern(w=1, wtimeout=5000)
                        )
                        attendance_doc = {
                            "student_name": student_name_for_attendance,
                            "date": date,
                            "time": timestamp,
                            "status": status,
                            "timestamp": current_datetime,  # Full datetime for easier querying
                            "created_at": datetime.utcnow(),
                            "marked_by": "face_recognition" + ("_restricted" if LOGGED_IN_STUDENT_NAME else "")
                        }
                        
                        print(f"📝 Inserting document...")
                        result = attendance_col_with_wc.insert_one(attendance_doc)
                        
                        if result.inserted_id:
                            print(f"✅ Insert returned ID: {result.inserted_id}")
                            
                            # Verify the document was actually saved
                            print(f"🔍 Verifying document in database...")
                            verify_doc = attendance_col.find_one({"_id": result.inserted_id})
                            if verify_doc:
                                mongo_saved = True
                                print(f"✅✅✅ SUCCESS: Saved to MongoDB!")
                                print(f"   Student: {student_name_for_attendance}")
                                print(f"   ID: {result.inserted_id}")
                                print(f"   Verified: Document exists in database")
                                
                                # Count total documents
                                total = attendance_col.count_documents({})
                                print(f"   Total attendance records: {total}")
                            else:
                                print(f"❌❌❌ CRITICAL: Document inserted but NOT found on verification!")
                                print(f"   This means the write didn't persist.")
                        else:
                            print(f"❌ ERROR: MongoDB insert returned no ID")
                            print(f"   This usually means the write failed.")
                    except Exception as e:
                        print(f"❌❌❌ EXCEPTION: Failed to save to MongoDB")
                        print(f"   Error: {e}")
                        import traceback
                        print("   Full traceback:")
                        traceback.print_exc()
                else:
                    print("❌❌❌ CRITICAL: MongoDB connection failed!")
                    print("   Check if MongoDB is running on 127.0.0.1:27017")
                    print("   Run: python test_attendance_save.py to test connection")
                
                # Also save to CSV file (backup/legacy support)
                try:
                    with open(attendance_file, "a", newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        if not exists:
                            writer.writerow(COL_NAMES)  # Write the header if file does not exist
                        writer.writerow(attendance)
                    csv_saved = True
                except Exception as e:
                    print(f"⚠️  Warning: Failed to save to CSV: {e}")
                    csv_saved = False
                
                if mongo_saved or csv_saved:
                    print(f"\n✅ Attendance marked successfully for {student_name_for_attendance} at {timestamp}\n")
                    # Show success message on the frame
                    cv2.putText(frame, "Attendance Saved!", (50, 100), 
                               cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                    cv2.imshow("Face Recognition Attendance", frame)
                    cv2.waitKey(2000)  # Show message for 2 seconds
                else:
                    print(f"\n❌ Failed to save attendance for {detected_name}\n")
                    cv2.putText(frame, "Save Failed!", (50, 100), 
                               cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
                    cv2.imshow("Face Recognition Attendance", frame)
                    cv2.waitKey(2000)

    if k == ord('q'):
        break

video.release()
cv2.destroyAllWindows()
