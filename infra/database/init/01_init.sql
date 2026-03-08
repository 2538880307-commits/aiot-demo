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

CREATE TABLE IF NOT EXISTS tools (
    id BIGSERIAL PRIMARY KEY,
    tool_code VARCHAR(64) NOT NULL UNIQUE,
    tool_type VARCHAR(64) NOT NULL,
    tool_name VARCHAR(128) NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    team VARCHAR(128) NOT NULL,
    image_url TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(64) NOT NULL UNIQUE,
    employee_no VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(64) NOT NULL,
    department VARCHAR(128) NOT NULL,
    position VARCHAR(128) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'employee',
    permissions JSONB NOT NULL DEFAULT '[]'::jsonb
);

CREATE TABLE IF NOT EXISTS system_settings (
    id BIGSERIAL PRIMARY KEY,
    setting_key VARCHAR(64) NOT NULL UNIQUE,
    setting_value JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_by VARCHAR(64) NOT NULL DEFAULT 'system',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tool_types (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(64) NOT NULL UNIQUE,
    description VARCHAR(256) NOT NULL DEFAULT '',
    sort_order INTEGER NOT NULL DEFAULT 100,
    enabled BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS operation_logs (
    id BIGSERIAL PRIMARY KEY,
    module VARCHAR(64) NOT NULL,
    action VARCHAR(64) NOT NULL,
    actor VARCHAR(64) NOT NULL,
    target VARCHAR(128) NOT NULL DEFAULT '',
    detail_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_detection_logs_site_time
    ON detection_logs (site_code, event_time DESC);
CREATE INDEX IF NOT EXISTS idx_detection_logs_result_json
    ON detection_logs USING GIN (result_json);
CREATE INDEX IF NOT EXISTS idx_alert_logs_site_time
    ON alert_logs (site_code, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tools_code ON tools (tool_code);
CREATE INDEX IF NOT EXISTS idx_tools_type ON tools (tool_type);
CREATE INDEX IF NOT EXISTS idx_tools_name ON tools (tool_name);
CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);
CREATE INDEX IF NOT EXISTS idx_users_employee_no ON users (employee_no);
CREATE INDEX IF NOT EXISTS idx_operation_logs_module ON operation_logs (module);
CREATE INDEX IF NOT EXISTS idx_operation_logs_actor ON operation_logs (actor);
CREATE INDEX IF NOT EXISTS idx_operation_logs_time ON operation_logs (timestamp DESC);

INSERT INTO tool_types (name, description, sort_order, enabled)
VALUES
    ('电动工具', '电驱动类工具', 10, TRUE),
    ('手动工具', '人工操作类工具', 20, TRUE),
    ('测量工具', '测量检测类工具', 30, TRUE),
    ('安全设备', '安全防护设备', 40, TRUE)
ON CONFLICT (name) DO NOTHING;

INSERT INTO tools (tool_code, tool_type, tool_name, stock, team, image_url)
VALUES
    ('01001', '电动工具', '冲击电钻', 6, '维修一组', ''),
    ('09010', '手动工具', '手动扳手', 34, '维修一组', ''),
    ('07003', '手动工具', '套筒扳手', 21, '维修一组', ''),
    ('09006', '手动工具', '手动螺丝刀', 16, '维修二组', ''),
    ('07012', '电动工具', '电动角磨机', 4, '维修二组', ''),
    ('09003', '手动工具', '手动钢丝钳', 13, '维修一组', '')
ON CONFLICT (tool_code) DO NOTHING;

INSERT INTO users (username, employee_no, name, department, position, role, permissions)
VALUES
    ('admin', 'A0001', '系统管理员', '信息中心', '系统管理员', 'admin', '["工具管理","权限管理","系统设置"]'::jsonb),
    ('operator', 'E0001', '现场值班员', '车辆检修部', '检修员', 'employee', '["工具管理"]'::jsonb)
ON CONFLICT (username) DO NOTHING;

INSERT INTO system_settings (setting_key, setting_value, updated_by)
VALUES
    ('password_policy', '{"min_length":8,"require_uppercase":true,"require_lowercase":true,"require_number":true,"require_special":false,"session_timeout_minutes":120,"max_login_retries":5}'::jsonb, 'system'),
    ('alert_threshold', '{"low_stock_threshold":5,"detection_confidence_threshold":0.8,"alert_dedup_seconds":60}'::jsonb, 'system')
ON CONFLICT (setting_key) DO NOTHING;
