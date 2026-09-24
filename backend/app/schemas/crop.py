from pydantic import BaseModel


class CropOut(BaseModel):
    id: str
    name: str
    display_name_en: str
    display_name_te: str | None = None
    display_name_hi: str | None = None

    class Config:
        from_attributes = True
