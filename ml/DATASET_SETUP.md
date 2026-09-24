# Dataset Setup — GreenMind

We do NOT commit dataset images to Git (too large, and PlantVillage's license
requires attribution rather than redistribution-as-code).

## Recommended dataset: PlantVillage

1. Download from Kaggle:
   https://www.kaggle.com/datasets/emmarex/plantdisease
   (or the "New Plant Diseases Dataset (Augmented)" variant for more samples)

2. Extract into:
   ```
   ml/dataset/raw/<CropName>___<DiseaseName>/*.jpg
   ```
   This is PlantVillage's native folder-per-class layout, e.g.:
   ```
   ml/dataset/raw/Tomato___Early_blight/
   ml/dataset/raw/Tomato___healthy/
   ml/dataset/raw/Potato___Late_blight/
   ```

3. Run the split script (created in ML Phase):
   ```
   python ml/training/prepare_dataset.py --raw_dir ml/dataset/raw --out_dir ml/dataset/processed
   ```
   This produces `train/`, `val/`, `test/` splits (default 70/15/15) with
   stratification per class.

## License note
PlantVillage is publicly available for research/educational use. Confirm the
current license terms on the Kaggle page before any commercial deployment,
and credit the original dataset authors (Hughes & Salathé, 2015) in your
report/README.

## Class list
The exact disease classes depend on which crops you include. Do not
hardcode invented classes — generate `ml/dataset/class_names.json` from the
actual folder names present after extraction (the prepare script does this
automatically).
