"""
Standalone CLI for testing the trained model on a single image, independent
of the backend — useful for quick sanity checks during development.

Usage:
    python ml/inference/predict.py --image path/to/leaf.jpg --model_path ml/models/crop_disease_model.pt
"""
import argparse
import json
import os
import sys

import torch
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "training"))
from model_utils import build_model, get_transforms  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--model_path", default="ml/models/crop_disease_model.pt")
    parser.add_argument("--class_names_path", default="ml/models/class_names.json")
    parser.add_argument("--arch", default="efficientnet_b0")
    parser.add_argument("--input_size", type=int, default=224)
    args = parser.parse_args()

    with open(args.class_names_path) as f:
        class_names = json.load(f)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model(args.arch, num_classes=len(class_names)).to(device)
    model.load_state_dict(torch.load(args.model_path, map_location=device))
    model.eval()

    _, eval_tf = get_transforms(args.input_size)
    img = Image.open(args.image).convert("RGB")
    tensor = eval_tf(img).unsqueeze(0).to(device)

    with torch.no_grad():
        probs = torch.softmax(model(tensor), dim=1)[0]
        top_idx = int(torch.argmax(probs).item())

    print(f"Predicted class: {class_names[top_idx]}")
    print(f"Confidence: {probs[top_idx].item():.4f}")


if __name__ == "__main__":
    main()
