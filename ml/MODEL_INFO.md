# GreenMind — Trained Model Information

## Architecture
EfficientNet-B0, transfer learning from ImageNet weights, final classifier
layer replaced for 38 output classes (`ml/training/model_utils.py`).

## Classes (38)
Trained on the standard PlantVillage class set, covering 14 crops:
Apple, Blueberry, Cherry, Corn (Maize), Grape, Orange, Peach, Bell Pepper,
Potato, Raspberry, Soybean, Squash, Strawberry, Tomato.

Full list: `ml/models/class_names.json`. **GreenMind can only identify these
38 crop/disease combinations — it does not recognize other crops or
diseases outside this list.** An image of an unsupported crop/disease, or
a low-quality/ambiguous photo, is expected to produce a low-confidence
result rather than a (potentially wrong) specific diagnosis.

## Evaluation (PlantVillage held-out test set)
| Metric | Value |
|---|---|
| Test images | 8,179 |
| Classes | 38 |
| Accuracy | 99.61% |
| Macro precision | 99.45% |
| Macro recall | 99.44% |
| Macro F1 | 99.44% |

Full per-class breakdown: `ml/models/classification_report.json` /
`classification_report.txt`. Confusion matrix: `ml/models/confusion_matrix.json`.

**This is a PlantVillage held-out test-set result, not a real-world field
accuracy figure.** PlantVillage images are lab-captured: single leaf,
plain background, controlled lighting. Real farm photos — multiple leaves,
natural backgrounds, variable lighting, phone camera artifacts — are
harder, and accuracy in the field will be lower than 99.61%. Treat this
number as evidence the model learned the training distribution well, not
as a promise about every photo a farmer will upload.

## Confidence threshold
The backend (`CONFIDENCE_THRESHOLD` env var, default `0.60`) rejects
low-confidence predictions rather than reporting a possibly-wrong specific
diagnosis. Below this threshold, the API returns
`status: "low_confidence"` with a generic safe response and the model's
best guess shown only as an unconfirmed hint (`possible_disease`), never
as a diagnosis.

## Retraining
The model is already trained — do not retrain unless you have a specific
reason (new classes, more data, a different architecture). If you do:
```bash
cd ml/training
python train.py --data_dir ../dataset/processed --epochs 15
python evaluate.py --data_dir ../dataset/processed
```
This overwrites `ml/models/crop_disease_model.pt` and the evaluation
artifacts — back them up first if you want to keep the current results.
