"""
Evaluates the trained GreenMind crop-disease model on the held-out test set.

Calculates:
- Accuracy
- Macro precision, recall, F1
- Weighted precision, recall, F1
- Per-class precision, recall, F1
- Confusion matrix

No scikit-learn or matplotlib required.

Usage:
    python ml/training/evaluate.py --data_dir ml/dataset/processed --model_path ml/models/crop_disease_model.pt
"""

import argparse
import json
import os

import numpy as np
import torch
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder

from model_utils import build_model, get_transforms


def calculate_metrics(cm):
    """Calculate classification metrics from a confusion matrix."""

    num_classes = cm.shape[0]
    total = cm.sum()

    per_class = []

    for i in range(num_classes):
        tp = cm[i, i]
        fp = cm[:, i].sum() - tp
        fn = cm[i, :].sum() - tp
        support = cm[i, :].sum()

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        per_class.append(
            {
                "precision": float(precision),
                "recall": float(recall),
                "f1-score": float(f1),
                "support": int(support),
            }
        )

    accuracy = (
        float(np.trace(cm) / total)
        if total > 0
        else 0.0
    )

    macro_precision = float(
        np.mean([x["precision"] for x in per_class])
    )
    macro_recall = float(
        np.mean([x["recall"] for x in per_class])
    )
    macro_f1 = float(
        np.mean([x["f1-score"] for x in per_class])
    )

    supports = np.array(
        [x["support"] for x in per_class],
        dtype=float,
    )

    if supports.sum() > 0:
        weighted_precision = float(
            np.average(
                [x["precision"] for x in per_class],
                weights=supports,
            )
        )
        weighted_recall = float(
            np.average(
                [x["recall"] for x in per_class],
                weights=supports,
            )
        )
        weighted_f1 = float(
            np.average(
                [x["f1-score"] for x in per_class],
                weights=supports,
            )
        )
    else:
        weighted_precision = 0.0
        weighted_recall = 0.0
        weighted_f1 = 0.0

    return {
        "accuracy": accuracy,
        "macro avg": {
            "precision": macro_precision,
            "recall": macro_recall,
            "f1-score": macro_f1,
        },
        "weighted avg": {
            "precision": weighted_precision,
            "recall": weighted_recall,
            "f1-score": weighted_f1,
        },
        "per_class": per_class,
    }


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data_dir",
        default="ml/dataset/processed",
    )

    parser.add_argument(
        "--model_path",
        default="ml/models/crop_disease_model.pt",
    )

    parser.add_argument(
        "--arch",
        default="efficientnet_b0",
        choices=[
            "efficientnet_b0",
            "mobilenet_v3",
            "resnet18",
        ],
    )

    parser.add_argument(
        "--input_size",
        type=int,
        default=224,
    )

    parser.add_argument(
        "--out_dir",
        default="ml/models",
    )

    args = parser.parse_args()

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print(f"Using device: {device}")

    # Evaluation transforms must match inference transforms.
    _, eval_tf = get_transforms(args.input_size)

    test_dir = os.path.join(
        args.data_dir,
        "test",
    )

    if not os.path.isdir(test_dir):
        raise FileNotFoundError(
            f"Test directory not found: {test_dir}"
        )

    if not os.path.isfile(args.model_path):
        raise FileNotFoundError(
            f"Model not found: {args.model_path}"
        )

    test_ds = ImageFolder(
        test_dir,
        transform=eval_tf,
    )

    test_loader = DataLoader(
        test_ds,
        batch_size=32,
        shuffle=False,
        num_workers=0,
    )

    class_names = test_ds.classes
    num_classes = len(class_names)

    print(f"Test images: {len(test_ds)}")
    print(f"Classes: {num_classes}")

    # Build exactly the same architecture used during training.
    model = build_model(
        args.arch,
        num_classes=num_classes,
    ).to(device)

    state_dict = torch.load(
        args.model_path,
        map_location=device,
    )

    model.load_state_dict(state_dict)
    model.eval()

    all_preds = []
    all_labels = []

    print("\nRunning test-set inference...")

    with torch.no_grad():

        for batch_index, (images, labels) in enumerate(
            test_loader,
            start=1,
        ):

            images = images.to(device)

            outputs = model(images)

            predictions = outputs.argmax(
                dim=1
            ).cpu().numpy()

            all_preds.extend(
                predictions.tolist()
            )

            all_labels.extend(
                labels.numpy().tolist()
            )

            if batch_index % 10 == 0:
                print(
                    f"  Processed {min(batch_index * 32, len(test_ds))}"
                    f"/{len(test_ds)} images..."
                )

    # Create confusion matrix.
    cm = np.zeros(
        (num_classes, num_classes),
        dtype=np.int64,
    )

    for actual, predicted in zip(
        all_labels,
        all_preds,
    ):
        cm[actual, predicted] += 1

    metrics = calculate_metrics(cm)

    accuracy = metrics["accuracy"]
    macro = metrics["macro avg"]
    weighted = metrics["weighted avg"]
    per_class = metrics["per_class"]

    print("\n" + "=" * 75)
    print("GREENMIND TEST SET EVALUATION")
    print("=" * 75)

    print(
        f"\nTest Accuracy       : "
        f"{accuracy:.4f} ({accuracy * 100:.2f}%)"
    )

    print(
        f"Macro Precision     : "
        f"{macro['precision']:.4f}"
    )

    print(
        f"Macro Recall        : "
        f"{macro['recall']:.4f}"
    )

    print(
        f"Macro F1            : "
        f"{macro['f1-score']:.4f}"
    )

    print(
        f"Weighted Precision  : "
        f"{weighted['precision']:.4f}"
    )

    print(
        f"Weighted Recall     : "
        f"{weighted['recall']:.4f}"
    )

    print(
        f"Weighted F1         : "
        f"{weighted['f1-score']:.4f}"
    )

    print("\n" + "-" * 75)
    print("PER-CLASS RESULTS")
    print("-" * 75)

    for name, result in zip(
        class_names,
        per_class,
    ):

        print(
            f"{name:55s} "
            f"P={result['precision']:.4f} "
            f"R={result['recall']:.4f} "
            f"F1={result['f1-score']:.4f} "
            f"N={result['support']}"
        )

    # Save reports.
    os.makedirs(
        args.out_dir,
        exist_ok=True,
    )

    json_path = os.path.join(
        args.out_dir,
        "classification_report.json",
    )

    text_path = os.path.join(
        args.out_dir,
        "classification_report.txt",
    )

    confusion_path = os.path.join(
        args.out_dir,
        "confusion_matrix.json",
    )

    # JSON report.
    report_dict = {
        "model": args.model_path,
        "architecture": args.arch,
        "test_images": len(test_ds),
        "classes": num_classes,
        "accuracy": accuracy,
        "macro avg": macro,
        "weighted avg": weighted,
        "per_class": {},
    }

    for class_name, result in zip(
        class_names,
        per_class,
    ):
        report_dict["per_class"][class_name] = result

    with open(
        json_path,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            report_dict,
            f,
            indent=2,
        )

    # Human-readable report.
    with open(
        text_path,
        "w",
        encoding="utf-8",
    ) as f:

        f.write(
            "GREENMIND TEST SET EVALUATION\n"
        )
        f.write("=" * 75 + "\n\n")

        f.write(
            f"Test images: {len(test_ds)}\n"
        )
        f.write(
            f"Classes: {num_classes}\n\n"
        )

        f.write(
            f"Test Accuracy       : "
            f"{accuracy:.4f} ({accuracy * 100:.2f}%)\n"
        )

        f.write(
            f"Macro Precision     : "
            f"{macro['precision']:.4f}\n"
        )

        f.write(
            f"Macro Recall        : "
            f"{macro['recall']:.4f}\n"
        )

        f.write(
            f"Macro F1            : "
            f"{macro['f1-score']:.4f}\n"
        )

        f.write(
            f"Weighted Precision  : "
            f"{weighted['precision']:.4f}\n"
        )

        f.write(
            f"Weighted Recall     : "
            f"{weighted['recall']:.4f}\n"
        )

        f.write(
            f"Weighted F1         : "
            f"{weighted['f1-score']:.4f}\n\n"
        )

        f.write(
            "PER-CLASS RESULTS\n"
        )
        f.write("-" * 75 + "\n")

        for name, result in zip(
            class_names,
            per_class,
        ):

            f.write(
                f"\n{name}\n"
                f"  Precision: {result['precision']:.4f}\n"
                f"  Recall:    {result['recall']:.4f}\n"
                f"  F1:        {result['f1-score']:.4f}\n"
                f"  Support:   {result['support']}\n"
            )

    # Save raw confusion matrix as JSON.
    confusion_data = {
        "class_names": class_names,
        "matrix": cm.tolist(),
    }

    with open(
        confusion_path,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            confusion_data,
            f,
            indent=2,
        )

    print("\n" + "=" * 75)
    print("EVALUATION COMPLETE")
    print("=" * 75)

    print("\nSaved:")
    print(f"  {json_path}")
    print(f"  {text_path}")
    print(f"  {confusion_path}")

    print(
        "\nThese are the REAL test-set metrics. "
        "Do not report the validation accuracy as the final test accuracy."
    )


if __name__ == "__main__":
    main()