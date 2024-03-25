
import validators
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from . import models, schemas, misc
from . database import SessionLocal, engine
from starlette.datastructures import URL
from .config import get_settings

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def raise_not_found(request):
    message = f"URL '{request.url}' doesn't exist"
    raise HTTPException(status_code=404, detail=message)

def raise_bad_request(message):
    raise HTTPException(status_code=400, detail=message)

def get_admin_info(db_url: models.URL_short) -> schemas.URLInfo:
    base_url = URL(get_settings().base_url)
    admin_endpoint = app.url_path_for(
        "admin info", secret_key=db_url.secret_key
    )
    db_url.url = str(base_url.replace(path=db_url.key))
    db_url.admin_url = str(base_url.replace(path=admin_endpoint))
    return db_url

@app.get("/")
def read_root():
    return "shortURL_thing"

@app.get("/{url_key}")
def forward_to_target_url(
        url_key: str,
        request: Request,
        db: Session = Depends(get_db)
    ):
    # db_url = (
    #     db.query(models.URL_short)
    #     .filter(models.URL_short.key == url_key, models.URL_short.is_active)
    #     .first()
    # )
    if db_url := misc.get_dburl_with_key(db=db, url_key=url_key):
        misc.db_clicks(db=db, db_url=db_url)
        return RedirectResponse(db_url.target_url)
        #return get_admin_info(db_url)
    else:
        raise_not_found(request)

@app.post("/url", response_model=schemas.URLInfo)
def create_url(url: schemas.URLBase, db: Session = Depends(get_db)):
    if not validators.url(url.target_url):
        raise_bad_request(message="URL is invalid")

    db_url = misc.generate_db_url(db=db, url=url)
    # db_url.url = db_url.key
    # db_url.admin_url = db_url.secret_key

    # return db_url
    return get_admin_info(db_url)

@app.get(
    "/admin/{secret_key}",
    name="admin info",
    response_model=schemas.URLInfo,
)
def get_url_info(
    secret_key: str, request: Request, db: Session = Depends(get_db)
):
    if db_url := misc.get_dburl_with_secret_key(db, secret_key=secret_key):
        db_url.url = db_url.key
        db_url.admin_url = db_url.secret_key
        return db_url
    else:
        raise_not_found(request)

@app.delete("/admin/{secret_key}")
def delete_url(
    secret_key: str, request: Request, db: Session = Depends(get_db)
):
    if db_url := misc.deactivate_dburl_with_secret_key(db, secret_key=secret_key):
        message = f"Successfully deleted shortened URL for '{db_url.target_url}'"
        return {"detail": message}
    else:
        raise_not_found(request)