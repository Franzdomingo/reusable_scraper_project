CREATE TABLE models (
    model_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    kaggle_url TEXT,
    short_description TEXT,
    downloads INTEGER,
    usability NUMERIC(4,2),
    model_card TEXT
);

CREATE TABLE model_tags (
    tag_id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES models(model_id) ON DELETE CASCADE,
    tag TEXT NOT NULL
);

CREATE TABLE model_activity_overview (
    activity_id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES models(model_id) ON DELETE CASCADE,
    last_scraped TIMESTAMPTZ,
    total_downloads INTEGER,
    total_views INTEGER,
    total_engagements NUMERIC(8,5)
);

CREATE TABLE model_variations (
    variation_id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES models(model_id) ON DELETE CASCADE,
    variation TEXT,
    variation_name TEXT,
    variation_version TEXT,
    variation_created_by TEXT,
    variation_update_description TEXT,
    variation_license TEXT,
    variation_base_model TEXT,
    variation_downloads INTEGER,
    variations_model_card TEXT,
    variations_is_finetunable BOOLEAN,
    variations_example_usage TEXT
);

CREATE TABLE model_metadata (
    metadata_id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES models(model_id) ON DELETE CASCADE,
    provenance TEXT,
    provenance_updates TEXT,
    auto_syncing BOOLEAN DEFAULT FALSE,
    citations TEXT
);

CREATE TABLE model_collaborators (
    collaborator_id SERIAL PRIMARY KEY,
    metadata_id INTEGER REFERENCES model_metadata(metadata_id) ON DELETE CASCADE,
    name TEXT,
    role TEXT
);
