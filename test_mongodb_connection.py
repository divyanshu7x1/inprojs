"""
MongoDB Connection and Data Saving Test Script

This script tests if MongoDB is working correctly and can save/retrieve data.
Run this to diagnose why data isn't appearing in MongoDB Compass.
"""

from pymongo import MongoClient
from datetime import datetime
import sys

# MongoDB configuration
MONGO_URI = "mongodb://127.0.0.1:27017"
DB_NAME = "attendance_db"
STUDENTS_COL = "students"
ATTENDANCE_COL = "attendance"

def test_connection():
    """Test MongoDB connection"""
    print("=" * 60)
    print("Testing MongoDB Connection")
    print("=" * 60)
    
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Test connection
        client.server_info()
        print("✅ MongoDB connection successful!")
        print(f"   URI: {MONGO_URI}")
        return client
    except Exception as e:
        print(f"❌ MongoDB connection failed!")
        print(f"   Error: {e}")
        print("\nTroubleshooting:")
        print("   1. Make sure MongoDB is running")
        print("   2. Check if MongoDB is listening on port 27017")
        print("   3. Try: mongosh mongodb://127.0.0.1:27017")
        return None

def test_database_operations(client):
    """Test database operations"""
    if client is None:
        return False
    
    print("\n" + "=" * 60)
    print("Testing Database Operations")
    print("=" * 60)
    
    try:
        db = client[DB_NAME]
        print(f"✅ Database '{DB_NAME}' accessed")
        
        # Test students collection
        students_col = db[STUDENTS_COL]
        print(f"✅ Collection '{STUDENTS_COL}' accessed")
        
        # Test attendance collection
        attendance_col = db[ATTENDANCE_COL]
        print(f"✅ Collection '{ATTENDANCE_COL}' accessed")
        
        # Test insert into students
        test_student = {
            "student_id": "TEST001",
            "name": "Test Student",
            "password_hash": "test_hash_12345",
            "extra": "Test Class",
            "created_at": datetime.utcnow().isoformat(),
            "test_entry": True  # Mark as test so we can delete it
        }
        
        result = students_col.insert_one(test_student)
        print(f"✅ Test student inserted with ID: {result.inserted_id}")
        
        # Verify it was saved
        found = students_col.find_one({"student_id": "TEST001"})
        if found:
            print("✅ Test student found in database!")
            print(f"   Name: {found.get('name')}")
        else:
            print("❌ Test student NOT found after insert!")
            return False
        
        # Test insert into attendance
        test_attendance = {
            "student_name": "Test Student",
            "date": datetime.now().strftime("%d-%m-%Y"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "status": "Present",
            "timestamp": datetime.now(),
            "created_at": datetime.utcnow(),
            "marked_by": "test_script",
            "test_entry": True  # Mark as test so we can delete it
        }
        
        result = attendance_col.insert_one(test_attendance)
        print(f"✅ Test attendance inserted with ID: {result.inserted_id}")
        
        # Verify it was saved
        found = attendance_col.find_one({"student_name": "Test Student", "test_entry": True})
        if found:
            print("✅ Test attendance found in database!")
            print(f"   Date: {found.get('date')}")
            print(f"   Status: {found.get('status')}")
        else:
            print("❌ Test attendance NOT found after insert!")
            return False
        
        # Count documents
        student_count = students_col.count_documents({})
        attendance_count = attendance_col.count_documents({})
        
        print(f"\n📊 Current Database Status:")
        print(f"   Students: {student_count} documents")
        print(f"   Attendance: {attendance_count} documents")
        
        # Clean up test entries
        print("\n🧹 Cleaning up test entries...")
        students_col.delete_many({"test_entry": True})
        attendance_col.delete_many({"test_entry": True})
        print("✅ Test entries removed")
        
        return True
        
    except Exception as e:
        print(f"❌ Database operation failed!")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_existing_data(client):
    """Check if there's existing data in the database"""
    if client is None:
        return
    
    print("\n" + "=" * 60)
    print("Checking Existing Data")
    print("=" * 60)
    
    try:
        db = client[DB_NAME]
        students_col = db[STUDENTS_COL]
        attendance_col = db[ATTENDANCE_COL]
        
        student_count = students_col.count_documents({})
        attendance_count = attendance_col.count_documents({})
        
        print(f"Students collection: {student_count} documents")
        if student_count > 0:
            print("\nSample students:")
            for student in students_col.find().limit(3):
                print(f"  - {student.get('student_id')}: {student.get('name')}")
        
        print(f"\nAttendance collection: {attendance_count} documents")
        if attendance_count > 0:
            print("\nSample attendance records:")
            for record in attendance_col.find().limit(3):
                print(f"  - {record.get('student_name')} on {record.get('date')} - {record.get('status')}")
        
    except Exception as e:
        print(f"❌ Error checking existing data: {e}")

def main():
    print("\n" + "=" * 60)
    print("MongoDB Diagnostic Test")
    print("=" * 60)
    print(f"Database: {DB_NAME}")
    print(f"Collections: {STUDENTS_COL}, {ATTENDANCE_COL}")
    print()
    
    # Test connection
    client = test_connection()
    if client is None:
        print("\n❌ Cannot proceed without MongoDB connection.")
        print("   Please start MongoDB and try again.")
        sys.exit(1)
    
    # Check existing data
    check_existing_data(client)
    
    # Test operations
    success = test_database_operations(client)
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed! MongoDB is working correctly.")
        print("\nIf data still doesn't appear in Compass:")
        print("  1. Refresh Compass (F5)")
        print("  2. Check you're connected to the same database")
        print("  3. Check database name: attendance_db")
        print("  4. Check collection names: students, attendance")
    else:
        print("❌ Some tests failed. Check the errors above.")
    print("=" * 60)

if __name__ == "__main__":
    main()

