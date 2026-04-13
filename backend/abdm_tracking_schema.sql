-- Optional ABDM correlation table for the HIU webhook flow.
-- Create this in Supabase if you want consent and health-data callbacks to
-- survive restarts instead of relying only on the in-memory cache.

create table if not exists public.abdm_consent_requests (
    abha_id text primary key,
    consent_request_id text,
    consent_artifact_id text,
    health_request_id text,
    consent_status text,
    created_at timestamptz not null default now()
);

create index if not exists abdm_consent_requests_consent_artifact_id_idx
    on public.abdm_consent_requests (consent_artifact_id);

create index if not exists abdm_consent_requests_health_request_id_idx
    on public.abdm_consent_requests (health_request_id);

-- Stateless ABDM session table used by the cryptographic HIU flow.
-- transaction_id is the lookup key used by the health-data webhook.
create table if not exists public.abdm_sessions (
    transaction_id text primary key,
    consent_request_id text,
    consent_artifact_id text,
    abha_id text,
    callback_base_url text,
    health_request_id text,
    private_key_hex text,
    nonce_hex text,
    status text not null default 'PENDING',
    error_message text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists abdm_sessions_consent_artifact_id_idx
    on public.abdm_sessions (consent_artifact_id);

create index if not exists abdm_sessions_consent_request_id_idx
    on public.abdm_sessions (consent_request_id);

create index if not exists abdm_sessions_health_request_id_idx
    on public.abdm_sessions (health_request_id);

create index if not exists abdm_sessions_status_idx
    on public.abdm_sessions (status);