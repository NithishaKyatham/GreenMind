-- GreenMind — reference PostgreSQL schema.
-- This is documentation of the schema SQLAlchemy models produce; the
-- actual tables are created via SQLAlchemy (dev) or Alembic (production).
-- Kept here so a reviewer can read the schema without running the app.

CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    preferred_language VARCHAR(10) NOT NULL DEFAULT 'en',
    location VARCHAR(255),
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE crops (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name_en VARCHAR(100) NOT NULL,
    display_name_te VARCHAR(100),
    display_name_hi VARCHAR(100)
);

CREATE TABLE disease_predictions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    crop VARCHAR(100) NOT NULL,
    image_path VARCHAR(500) NOT NULL,
    disease VARCHAR(150) NOT NULL,
    confidence FLOAT NOT NULL,
    severity VARCHAR(20) NOT NULL,
    is_fallback_prediction BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_predictions_user_id ON disease_predictions(user_id);
CREATE INDEX idx_predictions_created_at ON disease_predictions(created_at);

CREATE TABLE recommendations (
    id VARCHAR(36) PRIMARY KEY,
    prediction_id VARCHAR(36) UNIQUE NOT NULL REFERENCES disease_predictions(id),
    treatment TEXT NOT NULL,
    fertilizer TEXT,
    pesticide_guidance TEXT,
    prevention TEXT,
    crop_management TEXT,
    monitoring_advice TEXT
);

CREATE TABLE weather_records (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id),
    location VARCHAR(255) NOT NULL,
    temperature FLOAT,
    humidity FLOAT,
    rainfall FLOAT,
    condition VARCHAR(100),
    forecast_json TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_weather_user_id ON weather_records(user_id);

CREATE TABLE chat_messages (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    conversation_id VARCHAR(36) NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_chat_user_id ON chat_messages(user_id);
CREATE INDEX idx_chat_conversation_id ON chat_messages(conversation_id);

CREATE TABLE reports (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    prediction_id VARCHAR(36) NOT NULL REFERENCES disease_predictions(id),
    file_path VARCHAR(500) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_reports_user_id ON reports(user_id);
