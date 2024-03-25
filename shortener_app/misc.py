from sqlalchemy.orm import Session

from . import key_generator, models, schemas

def generate_db_url(db: Session, url: schemas.URLBase) -> models.URL_short:
    key = key_generator.generate_random_key()
    secret_key = f"{key}_{key_generator.generate_random_key(length=8)}"
    db_url = models.URL_short(
        target_url=url.target_url, key=key, secret_key=secret_key
    )
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    return db_url

def get_dburl_with_key(db: Session, url_key: str) -> models.URL_short:
    return (
        db.query(models.URL_short)
        .filter(models.URL_short.key == url_key, models.URL_short.is_active)
        .first()
    )

def get_dburl_with_secret_key(db: Session, secret_key: str) -> models.URL_short:
    return (
        db.query(models.URL_short)
        .filter(models.URL_short.secret_key == secret_key, models.URL_short.is_active)
        .first()
    )

def db_clicks(db: Session, db_url: schemas.URL_short) -> models.URL_short:
    db_url.clicks += 1
    db.commit()
    db.refresh(db_url)
    return db_url

def deactivate_dburl_with_secret_key(db: Session, secret_key: str) -> models.URL_short:
    db_url = get_dburl_with_secret_key(db, secret_key)
    if db_url:
        db_url.is_active = False
        db.commit()
        db.refresh(db_url)
    return db_url