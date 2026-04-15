"""
Verify MongoDB Data - Check if data is actually being saved

This script will check if data exists in MongoDB and show detailed information.
"""

from pymongo import MongoClient, WriteConcern
from datetime import datetime
import json

MONGO_URI = "mongodb://127.0.0.1:27017"
DB_NAME = "attendance_db"
STUDENTS_COL = "students"
ATTENDANCE_COL = "attendance"

def verify_data():
    """Verify data in MongoDB"""
    print("=" * 70)
    print("MongoDB Data Verification")
    print("=" * 70)
    
    try:
        # Connect
        client = MongoClient(
            MONGO_URI, 
            serverSelectionTimeoutMS=5000
        )
        client.server_info()
        print("✅ Connected to MongoDB")
        
        db = client[DB_NAME]
        print(f"✅ Database '{DB_NAME}' accessed")
        
        # List all collections
        collections = db.list_collection_names()
        print(f"\n📋 Collections in database: {collections}")
        
        # Check students collection
        students_col = db[STUDENTS_COL]
        student_count = students_col.count_documents({})
        print(f"\n👥 STUDENTS COLLECTION")
        print(f"   Total documents: {student_count}")
        
        if student_count > 0:
            print("\n   All students:")
            for i, student in enumerate(students_col.find(), 1):
                print(f"\n   Student #{i}:")
                print(f"      ID: {student.get('_id')}")
                print(f"      Student ID: {student.get('student_id')}")
                print(f"      Name: {student.get('name')}")
                print(f"      Created: {student.get('created_at')}")
        else:
            print("   ⚠️  No students found!")
        
        # Check attendance collection
        attendance_col = db[ATTENDANCE_COL]
        attendance_count = attendance_col.count_documents({})
        print(f"\n📊 ATTENDANCE COLLECTION")
        print(f"   Total documents: {attendance_count}")
        
        if attendance_count > 0:
            print("\n   Recent attendance records (last 10):")
            for i, record in enumerate(attendance_col.find().sort("timestamp", -1).limit(10), 1):
                print(f"\n   Record #{i}:")
                print(f"      ID: {record.get('_id')}")
                print(f"      Student: {record.get('student_name')}")
                print(f"      Date: {record.get('date')}")
                print(f"      Time: {record.get('time')}")
                print(f"      Status: {record.get('status')}")
                print(f"      Marked by: {record.get('marked_by', 'N/A')}")
        else:
            print("   ⚠️  No attendance records found!")
        
        # Test write with explicit write concern
        print("\n" + "=" * 70)
        print("Testing Write Operation")
        print("=" * 70)
        
        test_doc = {
            "test": True,
            "timestamp": datetime.now(),
            "message": "Test write operation"
        }
        
        # Write with explicit acknowledgment
        result = students_col.with_options(
            write_concern=WriteConcern(w=1, wtimeout=5000)
        ).insert_one(test_doc)
        
        print(f"✅ Test document inserted: {result.inserted_id}")
        
        # Verify it was written
        found = students_col.find_one({"_id": result.inserted_id})
        if found:
            print("✅ Test document verified in database!")
        else:
            print("❌ Test document NOT found after insert!")
        
        # Clean up
        students_col.delete_one({"_id": result.inserted_id})
        print("✅ Test document cleaned up")
        
        # Check database stats
        print("\n" + "=" * 70)
        print("Database Statistics")
        print("=" * 70)
        stats = db.command("dbStats")
        print(f"   Database size: {stats.get('dataSize', 0)} bytes")
        print(f"   Storage size: {stats.get('storageSize', 0)} bytes")
        print(f"   Collections: {stats.get('collections', 0)}")
        print(f"   Objects: {stats.get('objects', 0)}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    verify_data()

