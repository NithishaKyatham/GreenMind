"""
Shared model construction utilities for training and inference.
Must match app/ml/model_loader.py's architecture choices exactly, so a
model trained here loads correctly in the backend.
"""
import torch
import torch.nn as nn
import torchvision.models as tvm


def build_model(architecture: str, num_classes: int) -> nn.Module:
    if architecture == "efficientnet_b0":
        model = tvm.efficientnet_b0(weights=tvm.EfficientNet_B0_Weights.IMAGENET1K_V1)
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)
    elif architecture == "mobilenet_v3":
        model = tvm.mobilenet_v3_small(weights=tvm.MobileNet_V3_Small_Weights.IMAGENET1K_V1)
        model.classifier[3] = nn.Linear(model.classifier[3].in_features, num_classes)
    elif architecture == "resnet18":
        model = tvm.resnet18(weights=tvm.ResNet18_Weights.IMAGENET1K_V1)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
    else:
        raise ValueError(f"Unknown architecture: {architecture}")
    return model


def get_transforms(input_size: int = 224):
    from torchvision import transforms as T

    normalize = T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])

    train_transform = T.Compose([
        T.RandomResizedCrop(input_size, scale=(0.8, 1.0)),
        T.RandomHorizontalFlip(),
        T.RandomRotation(15),
        T.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        T.ToTensor(),
        normalize,
    ])
    eval_transform = T.Compose([
        T.Resize((input_size, input_size)),
        T.ToTensor(),
        normalize,
    ])
    return train_transform, eval_transform
