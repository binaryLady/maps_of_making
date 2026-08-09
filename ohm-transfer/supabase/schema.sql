-- TTM stack schema for the OHM dashboard (run in the Supabase SQL editor).
-- Shares the same database as other TTM sites — tables are prefixed ohm_.
-- Two tables: gate sign-ins and telemetry events. RLS is enabled with
-- DEMO-GRADE policies: the anon key may INSERT both tables and SELECT them.
-- Before real traffic, tighten the SELECT policies to an authenticated role.

create table if not exists public.ohm_visitors (
  id          bigint generated always as identity primary key,
  email       text not null unique,
  name        text not null,
  first_seen  timestamptz not null default now(),
  last_seen   timestamptz not null default now(),
  user_agent  text,
  is_admin    boolean not null default false
);
-- If the table pre-dates the is_admin column, this brings it up to date:
alter table public.ohm_visitors
  add column if not exists is_admin boolean not null default false;
-- Grant admin (the /admin/ area only renders for these visitors):
--   update public.ohm_visitors set is_admin = true where email = 'you@example.com';

create table if not exists public.ohm_telemetry_events (
  id          bigint generated always as identity primary key,
  event       text not null,
  props       jsonb not null default '{}'::jsonb,
  session_id  text,
  page        text,
  visitor_email text,
  ts          timestamptz not null default now()
);
create index if not exists ohm_telemetry_events_ts_idx on public.ohm_telemetry_events (ts desc);
create index if not exists ohm_telemetry_events_event_idx on public.ohm_telemetry_events (event);

alter table public.ohm_visitors enable row level security;
alter table public.ohm_telemetry_events enable row level security;

-- Gate writes (anon)
create policy "anon can insert ohm visitors" on public.ohm_visitors
  for insert to anon with check (true);
create policy "anon can update own ohm visitor row" on public.ohm_visitors
  for update to anon using (true) with check (true);
create policy "anon can insert ohm telemetry" on public.ohm_telemetry_events
  for insert to anon with check (true);

-- Dashboard reads (DEMO: anon; tighten before real traffic)
create policy "anon can read ohm visitors (demo)" on public.ohm_visitors
  for select to anon using (true);
create policy "anon can read ohm telemetry (demo)" on public.ohm_telemetry_events
  for select to anon using (true);
