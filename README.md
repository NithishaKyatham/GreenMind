# GreenMind

## AI-Powered Crop Disease Detection and Recommendation System for Sustainable Development

**Status: Core system implemented and tested locally**

GreenMind is an AI-powered agriculture platform that combines computer vision, machine learning, and a FastAPI backend to detect crop diseases from plant images and provide relevant recommendations.

The system integrates a real **EfficientNet-B0** model trained on the **38-class PlantVillage dataset** into the live prediction pipeline. The core application flow includes registration, authentication, image upload, disease prediction, recommendations, prediction history, and PDF reporting.

> **Model performance:** The trained model achieves **99.61% accuracy on the held-out PlantVillage test set** (8,179 laboratory-captured images across 38 classes). This result should not be interpreted as real-world field accuracy; performance on natural farm photographs can be lower.

### Supported Scope

The current model recognizes **38 crop/disease combinations across 14 crops**:

Apple, Blueberry, Cherry, Corn, Grape, Orange, Peach, Bell Pepper, Potato, Raspberry, Soybean, Squash, Strawberry, and Tomato.

The system includes confidence handling for unsupported or uncertain images rather than presenting every prediction as a confirmed diagnosis.


## Architecture

```text
                    ┌──────────────────────┐
                    │      React + TS      │
                    │  Vite + Tailwind CSS │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      FastAPI API     │
                    │  REST + JWT Auth     │
                    └──────────┬───────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
      ┌────────────┐    ┌─────────────┐   ┌─────────────┐
      │ ML Inference│    │Recommendation│   │   Weather   │
      │ EfficientNet│    │    Engine    │   │   Service   │
      │    -B0      │    │  38 Classes  │   │ OpenWeather │
      └──────┬─────┘    └─────────────┘   └─────────────┘
             │
             ▼
      ┌──────────────┐
      │ Confidence    │
      │ Threshold     │
      └──────┬───────┘
             │
             ▼
      ┌──────────────┐
      │ PostgreSQL / │
      │    SQLite    │
      └──────────────┘
```

## ML Pipeline

```text
Plant Image
    ↓
Image Preprocessing
    ↓
224 × 224 Input
    ↓
EfficientNet-B0
    ↓
38-Class Prediction
    ↓
Confidence Check
    ├── High Confidence
    │       ↓
    │   Disease Result
    │       ↓
    │   Recommendation
    │
    └── Low Confidence
            ↓
        Safe Uncertain Response
```

