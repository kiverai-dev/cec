from typing import Optional, List
from sqlalchemy.orm import Session
from .models import User, Upload, Analysis, Setting
import bcrypt


def create_user(db: Session, username: str, password: str, role: str = "viewer", email: Optional[str] = None) -> User:
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(username=username, password_hash=password_hash, role=role, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
        return None
    return user


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def get_all_users(db: Session) -> List[User]:
    return db.query(User).all()


def update_user(db: Session, user_id: int, **kwargs) -> Optional[User]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    for key, value in kwargs.items():
        if hasattr(user, key):
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> bool:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True


def set_user_active(db: Session, user_id: int, is_active: bool) -> Optional[User]:
    return update_user(db, user_id, is_active=is_active)


def create_upload(db: Session, user_id: int, filename: str, file_path: str) -> Upload:
    upload = Upload(user_id=user_id, filename=filename, file_path=file_path)
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload


def get_upload_by_id(db: Session, upload_id: int) -> Optional[Upload]:
    return db.query(Upload).filter(Upload.id == upload_id).first()


def get_uploads_by_user(db: Session, user_id: int, limit: int = 50) -> List[Upload]:
    return db.query(Upload).filter(Upload.user_id == user_id).order_by(Upload.created_at.desc()).limit(limit).all()


def get_all_uploads(db: Session, limit: int = 100) -> List[Upload]:
    return db.query(Upload).order_by(Upload.created_at.desc()).limit(limit).all()


def update_upload_status(db: Session, upload_id: int, status: str, error_message: Optional[str] = None) -> Optional[Upload]:
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        return None
    upload.status = status
    upload.error_message = error_message
    db.commit()
    db.refresh(upload)
    return upload


def delete_upload(db: Session, upload_id: int) -> bool:
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        return False
    db.delete(upload)
    db.commit()
    return True


def create_analysis(db: Session, upload_id: int, extracted_json: str, result_text: str) -> Analysis:
    analysis = Analysis(upload_id=upload_id, extracted_json=extracted_json, result_text=result_text)
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def get_analysis_by_upload(db: Session, upload_id: int) -> Optional[Analysis]:
    return db.query(Analysis).filter(Analysis.upload_id == upload_id).first()


def get_analysis_by_id(db: Session, analysis_id: int) -> Optional[Analysis]:
    return db.query(Analysis).filter(Analysis.id == analysis_id).first()


def get_setting(db: Session, key: str, default: Optional[str] = None) -> Optional[str]:
    setting = db.query(Setting).filter(Setting.key == key).first()
    if setting:
        return setting.value
    return default


def set_setting(db: Session, key: str, value: str) -> Setting:
    setting = db.query(Setting).filter(Setting.key == key).first()
    if setting:
        setting.value = value
    else:
        setting = Setting(key=key, value=value)
        db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting


def get_all_settings(db: Session) -> dict:
    settings = db.query(Setting).all()
    return {s.key: s.value for s in settings}


def users_exist(db: Session) -> bool:
    return db.query(User).first() is not None
