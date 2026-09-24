"""
Splits a PlantVillage-style folder-per-class dataset into train/val/test,
and writes class_names.json (used by both training and the backend's
model_loader.py, so class ordering always matches).

Usage:
    python ml/training/prepare_dataset.py --raw_dir ml/dataset/raw --out_dir ml/dataset/processed
"""
import argparse
import json
import os
import random
import shutil


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw_dir", required=True, help="Folder containing one subfolder per class")
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--train_ratio", type=float, default=0.70)
    parser.add_argument("--val_ratio", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)

    class_names = sorted([
        d for d in os.listdir(args.raw_dir) if os.path.isdir(os.path.join(args.raw_dir, d))
    ])
    if not class_names:
        raise SystemExit(f"No class subfolders found in {args.raw_dir}. See ml/DATASET_SETUP.md.")

    for split in ["train", "val", "test"]:
        for cls in class_names:
            os.makedirs(os.path.join(args.out_dir, split, cls), exist_ok=True)

    summary = {}
    for cls in class_names:
        cls_dir = os.path.join(args.raw_dir, cls)
        images = [f for f in os.listdir(cls_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
        random.shuffle(images)

        n_train = int(len(images) * args.train_ratio)
        n_val = int(len(images) * args.val_ratio)

        splits = {
            "train": images[:n_train],
            "val": images[n_train:n_train + n_val],
            "test": images[n_train + n_val:],
        }
        for split, files in splits.items():
            for fname in files:
                shutil.copy2(
                    os.path.join(cls_dir, fname),
                    os.path.join(args.out_dir, split, cls, fname),
                )
        summary[cls] = {k: len(v) for k, v in splits.items()}
        print(f"{cls}: train={len(splits['train'])} val={len(splits['val'])} test={len(splits['test'])}")

    with open(os.path.join(args.out_dir, "..", "class_names.json"), "w") as f:
        json.dump(class_names, f, indent=2)
    # Also drop a copy next to where model_loader.py expects it (ml/models/)
    os.makedirs("ml/models", exist_ok=True)
    with open("ml/models/class_names.json", "w") as f:
        json.dump(class_names, f, indent=2)

    with open(os.path.join(args.out_dir, "..", "split_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nDone. {len(class_names)} classes. class_names.json written to ml/models/")


if __name__ == "__main__":
    main()
