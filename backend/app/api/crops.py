"""
Crops supported by the trained model.

The seed list mirrors exactly the 14 crops present in ml/models/class_names.json
(38 disease classes total). Do not add crops here that the model wasn't
trained on — the dropdown must never promise support GreenMind doesn't have.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.crop import Crop
from app.schemas.crop import CropOut

router = APIRouter(prefix="/crops", tags=["Crops"])

# name = the raw crop token used in the model's class names (before "___").
# Only display_name_en is guaranteed accurate; Telugu/Hindi are provided
# where the translation is common and unambiguous, left null otherwise
# rather than risk an incorrect translation.
_SEED_CROPS = [
    {"name": "Apple", "display_name_en": "Apple", "display_name_te": "ఆపిల్", "display_name_hi": "सेब"},
    {"name": "Blueberry", "display_name_en": "Blueberry"},
    {"name": "Cherry_(including_sour)", "display_name_en": "Cherry"},
    {"name": "Corn_(maize)", "display_name_en": "Corn (Maize)", "display_name_te": "మొక్కజొన్న", "display_name_hi": "मक्का"},
    {"name": "Grape", "display_name_en": "Grape", "display_name_te": "ద్రాక్ష", "display_name_hi": "अंगूर"},
    {"name": "Orange", "display_name_en": "Orange", "display_name_te": "నారింజ", "display_name_hi": "संतरा"},
    {"name": "Peach", "display_name_en": "Peach"},
    {"name": "Pepper,_bell", "display_name_en": "Bell Pepper", "display_name_te": "క్యాప్సికం", "display_name_hi": "शिमला मिर्च"},
    {"name": "Potato", "display_name_en": "Potato", "display_name_te": "బంగాళాదుంప", "display_name_hi": "आलू"},
    {"name": "Raspberry", "display_name_en": "Raspberry"},
    {"name": "Soybean", "display_name_en": "Soybean", "display_name_te": "సోయాబీన్", "display_name_hi": "सोयाबीन"},
    {"name": "Squash", "display_name_en": "Squash"},
    {"name": "Strawberry", "display_name_en": "Strawberry"},
    {"name": "Tomato", "display_name_en": "Tomato", "display_name_te": "టమోటా", "display_name_hi": "टमाटर"},
]


@router.get("", response_model=list[CropOut])
def list_crops(db: Session = Depends(get_db)):
    existing = db.query(Crop).count()
    if existing != len(_SEED_CROPS):
        # Re-sync on mismatch (e.g. upgrading from the old 2-crop seed list)
        # rather than only seeding when the table is completely empty.
        existing_names = {c.name for c in db.query(Crop).all()}
        for c in _SEED_CROPS:
            if c["name"] not in existing_names:
                db.add(Crop(**c))
        db.commit()
    return db.query(Crop).order_by(Crop.display_name_en).all()
