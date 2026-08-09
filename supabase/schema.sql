-- TTM stack schema for Maps of Making (run in the Supabase SQL editor).
-- Two tables: gate sign-ins and telemetry events. RLS is enabled with
-- DEMO-GRADE policies: the anon key may INSERT both tables and SELECT them
-- (the /admin/ dashboard reads with the anon key). Before real traffic,
-- tighten the SELECT policies to an authenticated admin role.

create table if not exists public.visitors (
  id          bigint generated always as identity primary key,
  email       text not null unique,
  name        text not null,
  first_seen  timestamptz not null default now(),
  last_seen   timestamptz not null default now(),
  user_agent  text
);

create table if not exists public.telemetry_events (
  id          bigint generated always as identity primary key,
  event       text not null,
  props       jsonb not null default '{}'::jsonb,
  session_id  text,
  page        text,
  visitor_email text,
  ts          timestamptz not null default now()
);
create index if not exists telemetry_events_ts_idx on public.telemetry_events (ts desc);
create index if not exists telemetry_events_event_idx on public.telemetry_events (event);

alter table public.visitors enable row level security;
alter table public.telemetry_events enable row level security;

-- Gate writes (anon)
create policy "anon can insert visitors" on public.visitors
  for insert to anon with check (true);
create policy "anon can update own visitor row" on public.visitors
  for update to anon using (true) with check (true);
create policy "anon can insert telemetry" on public.telemetry_events
  for insert to anon with check (true);

-- Admin dashboard reads (DEMO: anon; tighten before real traffic)
create policy "anon can read visitors (demo)" on public.visitors
  for select to anon using (true);
create policy "anon can read telemetry (demo)" on public.telemetry_events
  for select to anon using (true);
