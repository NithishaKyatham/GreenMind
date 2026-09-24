# GreenMind External Validation

This is an offline research pipeline for measuring the existing GreenMind EfficientNet-B0 model on lawfully acquired external images. It does not modify production inference, model weights, preprocessing, class mappings, confidence handling, recommendations, LIME, or the frontend.

## Tracks

### Direct overlap

Use a prepared CSV manifest. Only rows with `mapping_status=EXACT` enter the primary direct-overlap evaluation automatically. The source `original_label` is preserved. Generic labels, broad disease names, multi-label records, `complex` records, and unsupported crops are excluded unless a documented mapping rule is approved.

### OOD

Use a separate manifest with unsupported crops or classes, such as cassava or pear. OOD evaluation reports rejection and confident-known-class error behavior. Ordinary 38-class accuracy is not a meaningful primary OOD metric.

## Manifest

The manifest supports these columns:

```text
external_image_id, local_relative_path, dataset_name, dataset_version,
original_label, mapped_greenmind_label, mapping_status, crop, source_url,
source_dataset, collection_environment, plant_id, field_id,
capture_session_id, device_id, annotation_confidence, annotation_source,
sha256, perceptual_hash, duplicate_group_id, split, exclusion_reason
```

Metadata that a source does not provide remains blank. It must not be invented. `mapping_status` must be one of:

```text
EXACT
POSSIBLE_BUT_REQUIRES_DOCUMENTED_RULE
AMBIGUOUS
UNSUPPORTED
```

## Hashing and duplicates

`build_external_manifest.py` can add SHA-256 hashes and optional average perceptual hashes. SHA-256 identifies exact byte duplicates. Perceptual-hash matches are probable visual duplicates only and require manual review; they do not prove identity.

`check_external_duplicates.py` writes a report with:

- `exact_duplicate`
- `probable_visual_duplicate_review_required`
- `unique_or_unhashed`

## Evaluation commands

Run from `backend/` after an authorized dataset and manifest exist:

```powershell
python scripts/build_external_manifest.py `
  --input-csv C:\authorized\source_manifest.csv `
  --image-root C:\authorized\images `
  --output-csv C:\authorized\manifest.csv `
  --perceptual-hash

python scripts/check_external_duplicates.py `
  --manifest C:\authorized\manifest.csv `
  --output ..\reports\external_validation\duplicates.csv

python scripts/evaluate_external_dataset.py `
  --manifest C:\authorized\manifest.csv `
  --image-root C:\authorized\images `
  --dataset-name example_dataset `
  --mode direct

python scripts/evaluate_external_dataset.py `
  --manifest C:\authorized\ood_manifest.csv `
  --image-root C:\authorized\images `
  --dataset-name example_dataset_ood `
  --mode ood
```

The evaluator uses the configured existing model loader, the exact production preprocessing function, the configured class ordering, and the production confidence threshold of `0.60`. It rejects fallback mode and requires the real 38-class model.

## Outputs

Results are written under:

```text
reports/external_validation/<dataset_name>/
```

Expected outputs include:

```text
run_metadata.json
manifest_snapshot.csv
metrics.json
per_class_metrics.csv
confusion_matrix.json
confidence_statistics.json
failure_cases.csv
excluded_rows.csv        # only when exclusions exist
plots/
```

The current infrastructure writes machine-readable confidence and threshold data. It does not fabricate plots or reports when no dataset is present.

## Metrics

Direct evaluation reports accuracy, macro precision, macro recall, macro F1, weighted F1, per-class metrics, supports, confusion matrix, mapping-status counts, represented classes, and images per class.

Confidence analysis reports mean, median, standard deviation, minimum, maximum, 5th/25th/50th/75th/95th percentiles, correct/incorrect distributions, percentage below `0.60`, accepted coverage, accepted accuracy, rejected coverage, and accuracy on all images.

OOD analysis reports rejection rate, confident-known-class error rate, confidence statistics, predicted-class distribution, and threshold analysis. A confident known GreenMind class on an unsupported image is an OOD failure, not a correct diagnosis.

## Difficult conditions

Condition fields may identify `natural_background`, `multiple_leaves`, `variable_lighting`, `blur`, `occlusion`, `viewing_angle`, `mobile_camera`, `complex_symptoms`, or `maturity_variation`. The evaluator does not infer these conditions from filenames. A subset is meaningful only when the manifest provides source evidence or a documented annotation.

## Failure analysis

Failure exports preserve original labels and include the prediction, confidence, acceptance state, source URL, hashes, condition metadata, reviewer, and notes. The pipeline automatically flags high-confidence wrong predictions at confidence `>= 0.90`. Biological causes such as background or lighting are not assigned automatically; unknown causes remain `UNREVIEWED`.

## Reproducibility

`run_metadata.json` records dataset metadata when supplied, manifest/model/class mapping hashes, architecture, input size, preprocessing mean/std, confidence threshold, random seed, Python/PyTorch/torchvision/Pillow/scikit-learn versions, script version, and experiment timestamp. Unknown dataset metadata remains null.

## PlantVillage overlap limitation

Separate authorship or field collection does not prove image-level independence from PlantVillage. If the original PlantVillage files are unavailable, GreenMind can report only documented provenance and cannot claim that no exact or near-duplicate images exist.

## Production boundary

This pipeline is standalone. It does not call the production prediction endpoint and does not alter production inference behavior, model weights, preprocessing, class names, confidence threshold, recommendations, LIME, or frontend code.
