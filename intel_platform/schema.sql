BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE tenant (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    country_code CHAR(2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE app_user (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    username TEXT NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT,
    password_hash TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, username)
);

CREATE TABLE role (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    UNIQUE (tenant_id, name)
);

CREATE TABLE permission (
    code TEXT PRIMARY KEY,
    description TEXT NOT NULL
);

CREATE TABLE role_permission (
    role_id UUID NOT NULL REFERENCES role(id) ON DELETE CASCADE,
    permission_code TEXT NOT NULL REFERENCES permission(code) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_code)
);

CREATE TABLE user_role (
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES role(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE case_file (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    status TEXT NOT NULL CHECK (status IN ('open', 'under_review', 'closed', 'archived')),
    classification TEXT NOT NULL CHECK (classification IN ('restricted', 'confidential', 'secret')),
    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    created_by UUID NOT NULL REFERENCES app_user(id),
    UNIQUE (tenant_id, code)
);

CREATE TABLE case_access (
    case_id UUID NOT NULL REFERENCES case_file(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    access_level TEXT NOT NULL CHECK (access_level IN ('viewer', 'editor', 'commander')),
    granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (case_id, user_id)
);

CREATE TABLE person_entity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    given_names TEXT NOT NULL,
    family_names TEXT NOT NULL,
    date_of_birth DATE,
    document_number TEXT,
    nationality TEXT,
    risk_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, document_number)
);

CREATE TABLE organization_entity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    legal_name TEXT NOT NULL,
    trade_name TEXT,
    registry_number TEXT,
    country_code CHAR(2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, registry_number)
);

CREATE TABLE asset (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    asset_type TEXT NOT NULL CHECK (asset_type IN ('vehicle', 'property', 'account', 'device', 'other')),
    label TEXT NOT NULL,
    serial_number TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE lead (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    case_id UUID REFERENCES case_file(id) ON DELETE SET NULL,
    source_type TEXT NOT NULL CHECK (source_type IN ('human', 'document', 'open_source', 'judicial', 'internal')),
    reliability_rating SMALLINT NOT NULL CHECK (reliability_rating BETWEEN 1 AND 5),
    confidence_rating SMALLINT NOT NULL CHECK (confidence_rating BETWEEN 1 AND 5),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES app_user(id)
);

CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    case_id UUID NOT NULL REFERENCES case_file(id) ON DELETE CASCADE,
    evidence_type TEXT NOT NULL CHECK (evidence_type IN ('document', 'image', 'video', 'audio', 'device_dump', 'report', 'other')),
    title TEXT NOT NULL,
    storage_uri TEXT NOT NULL,
    sha256 TEXT,
    chain_of_custody JSONB NOT NULL DEFAULT '[]'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES app_user(id)
);

CREATE TABLE entity_link (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    source_kind TEXT NOT NULL CHECK (source_kind IN ('person', 'organization', 'asset', 'lead', 'case')),
    source_id UUID NOT NULL,
    target_kind TEXT NOT NULL CHECK (target_kind IN ('person', 'organization', 'asset', 'lead', 'case')),
    target_id UUID NOT NULL,
    relationship_type TEXT NOT NULL,
    confidence_rating SMALLINT NOT NULL CHECK (confidence_rating BETWEEN 1 AND 5),
    explanation TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES app_user(id)
);

CREATE TABLE case_note (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES case_file(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES app_user(id),
    body TEXT NOT NULL,
    note_type TEXT NOT NULL CHECK (note_type IN ('analysis', 'briefing', 'decision', 'task', 'summary')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE task_item (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES case_file(id) ON DELETE CASCADE,
    assigned_to UUID REFERENCES app_user(id),
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT NOT NULL CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    status TEXT NOT NULL CHECK (status IN ('todo', 'doing', 'blocked', 'done')),
    due_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE ai_model (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    provider TEXT NOT NULL CHECK (provider IN ('ollama', 'vllm', 'llama_cpp', 'custom')),
    endpoint TEXT NOT NULL,
    context_window INTEGER,
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE ai_job (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    case_id UUID REFERENCES case_file(id) ON DELETE SET NULL,
    requested_by UUID NOT NULL REFERENCES app_user(id),
    model_id UUID NOT NULL REFERENCES ai_model(id),
    job_type TEXT NOT NULL CHECK (job_type IN ('summarization', 'timeline', 'link_suggestion', 'translation', 'report_draft')),
    prompt TEXT NOT NULL,
    response TEXT,
    status TEXT NOT NULL CHECK (status IN ('queued', 'running', 'completed', 'failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE retention_policy (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    record_type TEXT NOT NULL,
    retention_days INTEGER NOT NULL CHECK (retention_days > 0),
    legal_basis TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, record_type)
);

CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    actor_user_id UUID REFERENCES app_user(id),
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    details JSONB NOT NULL DEFAULT '{}'::JSONB,
    ip_address INET,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_case_file_tenant_status ON case_file (tenant_id, status);
CREATE INDEX idx_case_access_user ON case_access (user_id);
CREATE INDEX idx_person_entity_name ON person_entity (tenant_id, family_names, given_names);
CREATE INDEX idx_lead_case_time ON lead (case_id, captured_at DESC);
CREATE INDEX idx_evidence_case_time ON evidence (case_id, created_at DESC);
CREATE INDEX idx_entity_link_source ON entity_link (source_kind, source_id);
CREATE INDEX idx_entity_link_target ON entity_link (target_kind, target_id);
CREATE INDEX idx_audit_log_tenant_time ON audit_log (tenant_id, created_at DESC);

INSERT INTO permission (code, description) VALUES
    ('case.read', 'Ver expedientes autorizados'),
    ('case.write', 'Editar expedientes autorizados'),
    ('evidence.write', 'Agregar evidencia y custodias'),
    ('lead.write', 'Registrar leads y notas'),
    ('admin.users', 'Administrar usuarios y roles'),
    ('ai.run', 'Ejecutar tareas de IA local')
ON CONFLICT (code) DO NOTHING;

COMMIT;
