# How to Check Data Inside MongoDB

This guide shows you multiple ways to view and check data stored in MongoDB.

## Method 1: Using Python Script (Easiest)

I've created a Python script that makes it easy to view your data:

```bash
python view_mongodb_data.py
```

This interactive script allows you to:
- View all students
- View all attendance records
- Filter by date or student name
- View statistics
- See recent records

## Method 2: Using MongoDB Compass (GUI - Recommended)

MongoDB Compass is a graphical tool that makes it easy to browse your data.

### Installation:
1. Download from: https://www.mongodb.com/try/download/compass
2. Install and open MongoDB Compass

### Connection:
1. Open MongoDB Compass
2. Enter connection string: `mongodb://127.0.0.1:27017`
3. Click "Connect"
4. Select database: `attendance_db`
5. Browse collections:
   - `students` - Student IDs and passwords
   - `attendance` - Attendance records

### Features:
- Visual data browser
- Filter and search data
- Edit documents
- View indexes
- Export data

## Method 3: Using MongoDB Shell (mongosh)

MongoDB Shell is a command-line interface.

### Installation:
MongoDB Shell usually comes with MongoDB installation.

### Usage:

```bash
# Connect to MongoDB
mongosh mongodb://127.0.0.1:27017

# Or simply (if default connection)
mongosh
```

### Commands:

```javascript
// Switch to your database
use attendance_db

// View all collections
show collections

// View all students
db.students.find().pretty()

// View all attendance records
db.attendance.find().pretty()

// Count documents
db.students.countDocuments()
db.attendance.countDocuments()

// Find specific student
db.students.find({student_id: "STU001"}).pretty()

// Find attendance by date
db.attendance.find({date: "29-01-2024"}).pretty()

// Find attendance by student name
db.attendance.find({student_name: "John Doe"}).pretty()

// Find recent attendance (last 10)
db.attendance.find().sort({timestamp: -1}).limit(10).pretty()

// Find all Present records
db.attendance.find({status: "Present"}).pretty()

// Count by status
db.attendance.aggregate([
  {$group: {_id: "$status", count: {$sum: 1}}}
])

// Exit
exit
```

## Method 4: Using Python Directly

You can also write your own Python scripts:

```python
from pymongo import MongoClient

# Connect
client = MongoClient("mongodb://127.0.0.1:27017")
db = client["attendance_db"]

# View students
students = db["students"].find()
for student in students:
    print(student)

# View attendance
attendance = db["attendance"].find()
for record in attendance:
    print(record)
```

## Method 5: Quick Check Script

Run the verification script to see summary:

```bash
python mongodb_setup.py
```

This shows:
- Collection names
- Document counts
- Sample document structure
- Index information

## Collection Structures

### Students Collection
```json
{
  "_id": ObjectId("..."),
  "student_id": "STU001",
  "name": "John Doe",
  "password_hash": "abc123...",
  "extra": "Class A",
  "created_at": "2024-01-29T10:00:00"
}
```

### Attendance Collection
```json
{
  "_id": ObjectId("..."),
  "student_name": "John Doe",
  "date": "29-01-2024",
  "time": "10:30:00",
  "status": "Present",
  "timestamp": ISODate("2024-01-29T10:30:00"),
  "created_at": ISODate("2024-01-29T10:30:00"),
  "marked_by": "face_recognition"
}
```

## Common Queries

### Find student by ID
```python
student = db["students"].find_one({"student_id": "STU001"})
```

### Find attendance today
```python
from datetime import datetime
today = datetime.now().strftime("%d-%m-%Y")
attendance = db["attendance"].find({"date": today})
```

### Find all students who marked attendance
```python
students = db["attendance"].distinct("student_name")
```

### Count attendance by status
```python
present = db["attendance"].count_documents({"status": "Present"})
absent = db["attendance"].count_documents({"status": "Absent"})
```

## Troubleshooting

### Can't connect to MongoDB?
1. Make sure MongoDB is running:
   ```bash
   # Windows
   net start MongoDB
   
   # Linux/Mac
   sudo systemctl start mongod
   ```

2. Check if MongoDB is listening on port 27017:
   ```bash
   # Windows
   netstat -an | findstr 27017
   
   # Linux/Mac
   netstat -an | grep 27017
   ```

### No data showing?
- Make sure you're connected to the correct database: `attendance_db`
- Check collection names: `students` and `attendance`
- Try registering a student first or marking attendance

## Tips

1. **Use MongoDB Compass** for the easiest visual browsing
2. **Use the Python script** (`view_mongodb_data.py`) for quick checks
3. **Use mongosh** for advanced queries and scripting
4. **Check indexes** for better query performance

