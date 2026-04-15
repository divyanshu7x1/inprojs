 HEAD
# 📸 Face Recognition Attendance System

A complete **face recognition-based attendance management system** built with **Python**, **OpenCV**, **Streamlit**, and **MongoDB**.  
It allows students to log in, take attendance using a camera, and stores attendance records in MongoDB as well as a CSV backup.  
Admins have a dashboard to manage, edit, and visualize attendance.

## 🚀 Features

### ✅ Student Module
- Student registration (ID + Password)
- Secure login with SHA256 password hashing
- Take attendance using camera (face recognition)
- Records stored with timestamp & status

### ✅ Admin Module
- Admin login with role-based access
- View all attendance records
- Edit/update attendance
- Mark students present/absent manually
- Dashboard with analytics and pie chart visualization
- Bulk-mark missing students as absent

### ✅ Data Storage
- MongoDB for all student & attendance data
- CSV file backup for redundancy
- Dynamic loading of multiple CSV files under `/Attendance/`

---

## 📦 Project Structure

│
├── app.py → Main Streamlit app
├── register.py → Register students
├── test.py → Face recognition + attendance marking
├── mongodb_setup.py → MongoDB verification script
│
├── data/
│ ├── faces_data.pkl → Encoded face data
│ └── names.pkl → Student names list
│
├── Attendance/ → Daily CSV attendance files
├── Attendance_29-01-2024.csv
│
├── teachers.json → Admin & teacher accounts
├── requirements.txt
└── README.md → Documentation



## ⚙️ Requirements

Install the following tools:

- Python 3.8+
- MongoDB 6.0+ (running locally)
- OpenCV
- Streamlit
- PyMongo
- Numpy
- Matplotlib
- Pandas

Install all dependencies:

```bash
pip install -r requirements.txt






🧑‍🎓 Student Workflow

Go to the Register page

Enter:

Name

Student ID

Password

Login using Student ID

Press Take Attendance

Camera opens → press:

'o' to mark attendance (Present)

'q' to quit

Records will be saved to:

MongoDB: attendance collection

CSV: Attendance_29-01-2024.csv or /Attendance/*.csv


🔐 Admin Workflow

Login as Admin:

ID: admin
Password: admin


Admin can:

View all attendance

Update/edit records

Bulk mark absentees

Visualize data

Delete entries

🧪 Face Training (Optional)

Run this to add faces:

python add_faces.py


This generates:

data/faces_data.pkl
data/names.pkl


These are used by the face recognition model.

🧐 Troubleshooting
❌ mongosh not recognized

Add MongoDB bin folder to PATH:

C:\Program Files\MongoDB\Server\X.Y\bin

❌ Unable to connect to MongoDB in Streamlit

Check service:

mongo


or:

mongosh


Make sure this works:

mongo mongodb://127.0.0.1:27017

❌ Student names appearing automatically

Check demo/test data inserted in code:

insert_one()

default admin accounts

sample entries in students.json

📬 Queries & Support

If you face issues with:

database insertion

camera not opening

face training

Streamlit errors

MongoDB connection

Create an issue in this repo or reach out.

❤️ Acknowledgements

OpenCV for face detection

Streamlit for UI

MongoDB for backend data handling

📄 License

This project is open-source and free to use for educational purposes.




Required for your UI & server:

streamlit

Required for DB:

pymongo

Required for face recognition & camera:

opencv-python

opencv-contrib-python
(needed if you use LBPH face recognizer, EigenFace, FisherFace)

Required for CSV/analytics:

pandas

matplotlib

numpy

Required for saving/loading faces:

cloudpickle

Pillow

Required for hashing/storing passwords:

bcrypt

Other compatibility:

requests

protobuf

✅ Install everything
pip install -r requirements.txt

# projects
 979d8d4c0cb0d76f52834ee039d0cdc39e906987
