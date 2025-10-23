-- Table to store main Kaggle model info
CREATE TABLE kaggle_models (
    id SERIAL PRIMARY KEY,
    kaggle_url TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    scraped_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    downloads INT,
    usability NUMERIC(5,2),
    short_description TEXT,
    model_card TEXT,
    example_usage TEXT,
    last_scraped TIMESTAMP,
    total_views INT,
    total_engagements NUMERIC(10,5),
    -- Store activity overview as JSONB (e.g., last_scraped, total_downloads, total_views, total_engagements)
    activity_overview JSONB,

    model_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table to store tags (many-to-many relationship with models)
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE model_tags (
    model_id INT REFERENCES kaggle_models(id) ON DELETE CASCADE,
    tag_id INT REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (model_id, tag_id)
);

-- Table to store model variations
CREATE TABLE model_variations (
    id SERIAL PRIMARY KEY,
    model_id INT REFERENCES kaggle_models(id) ON DELETE CASCADE,
    variation TEXT NOT NULL,
    variation_name TEXT NOT NULL,
    variation_version TEXT,
    variation_created_by TEXT,
    variation_update_description TEXT,
    variation_license TEXT,
    variation_downloads INT,
    variations_model_card TEXT,
    variations_is_finetunable BOOLEAN,
    variations_example_usage TEXT
);

-- Table to store model metadata/collaborators
CREATE TABLE model_collaborators (
    id SERIAL PRIMARY KEY,
    model_id INT REFERENCES kaggle_models(id) ON DELETE CASCADE,
    collaborator_name TEXT NOT NULL,
    role TEXT
);

-- Indexes to speed up JSONB queries and common lookups
CREATE INDEX IF NOT EXISTS idx_kaggle_models_activity_overview ON kaggle_models USING GIN (activity_overview);
CREATE INDEX IF NOT EXISTS idx_kaggle_models_model_metadata ON kaggle_models USING GIN (model_metadata);
CREATE INDEX IF NOT EXISTS idx_kaggle_models_name ON kaggle_models (name);
