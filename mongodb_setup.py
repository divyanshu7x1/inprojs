"""
MongoDB Setup and Verification Script

This script helps verify that MongoDB collections are properly set up:
1. students - stores student IDs and passwords
2. attendance - stores attendance records

Run this script to check your MongoDB setup.
"""

from pymongo import MongoClient
from datetime import datetime

# MongoDB configuration
MONGO_URI = "mongodb://127.0.0.1:27017"
DB_NAME = "attendance_db"
STUDENTS_COL = "students"
ATTENDANCE_COL = "attendance"

def get_db():
    """Get MongoDB database connection"""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        client.server_info()  # Test connection
        return client[DB_NAME]
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
        print("   Make sure MongoDB is running on 127.0.0.1:27017")
        return None

def verify_collections():
    """Verify that both collections exist and show their structure"""
    db = get_db()
    if db is None:
        return False
    
    print("=" * 60)
    print("MongoDB Collections Verification")
    print("=" * 60)
    
    # Check students collection
    students_col = db[STUDENTS_COL]
    students_count = students_col.count_documents({})
    print(f"\n📚 Collection: {STUDENTS_COL}")
    print(f"   Documents: {students_count}")
    
    if students_count > 0:
        sample = students_col.find_one()
        print(f"   Sample document structure:")
        for key in sample.keys():
            if key != "password_hash":
                print(f"      - {key}: {type(sample[key]).__name__}")
            else:
                print(f"      - {key}: <hashed>")
    
    # Check attendance collection
    attendance_col = db[ATTENDANCE_COL]
    attendance_count = attendance_col.count_documents({})
    print(f"\n📋 Collection: {ATTENDANCE_COL}")
    print(f"   Documents: {attendance_count}")
    
    if attendance_count > 0:
        sample = attendance_col.find_one()
        print(f"   Sample document structure:")
        for key in sample.keys():
            print(f"      - {key}: {type(sample[key]).__name__}")
    
    # Create indexes for better performance
    print(f"\n🔍 Creating indexes for better performance...")
    try:
        # Index on student_id for fast lookups
        students_col.create_index("student_id", unique=True)
        print("   ✅ Index created on students.student_id")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("   ℹ️  Index on students.student_id already exists")
        else:
            print(f"   ⚠️  Could not create index on students.student_id: {e}")
    
    try:
        # Index on student_name and timestamp for attendance queries
        attendance_col.create_index([("student_name", 1), ("timestamp", -1)])
        print("   ✅ Index created on attendance.student_name and timestamp")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("   ℹ️  Index on attendance already exists")
        else:
            print(f"   ⚠️  Could not create index on attendance: {e}")
    
    try:
        # Index on date for filtering
        attendance_col.create_index("date")
        print("   ✅ Index created on attendance.date")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("   ℹ️  Index on attendance.date already exists")
        else:
            print(f"   ⚠️  Could not create index on attendance.date: {e}")
    
    print("\n" + "=" * 60)
    print("✅ MongoDB setup verification complete!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    verify_collections()

