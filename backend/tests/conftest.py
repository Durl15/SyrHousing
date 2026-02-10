import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.database import Base, get_db
from backend.main import app
from backend.models import Program, UserProfile, WatchlistEntry, ScanState

TEST_DATABASE_URL = "sqlite:///./test_syrhousing.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def seed_profile(db):
    p = UserProfile(
        profile_name="default",
        city="Syracuse",
        county="Onondaga",
        is_senior=True,
        is_fixed_income=True,
        repair_needs=["roof", "heating", "structural"],
        repair_severity={"roof": 3, "heating": 2, "structural": 4},
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@pytest.fixture
def seed_programs(db):
    programs = [
        Program(
            program_key="hhq_urgent_care_syracuse",
            name="HHQ Urgent Care (Syracuse)",
            menu_category="URGENT SAFETY",
            repair_tags="roof;heating;electrical;structural;plumbing;stairs",
            priority_rank=100.0,
            max_benefit="Up to 20000",
            status_or_deadline="Rolling - Call to confirm",
            agency="Home HeadQuarters (HHQ)",
            phone="(315) 474-1939",
            website="https://www.homehq.org/homeowner-loans-grants",
        ),
        Program(
            program_key="nys_restore_senior_60",
            name="NYS RESTORE (Senior 60+)",
            menu_category="URGENT SAFETY",
            repair_tags="roof;heating;structural;electrical;plumbing;accessibility",
            priority_rank=100.0,
            max_benefit="10000-20000",
            agency="NYS HCR (via local administrators)",
            website="https://hcr.ny.gov/restore-program",
        ),
        Program(
            program_key="weatherization_peace_inc",
            name="Weatherization (PEACE Inc.)",
            menu_category="ENERGY & BILLS",
            repair_tags="insulation;air sealing;heating;windows",
            priority_rank=60.0,
            agency="PEACE Inc.",
            website="https://www.peace-caa.org/programs/energyhousing/",
        ),
        Program(
            program_key="access_to_home_nys",
            name="Access to Home (NYS)",
            menu_category="AGING IN PLACE",
            repair_tags="ramps;grab bars;bathroom;mobility",
            priority_rank=40.0,
            agency="NYS HCR (local providers)",
        ),
    ]
    for p in programs:
        db.add(p)
    db.commit()
    for p in programs:
        db.refresh(p)
    return programs


@pytest.fixture
def seed_watchlist(db):
    entries = [
        WatchlistEntry(
            program_key="hhq_homeowner",
            name="Home HeadQuarters - Homeowner Loans & Grants",
            url="https://www.homehq.org/homeowner-loans-grants",
            open_keywords="apply now;applications open;urgent care",
            closed_keywords="program currently closed;not accepting",
        ),
        WatchlistEntry(
            program_key="hcr_restore",
            name="NYS HCR - RESTORE Program",
            url="https://hcr.ny.gov/restore-program",
            open_keywords="how to apply;application;accepting",
            closed_keywords="applications are not being accepted;not accepting;closed",
        ),
    ]
    for e in entries:
        db.add(e)
    db.commit()
    for e in entries:
        db.refresh(e)
    return entries
