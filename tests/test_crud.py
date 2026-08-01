import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.models import Base
from app.database import crud


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_delete_upload_cascades_analysis(db):
    user = crud.create_user(db, "testuser", "password123", role="analyst")
    upload = crud.create_upload(db, user.id, "test.pdf", "/tmp/test.pdf")
    analysis = crud.create_analysis(db, upload.id, "{}", "result")
    upload_id = upload.id
    analysis_id = analysis.id

    assert crud.delete_upload(db, upload_id) is True
    assert crud.get_upload_by_id(db, upload_id) is None
    assert crud.get_analysis_by_id(db, analysis_id) is None


def test_delete_upload_not_found(db):
    assert crud.delete_upload(db, 999) is False
