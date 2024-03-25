from pydantic import BaseModel

class URLBase(BaseModel):
    target_url: str

class URL_short(URLBase):
    is_active: bool
    clicks: int

    class Config:
        #orm_mode = True
        from_attributes = True

class URLInfo(URL_short):
    url: str
    admin_url: str