"""
Test Attendance Save - Manually test saving attendance to MongoDB

This script will test if attendance can be saved to MongoDB.
Run this after marking attendance to see if the save is working.
"""

from pymongo import MongoClient, WriteConcern
from datetime import datetime
import sys

MONGO_URI = "mongodb://127.0.0.1:27017"
DB_NAME = "attendance_db"
ATTENDANCE_COL = "attendance"

def test_attendance_save():
    """Test saving attendance to MongoDB"""
    print("=" * 70)
    print("Testing Attendance Save to MongoDB")
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
        attendance_col = db[ATTENDANCE_COL]
        
        # Test insert
        test_doc = {
            "student_name": "Test Student",
            "date": datetime.now().strftime("%d-%m-%Y"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "status": "Present",
            "timestamp": datetime.now(),
            "created_at": datetime.utcnow(),
            "marked_by": "test_script"
        }
        
        print(f"\n📝 Attempting to insert test attendance...")
        print(f"   Student: {test_doc['student_name']}")
        print(f"   Date: {test_doc['date']}")
        print(f"   Time: {test_doc['time']}")
        
        # Insert with write concern
        attendance_col_with_wc = attendance_col.with_options(
            write_concern=WriteConcern(w=1, wtimeout=5000)
        )
        result = attendance_col_with_wc.insert_one(test_doc)
        
        if result.inserted_id:
            print(f"✅ Insert successful! ID: {result.inserted_id}")
            
            # Verify
            verify = attendance_col.find_one({"_id": result.inserted_id})
            if verify:
                print("✅ Verification: Document found in database!")
                
                # Count total documents
                total = attendance_col.count_documents({})
                print(f"\n📊 Total attendance documents: {total}")
                
                # Clean up test
                attendance_col.delete_one({"_id": result.inserted_id})
                print("✅ Test document cleaned up")
                
                return True
            else:
                print("❌ Verification failed: Document not found after insert!")
                return False
        else:
            print("❌ Insert failed: No ID returned")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_attendance_save()
    if success:
        print("\n✅ Attendance save is working! The issue might be in test.py")
        print("   Check the console output when marking attendance.")
    else:
        print("\n❌ Attendance save failed. Check MongoDB connection.")

