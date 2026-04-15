"""Streamlit page: migrate saved face pickles into MongoDB on-demand.

This page intentionally avoids running heavy migration logic at import time so
Streamlit's multi-page loader doesn't execute it automatically. Click the
button below to run the migration.
"""
import streamlit as st
import pickle
import numpy as np
from pymongo import MongoClient
from pathlib import Path

# CONFIG - change if your DB is different
MONGO_URI = "mongodb://127.0.0.1:27017"
DB_NAME = "attendance_db"
FACES_COL = "faces"
DATA_DIR = Path("data")
FACES_PATH = DATA_DIR / "faces_data.pkl"
NAMES_PATH = DATA_DIR / "names.pkl"

st.title("📦 Migrate saved faces into MongoDB")
st.write("This will read `data/faces_data.pkl` and `data/names.pkl` and insert per-name documents into MongoDB. Run only when ready.")

if not FACES_PATH.exists() or not NAMES_PATH.exists():
    st.warning("Missing pickle files. Ensure `data/faces_data.pkl` and `data/names.pkl` exist before migrating.")
    st.stop()

if st.button("Run migration now"):
    try:
        with open(FACES_PATH, "rb") as f:
            faces = pickle.load(f)
        with open(NAMES_PATH, "rb") as f:
            names = pickle.load(f)

        faces = np.asarray(faces)
        if len(faces) != len(names):
            st.warning(f"Length mismatch: faces={len(faces)} names={len(names)}. Truncating to min length.")
            m = min(len(faces), len(names))
            faces = faces[:m]
            names = names[:m]

        # Group faces by name
        grouped = {}
        for arr, name in zip(faces, names):
            grouped.setdefault(name, []).append(arr)

        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        faces_col = db[FACES_COL]

        inserted = 0
        skipped = 0
        for name, face_list in grouped.items():
            if faces_col.find_one({"name": name}):
                skipped += 1
                continue
            # Convert numpy arrays to plain lists for BSON serialization
            faces_serialized = [np.asarray(a).tolist() for a in face_list]
            doc = {"name": name, "faces": faces_serialized, "count": len(faces_serialized)}
            faces_col.insert_one(doc)
            inserted += 1

        client.close()
        st.success(f"Migration complete — inserted {inserted} documents, skipped {skipped} existing names.")
    except Exception as e:
        st.error(f"Migration failed: {e}")
