"""
Trains the crop-disease classifier via transfer learning.

Usage:
    python ml/training/train.py --data_dir ml/dataset/processed --epochs 15 --arch efficientnet_b0

Outputs:
    ml/models/crop_disease_model.pt   (state_dict, loadable by the backend)
    ml/models/class_names.json        (already written by prepare_dataset.py)
    ml/models/training_log.json       (loss/accuracy per epoch, for the report)
"""
import argparse
import json
import os

import torch
from torch import nn, optim
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder

from model_utils import build_model, get_transforms


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", default="ml/dataset/processed")
    parser.add_argument("--out_dir", default="ml/models")
    parser.add_argument("--arch", default="efficientnet_b0",
                         choices=["efficientnet_b0", "mobilenet_v3", "resnet18"])
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--input_size", type=int, default=224)
    parser.add_argument("--patience", type=int, default=4, help="Early stopping patience (epochs)")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    train_tf, eval_tf = get_transforms(args.input_size)

    train_ds = ImageFolder(os.path.join(args.data_dir, "train"), transform=train_tf)
    val_ds = ImageFolder(os.path.join(args.data_dir, "val"), transform=eval_tf)

    class_names = train_ds.classes
    if val_ds.classes != class_names:
        raise SystemExit("Train/val class folders don't match — re-run prepare_dataset.py")

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=0)

    model = build_model(args.arch, num_classes=len(class_names)).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=2)

    best_val_loss = float("inf")
    epochs_no_improve = 0
    os.makedirs(args.out_dir, exist_ok=True)
    log = []

    for epoch in range(1, args.epochs + 1):
        model.train()
        train_loss, train_correct, train_total = 0.0, 0, 0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * images.size(0)
            train_correct += (outputs.argmax(1) == labels).sum().item()
            train_total += labels.size(0)

        model.eval()
        val_loss, val_correct, val_total = 0.0, 0, 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * images.size(0)
                val_correct += (outputs.argmax(1) == labels).sum().item()
                val_total += labels.size(0)

        train_loss /= max(train_total, 1)
        val_loss /= max(val_total, 1)
        train_acc = train_correct / max(train_total, 1)
        val_acc = val_correct / max(val_total, 1)
        scheduler.step(val_loss)

        print(f"Epoch {epoch}/{args.epochs} | train_loss={train_loss:.4f} train_acc={train_acc:.4f} "
              f"| val_loss={val_loss:.4f} val_acc={val_acc:.4f}")
        log.append({"epoch": epoch, "train_loss": train_loss, "train_acc": train_acc,
                     "val_loss": val_loss, "val_acc": val_acc})

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            epochs_no_improve = 0
            torch.save(model.state_dict(), os.path.join(args.out_dir, "crop_disease_model.pt"))
            print(f"  -> New best model saved (val_loss={val_loss:.4f})")
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= args.patience:
                print(f"Early stopping at epoch {epoch} (no improvement for {args.patience} epochs)")
                break

    with open(os.path.join(args.out_dir, "training_log.json"), "w") as f:
        json.dump(log, f, indent=2)

    print("\nTraining complete. Best model + class_names.json are in ml/models/.")
    print("Run evaluate.py next to get real test-set accuracy/precision/recall/F1 for your report.")


if __name__ == "__main__":
    main()
