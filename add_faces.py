import cv2
import pickle
import numpy as np
import os

# Ensure the 'data' directory exists
if not os.path.exists('data'):
    os.makedirs('data')

# Ensure the 'profiles' directory exists
if not os.path.exists('data/profiles'):
    os.makedirs('data/profiles')

video = cv2.VideoCapture(0)
if not video.isOpened():
    print("Error: Could not access camera. Please check if the camera is connected and not being used by another application.")
    exit(1)

facedetect = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

faces_data = []
profile_picture = None  # Store one good face image for profile picture
i = 0
profile_captured = False

name = input("Enter Your Name: ")

while True:
    ret, frame = video.read()
    if not ret:
        print("Error: Could not read frame from camera.")
        break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = facedetect.detectMultiScale(gray, 1.3, 5)
    
    for (x, y, w, h) in faces:
        # Use color face
        crop_img = frame[y:y + h, x:x + w, :]  # Color image
        resized_img = cv2.resize(crop_img, (50, 50))  # Resize to (50x50) for training
        flattened_img = resized_img.flatten()  # Flattened size: 7500

        if len(faces_data) < 100 and i % 10 == 0:
            faces_data.append(flattened_img)
            
            # Save a profile picture when we have about 30-50 samples (good quality)
            # Use a larger size (200x200) for better profile picture quality
            if not profile_captured and len(faces_data) >= 30:
                # Save a larger version for profile picture
                profile_picture = cv2.resize(crop_img, (200, 200))
                profile_captured = True

        i += 1
        cv2.putText(frame, str(len(faces_data)), (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 255), 1)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (50, 50, 255), 1)

    cv2.imshow("Frame", frame)
    k = cv2.waitKey(1)

    if k == ord('q') or len(faces_data) == 100:
        break

video.release()
cv2.destroyAllWindows()

# Check if any faces were collected
if len(faces_data) == 0:
    print("No faces collected. Exiting without saving.")
    exit(0)

# Convert faces_data to numpy array and reshape it properly
faces_data = np.asarray(faces_data)
faces_data = faces_data.reshape(len(faces_data), -1)  # Shape should be (100, 7500)

# Save profile picture
profile_path = None
if profile_picture is not None:
    # Sanitize name for filename (remove special characters)
    safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_name = safe_name.replace(' ', '_')
    profile_filename = f"{safe_name}.jpg"
    profile_path = f"data/profiles/{profile_filename}"
    
    # Save the profile picture
    cv2.imwrite(profile_path, profile_picture)
    print(f"📸 Profile picture saved: {profile_filename}")

# Save names
names_path = 'data/names.pkl'
faces_path = 'data/faces_data.pkl'

if not os.path.exists(names_path):
    names = [name] * len(faces_data)
    with open(names_path, 'wb') as f:
        pickle.dump(names, f)
else:
    with open(names_path, 'rb') as f:
        names = pickle.load(f)
    names.extend([name] * len(faces_data))  # Add the new names
    with open(names_path, 'wb') as f:
        pickle.dump(names, f)

# Save faces
if not os.path.exists(faces_path):
    with open(faces_path, 'wb') as f:
        pickle.dump(faces_data, f)
else:
    with open(faces_path, 'rb') as f:
        existing_faces = pickle.load(f)
    
    # Ensure both have the same shape
    if existing_faces.shape[1] == faces_data.shape[1]:
        updated_faces = np.concatenate((existing_faces, faces_data), axis=0)
        with open(faces_path, 'wb') as f:
            pickle.dump(updated_faces, f)
    else:
        print("Shape mismatch! Existing data has shape:", existing_faces.shape)
        print("New data has shape:", faces_data.shape)
        print("Cannot append. Please check your image size processing.")

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
            {"$set": {"profile_picture": profile_path}}
        )
        print(f"✅ Profile picture path saved to MongoDB for {name}")
    except Exception as e:
        print(f"⚠️  Warning: Could not update MongoDB with profile picture: {e}")
        print("   Profile picture is still saved locally.")
