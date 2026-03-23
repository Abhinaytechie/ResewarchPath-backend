import numpy as np
from sentence_transformers import SentenceTransformer
from database import SessionLocal
from models.domain import Journal
import sys

model = SentenceTransformer("all-MiniLM-L6-v2")

def diagnose(search_query):
    db = SessionLocal()
    try:
        journals = db.query(Journal).all()
        print(f"Total journals: {len(journals)}")
        if not journals:
            print("No journals found!")
            return

        # Check first journal
        sample = journals[0]
        print(f"Sample Journal: {sample.name}")
        print(f"Embedding type: {type(sample.embedding)}")
        
        if sample.embedding is not None:
            vec = np.array(sample.embedding)
            print(f"Vector shape: {vec.shape}")
        else:
            print("Embedding is NONE!")

        query_vec = model.encode(search_query)
        
        scores = []
        for j in journals:
            if j.embedding is None: continue
            j_vec = np.array(j.embedding)
            score = np.dot(query_vec, j_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(j_vec))
            scores.append((j.name, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        print(f"\nTop 5 scores for '{search_query}':")
        for name, s in scores[:5]:
            print(f"  {s:.4f} - {name}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    search = sys.argv[1] if len(sys.argv) > 1 else "diabetic retinopathy"
    diagnose(search)
