-- Run this in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    salary TEXT,
    job_type TEXT,
    description TEXT,
    url TEXT UNIQUE NOT NULL,
    source TEXT,
    match_score INTEGER,
    match_reasons JSONB,
    status TEXT DEFAULT 'pending_approval',
    telegram_message_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    applied_at TIMESTAMPTZ,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES jobs(id),
    job_title TEXT NOT NULL,
    company TEXT NOT NULL,
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    confirmation_email TEXT,
    status TEXT DEFAULT 'submitted',
    notes TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_url ON jobs(url);
CREATE INDEX IF NOT EXISTS idx_jobs_telegram_msg ON jobs(telegram_message_id);
CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications(job_id);
