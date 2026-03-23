from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models.domain import Base, Journal
import uuid
import os
from sqlalchemy import text
Base.metadata.create_all(bind=engine)
# Initialize embedding model accurately
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def generate_embedding(journal) -> list[float]:
    topics_str = ", ".join(journal.topics) if journal.topics else ""
    # Focus on semantic information only
    text = (
        f"Journal Name: {journal.name}. "
        f"Research Domain: {journal.domain}. "
        f"Focus Topics: {topics_str}."
    )
    # returns numpy array — convert to plain list for SQLAlchemy
    return embedding_model.encode(text).tolist()

def seed_db():
    db = SessionLocal()

    # Ensure pgvector extension exists
    try:
        db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        db.commit()
    except Exception as e:
        print(f"Note: Could not create extension: {e}")
        db.rollback()

    # Drop old vector column if it exists and ensure embedding is a vector type
    try:
        # Check if embedding is already a vector to avoid unnecessary drops
        db.execute(text("ALTER TABLE journals DROP COLUMN IF EXISTS vector"))
        # We manually ensure embedding is the right type
        db.execute(text("ALTER TABLE journals DROP COLUMN IF EXISTS embedding"))
        db.execute(text("ALTER TABLE journals ADD COLUMN embedding vector(384)"))
        db.commit()
    except Exception as e:
        print(f"Note: Schema update info: {e}")
        db.rollback()

    # Clear existing to ensure fresh vectors for all
    print("Clearing existing journals...")
    db.execute(text("DELETE FROM journals"))
    db.commit()

    journals = [

        # ── COMPUTER SCIENCE (10) ──────────────────────────────────────────────

        Journal(
            name="IEEE Access",
            publisher="IEEE",
            domain="Computer Science",
            index_types=["SCIE", "Scopus"],
            quartile="Q1",
            speed="Fast",
            avg_weeks=4,
            is_free=False,
            cost_note="APC required — waivers available for low-income countries",
            submission_url="https://ieeeaccess.ieee.org/",
            topics=["Artificial Intelligence", "Networking", "Software Engineering", "IoT"],
            impact_factor="3.9"
        ),
        Journal(
            name="Journal of Systems Architecture",
            publisher="Elsevier",
            domain="Computer Science",
            index_types=["SCI", "Scopus"],
            quartile="Q1",
            speed="Normal",
            avg_weeks=12,
            is_free=True,
            cost_note="Free",
            submission_url="https://www.journals.elsevier.com/journal-of-systems-architecture",
            topics=["Embedded Systems", "Hardware Architecture", "Real-Time Systems"],
            impact_factor="5.8"
        ),
        Journal(
            name="Applied Soft Computing",
            publisher="Elsevier",
            domain="Computer Science",
            index_types=["SCIE", "Scopus"],
            quartile="Q1",
            speed="Normal",
            avg_weeks=16,
            is_free=True,
            cost_note="Free",
            submission_url="https://www.journals.elsevier.com/applied-soft-computing",
            topics=["Machine Learning", "Neural Networks", "Fuzzy Logic", "Evolutionary Computation"],
            impact_factor="8.7"
        ),
        Journal(
            name="Digital Communications and Networks",
            publisher="KeAi",
            domain="Computer Science",
            index_types=["SCIE", "Scopus"],
            quartile="Q1",
            speed="Fast",
            avg_weeks=10,
            is_free=True,
            cost_note="Fully Open Access — APC waived",
            submission_url="https://www.keaipublishing.com/en/journals/digital-communications-and-networks/",
            topics=["Networking", "Communications", "Cybersecurity", "5G"],
            impact_factor="7.9"
        ),
        Journal(
            name="Expert Systems with Applications",
            publisher="Elsevier",
            domain="Computer Science",
            index_types=["SCIE", "Scopus"],
            quartile="Q1",
            speed="Normal",
            avg_weeks=12,
            is_free=True,
            cost_note="Free",
            submission_url="https://www.sciencedirect.com/journal/expert-systems-with-applications",
            topics=["AI", "Machine Learning", "Expert Systems", "Deep Learning", "Classification"],
            impact_factor="8.5"
        ),
        Journal(
            name="Egyptian Informatics Journal",
            publisher="Elsevier",
            domain="Computer Science",
            index_types=["Scopus"],
            quartile="Q1",
            speed="Fast",
            avg_weeks=6,
            is_free=True,
            cost_note="Free — Diamond Open Access",
            submission_url="https://www.sciencedirect.com/journal/egyptian-informatics-journal",
            topics=["Computer Science", "AI", "Networks", "Data Science", "Security"],
            impact_factor="5.1"
        ),
        Journal(
            name="AI Open",
            publisher="Elsevier",
            domain="Computer Science",
            index_types=["Scopus"],
            quartile="Q1",
            speed="Fast",
            avg_weeks=6,
            is_free=True,
            cost_note="Free — Diamond Open Access",
            submission_url="https://www.sciencedirect.com/journal/ai-open",
            topics=["AI", "NLP", "Deep Learning", "Reinforcement Learning", "Machine Learning"],
            impact_factor="5.3"
        ),
        Journal(
            name="Neural Computing and Applications",
            publisher="Springer",
            domain="Computer Science",
            index_types=["SCIE", "Scopus"],
            quartile="Q1",
            speed="Normal",
            avg_weeks=12,
            is_free=True,
            cost_note="Free",
            submission_url="https://www.springer.com/journal/521",
            topics=["Neural Networks", "Deep Learning", "Machine Learning", "AI Applications"],
            impact_factor="6.0"
        ),
        Journal(
            name="Multimedia Tools and Applications",
            publisher="Springer",
            domain="Computer Science",
            index_types=["SCIE", "Scopus"],
            quartile="Q2",
            speed="Normal",
            avg_weeks=12,
            is_free=True,
            cost_note="Free",
            submission_url="https://www.springer.com/journal/11042",
            topics=["Multimedia", "Image Processing", "Video Analysis", "Deep Learning", "Computer Vision"],
            impact_factor="3.6"
        ),
        Journal(
            name="Journal of King Saud University – Computer and Information Sciences",
            publisher="Elsevier",
            domain="Computer Science",
            index_types=["SCIE", "Scopus"],
            quartile="Q1",
            speed="Normal",
            avg_weeks=8,
            is_free=True,
            cost_note="Free — Open Access",
            submission_url="https://www.sciencedirect.com/journal/journal-of-king-saud-university-computer-and-information-sciences",
            topics=["Computer Science", "Machine Learning", "Networks", "Cloud Computing", "Cybersecurity"],
            impact_factor="13.3"
        ),

        # ── MEDICAL / BIOMEDICAL (6) ───────────────────────────────────────────

        Journal(
            name="Computers in Biology and Medicine",
            publisher="Elsevier",
            domain="Medical",
            index_types=["SCIE", "Scopus"],
            quartile="Q1",
            speed="Normal",
            avg_weeks=10,
            is_free=True,
            cost_note="Free",
            submission_url="https://www.sciencedirect.com/journal/computers-in-biology-and-medicine",
            topics=["Medical Imaging", "Deep Learning", "Diabetic Retinopathy", "Healthcare AI", "Bioinformatics"],
            impact_factor="7.7"
        ),
        Journal(
            name="Medical Image Analysis",
            publisher="Elsevier",
            domain="Medical",
            index_types=["SCI", "Scopus"],
            quartile="Q1",
            speed="Normal",
            avg_weeks=20,
            is_free=True,
            cost_note="Free",
            submission_url="https://www.sciencedirect.com/journal/medical-image-analysis",
            topics=["Image Processing", "Healthcare AI", "Computer Vision", "Segmentation"],
            impact_factor="10.9"
        ),
        Journal(
            name="Biomedical Signal Processing and Control",
            publisher="Elsevier",
            domain="Medical",
            index_types=["SCIE", "Scopus"],
            quartile="Q1",
            speed="Normal",
            avg_weeks=10,
            is_free=True,
            cost_note="Free",
            submission_url="https://www.sciencedirect.com/journal/biomedical-signal-processing-and-control",
            topics=["Biomedical Signals", "Deep Learning", "Retinal Imaging", "EEG", "ECG"],
            impact_factor="5.1"
        ),
        Journal(
            name="Artificial Intelligence in Medicine",
            publisher="Elsevier",
            domain="Medical",
            index_types=["SCIE", "Scopus"],
            quartile="Q1",
            speed="Normal",
            avg_weeks=12,
            is_free=True,
            cost_note="Free",
            submission_url="https://www.sciencedirect.com/journal/artificial-intelligence-in-medicine",
            topics=["AI", "Clinical Decision Support", "Medical Diagnosis", "Deep Learning"],
            impact_factor="7.5"
        ),
        Journal(
            name="Informatics in Medicine Unlocked",
            publisher="Elsevier",
            domain="Medical",
            index_types=["Scopus"],
            quartile="Q2",
            speed="Fast",
            avg_weeks=5,
            is_free=True,
            cost_note="Free — Diamond Open Access",
            submission_url="https://www.sciencedirect.com/journal/informatics-in-medicine-unlocked",
            topics=["Medical Informatics", "Health AI", "Deep Learning", "Clinical Systems"],
            impact_factor="4.0"
        ),
        Journal(
            name="Heliyon",
            publisher="Elsevier / Cell Press",
            domain="Medical",
            index_types=["SCIE", "Scopus"],
            quartile="Q2",
            speed="Fast",
            avg_weeks=6,
            is_free=True,
            cost_note="Free — Open Access",
            submission_url="https://www.sciencedirect.com/journal/heliyon",
            topics=["Science", "Technology", "Engineering", "Medicine", "Interdisciplinary"],
            impact_factor="4.0"
        ),

        # ── ELECTRONICS / ECE (4) ─────────────────────────────────────────────

        Journal(
            name="International Journal of Electrical and Computer Engineering",
            publisher="IAES",
            domain="Electronics / ECE",
            index_types=["Scopus"],
            quartile="Q2",
            speed="Fast",
            avg_weeks=6,
            is_free=True,
            cost_note="Free — Open Access",
            submission_url="https://ijece.iaescore.com",
            topics=["Electronics", "Signal Processing", "Embedded Systems", "VLSI", "Power Systems"],
            impact_factor="2.1"
        ),
        Journal(
            name="Bulletin of Electrical Engineering and Informatics",
            publisher="IAES",
            domain="Electronics / ECE",
            index_types=["Scopus"],
            quartile="Q2",
            speed="Fast",
            avg_weeks=5,
            is_free=True,
            cost_note="Free — Open Access",
            submission_url="https://beei.org",
            topics=["Electrical Engineering", "Informatics", "Power Systems", "IoT", "Signal Processing"],
            impact_factor="1.8"
        ),
        Journal(
            name="Sensors",
            publisher="MDPI",
            domain="Electronics / ECE",
            index_types=["SCIE", "Scopus"],
            quartile="Q2",
            speed="Fast",
            avg_weeks=4,
            is_free=False,
            cost_note="APC applies — waiver available for low-income countries",
            submission_url="https://www.mdpi.com/journal/sensors",
            topics=["Sensors", "IoT", "Wearable Devices", "Signal Processing", "Wireless Networks"],
            impact_factor="3.9"
        ),
        Journal(
            name="IET Image Processing",
            publisher="Wiley / IET",
            domain="Electronics / ECE",
            index_types=["SCIE", "Scopus"],
            quartile="Q2",
            speed="Normal",
            avg_weeks=10,
            is_free=True,
            cost_note="Free",
            submission_url="https://ietresearch.onlinelibrary.wiley.com/journal/17519667",
            topics=["Image Processing", "Computer Vision", "Deep Learning", "Pattern Recognition"],
            impact_factor="2.3"
        ),

        # ── MECHANICAL (4) ────────────────────────────────────────────────────

        Journal(
            name="International Journal of Mechanical Sciences",
            publisher="Elsevier",
            domain="Mechanical",
            index_types=["SCI", "Scopus"],
            quartile="Q1",
            speed="Normal",
            avg_weeks=14,
            is_free=True,
            cost_note="Free",
            submission_url="https://www.sciencedirect.com/journal/international-journal-of-mechanical-sciences",
            topics=["Solid Mechanics", "Fluid Mechanics", "Thermal Engineering", "Structural Analysis"],
            impact_factor="7.3"
        ),
        Journal(
            name="Journal of Materials Research and Technology",
            publisher="Elsevier",
            domain="Mechanical",
            index_types=["SCIE", "Scopus"],
            quartile="Q1",
            speed="Fast",
            avg_weeks=6,
            is_free=True,
            cost_note="Free — Open Access",
            submission_url="https://www.sciencedirect.com/journal/journal-of-materials-research-and-technology",
            topics=["Materials Science", "Composites", "Metallurgy", "Manufacturing", "Tribology"],
            impact_factor="6.4"
        ),
        Journal(
            name="International Journal of Advanced Manufacturing Technology",
            publisher="Springer",
            domain="Mechanical",
            index_types=["SCIE", "Scopus"],
            quartile="Q2",
            speed="Normal",
            avg_weeks=10,
            is_free=True,
            cost_note="Free",
            submission_url="https://www.springer.com/journal/170",
            topics=["Manufacturing", "CAD/CAM", "Robotics", "Materials", "Precision Engineering"],
            impact_factor="3.4"
        ),
        Journal(
            name="Results in Engineering",
            publisher="Elsevier",
            domain="Mechanical",
            index_types=["Scopus"],
            quartile="Q2",
            speed="Fast",
            avg_weeks=4,
            is_free=True,
            cost_note="Free — Open Access",
            submission_url="https://www.sciencedirect.com/journal/results-in-engineering",
            topics=["Engineering", "Mechanical Systems", "IoT", "Robotics", "Applied Engineering"],
            impact_factor="6.0"
        ),

        # ── CIVIL / ENVIRONMENTAL (3) ─────────────────────────────────────────

        Journal(
            name="Construction and Building Materials",
            publisher="Elsevier",
            domain="Civil / Environmental",
            index_types=["SCI", "Scopus"],
            quartile="Q1",
            speed="Normal",
            avg_weeks=12,
            is_free=True,
            cost_note="Free",
            submission_url="https://www.sciencedirect.com/journal/construction-and-building-materials",
            topics=["Civil Engineering", "Concrete", "Structural Materials", "Construction"],
            impact_factor="7.4"
        ),
        Journal(
            name="Sustainability",
            publisher="MDPI",
            domain="Civil / Environmental",
            index_types=["SCIE", "Scopus"],
            quartile="Q2",
            speed="Fast",
            avg_weeks=5,
            is_free=False,
            cost_note="APC applies — waiver available for low-income countries",
            submission_url="https://www.mdpi.com/journal/sustainability",
            topics=["Sustainability", "Civil Engineering", "Environment", "Green Energy", "Urban Planning"],
            impact_factor="3.9"
        ),
        Journal(
            name="International Journal of Environmental Research and Public Health",
            publisher="MDPI",
            domain="Civil / Environmental",
            index_types=["SCIE", "Scopus"],
            quartile="Q2",
            speed="Fast",
            avg_weeks=5,
            is_free=False,
            cost_note="APC applies — waiver available for low-income countries",
            submission_url="https://www.mdpi.com/journal/ijerph",
            topics=["Environment", "Public Health", "Sustainability", "Climate", "Pollution"],
            impact_factor="4.6"
        ),

        # ── INTERDISCIPLINARY (3) ─────────────────────────────────────────────

        Journal(
            name="Scientific Reports",
            publisher="Nature / Springer",
            domain="Interdisciplinary",
            index_types=["SCIE", "Scopus"],
            quartile="Q1",
            speed="Normal",
            avg_weeks=8,
            is_free=False,
            cost_note="APC applies — waiver available for authors from low-income countries",
            submission_url="https://www.nature.com/srep/",
            topics=["Science", "Engineering", "Biology", "Chemistry", "Medical", "AI"],
            impact_factor="4.6"
        ),
        Journal(
            name="PLOS ONE",
            publisher="PLOS",
            domain="Interdisciplinary",
            index_types=["SCIE", "Scopus"],
            quartile="Q1",
            speed="Normal",
            avg_weeks=10,
            is_free=False,
            cost_note="APC applies — waiver available for low-income countries",
            submission_url="https://journals.plos.org/plosone/",
            topics=["Science", "Medicine", "Engineering", "Biology", "AI", "Data Science"],
            impact_factor="3.7"
        ),
        Journal(
            name="Journal of Open Innovation: Technology, Market, and Complexity",
            publisher="Elsevier",
            domain="Interdisciplinary",
            index_types=["Scopus"],
            quartile="Q2",
            speed="Normal",
            avg_weeks=8,
            is_free=True,
            cost_note="Free — Open Access",
            submission_url="https://www.sciencedirect.com/journal/journal-of-open-innovation-technology-market-and-complexity",
            topics=["Innovation", "Technology Management", "Interdisciplinary Research"],
            impact_factor="4.3"
        ),
    ]

    for journal in journals:
        print(f"Generating embedding for: {journal.name}")
        journal.embedding = generate_embedding(journal)
        db.add(journal)

    db.commit()
    print(f"✅ Database seeded with {len(journals)} journals across 6 domains.")
    db.close()


if __name__ == "__main__":
    seed_db()

