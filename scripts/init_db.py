from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from shared.database import Base, SessionLocal, engine
from shared.seed_data import seed_initial_data
import shared.models  # noqa: F401


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_initial_data(db)
        print("database initialized")
    finally:
        db.close()


if __name__ == "__main__":
    main()
