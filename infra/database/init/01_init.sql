CREATE TABLE IF NOT EXISTS detection_logs (
    id BIGSERIAL PRIMARY KEY,
    site_code VARCHAR(64) NOT NULL,
    event_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    result_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS alert_logs (
    id BIGSERIAL PRIMARY KEY,
    site_code VARCHAR(64) NOT NULL,
    alert_type VARCHAR(64) NOT NULL,
    alert_level VARCHAR(32) NOT NULL,
    detail_json JSONB NOT NULL,
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_detection_logs_site_time
    ON detection_logs (site_code, event_time DESC);

CREATE INDEX IF NOT EXISTS idx_detection_logs_result_json
    ON detection_logs USING GIN (result_json);

CREATE INDEX IF NOT EXISTS idx_alert_logs_site_time
    ON alert_logs (site_code, created_at DESC);
