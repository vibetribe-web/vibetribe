-- Safe, additive indexes and constraints for VibeTribe.
-- Run in Supabase SQL Editor. This script does not drop tables or delete data.

-- Unique indexes backing required uniqueness. These fail only if duplicate data already exists.
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email);
CREATE UNIQUE INDEX IF NOT EXISTS ix_skills_name ON skills (name);
CREATE UNIQUE INDEX IF NOT EXISTS ix_clubs_name ON clubs (name);
CREATE UNIQUE INDEX IF NOT EXISTS ix_colleges_name ON colleges (name);
CREATE UNIQUE INDEX IF NOT EXISTS ix_branches_name ON branches (name);

-- Required performance indexes.
CREATE INDEX IF NOT EXISTS ix_clubs_is_active ON clubs (is_active);
CREATE INDEX IF NOT EXISTS ix_club_members_user_id ON club_members (user_id);
CREATE INDEX IF NOT EXISTS ix_club_members_role ON club_members (role);
CREATE INDEX IF NOT EXISTS ix_events_club_id ON events (club_id);
CREATE INDEX IF NOT EXISTS ix_events_created_by ON events (created_by);
CREATE INDEX IF NOT EXISTS ix_events_start_date ON events (start_date);
CREATE INDEX IF NOT EXISTS ix_teams_leader_id ON teams (leader_id);
CREATE INDEX IF NOT EXISTS ix_join_requests_team_status ON join_requests (team_id, status);
CREATE INDEX IF NOT EXISTS ix_join_requests_from_user_status ON join_requests (from_user_id, status);
CREATE INDEX IF NOT EXISTS ix_user_skills_skill_id ON user_skills (skill_id);
CREATE INDEX IF NOT EXISTS ix_team_required_skills_skill_id ON team_required_skills (skill_id);

-- Partial unique index: one pending request per user/team pair.
CREATE UNIQUE INDEX IF NOT EXISTS ux_pending_join_request
ON join_requests (from_user_id, team_id)
WHERE status = 'pending';

-- Business check constraints. NOT VALID avoids scanning/locking all existing rows immediately.
-- The DO blocks make these idempotent because PostgreSQL lacks ADD CONSTRAINT IF NOT EXISTS.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_teams_max_members_positive'
          AND conrelid = 'teams'::regclass
    ) THEN
        ALTER TABLE teams
        ADD CONSTRAINT ck_teams_max_members_positive
        CHECK (max_members > 0) NOT VALID;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_events_end_date_after_start_date'
          AND conrelid = 'events'::regclass
    ) THEN
        ALTER TABLE events
        ADD CONSTRAINT ck_events_end_date_after_start_date
        CHECK (end_date >= start_date) NOT VALID;
    END IF;
END $$;

-- Optional validation step. Run after confirming existing rows satisfy the checks.
-- ALTER TABLE teams VALIDATE CONSTRAINT ck_teams_max_members_positive;
-- ALTER TABLE events VALIDATE CONSTRAINT ck_events_end_date_after_start_date;

-- Verification: indexes.
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname IN (
      'ix_users_email',
      'ix_skills_name',
      'ix_clubs_name',
      'ix_colleges_name',
      'ix_branches_name',
      'ix_clubs_is_active',
      'ix_club_members_user_id',
      'ix_club_members_role',
      'ix_events_club_id',
      'ix_events_created_by',
      'ix_events_start_date',
      'ix_teams_leader_id',
      'ix_join_requests_team_status',
      'ix_join_requests_from_user_status',
      'ix_user_skills_skill_id',
      'ix_team_required_skills_skill_id',
      'ux_pending_join_request'
  )
ORDER BY tablename, indexname;

-- Verification: primary keys and check constraints.
SELECT
    conname,
    conrelid::regclass AS table_name,
    contype,
    pg_get_constraintdef(oid) AS definition,
    convalidated
FROM pg_constraint
WHERE conrelid::regclass::text IN (
    'users',
    'skills',
    'clubs',
    'colleges',
    'branches',
    'user_skills',
    'team_required_skills',
    'team_members',
    'club_members',
    'teams',
    'events'
)
  AND contype IN ('p', 'u', 'c')
ORDER BY table_name::text, conname;
