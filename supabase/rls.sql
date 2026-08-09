-- ═══════════════════════════════════════════════════════════════════════════
-- Solid RLS + real admin tier, both apps (maps_* and ohm_*).
-- Run in the Supabase SQL editor. Idempotent — safe to re-run.
--
-- Model:
--   anon (public visitors)  : may sign the gate via an RPC (no direct table
--                             writes), may insert telemetry, may read
--                             site_config. Can read NOTHING personal.
--   admin tier              : real Supabase Auth users (email OTP) whose
--                             email is in ttm_admins. Only they can read
--                             visitors/telemetry and write site_config.
--
-- This replaces the demo-grade policies, which had two real holes:
--   1) anon could SELECT visitors + telemetry (public email leak)
--   2) anon UPDATE on visitors could flip is_admin
-- ═══════════════════════════════════════════════════════════════════════════

-- ── admin registry ──────────────────────────────────────────────────────────
create table if not exists public.ttm_admins (
  email      text primary key,
  role       text not null default 'admin',   -- tier label: 'admin' | 'owner'
  added_at   timestamptz not null default now()
);
alter table public.ttm_admins enable row level security;

-- membership test for the signed-in Auth user (security definer so policies
-- can call it without granting table reads)
create or replace function public.is_ttm_admin()
returns boolean
language sql stable security definer
set search_path = public
as $$
  select exists (
    select 1 from public.ttm_admins a
    where lower(a.email) = lower(coalesce(auth.jwt()->>'email', ''))
  );
$$;
revoke all on function public.is_ttm_admin() from public;
grant execute on function public.is_ttm_admin() to authenticated, anon;

drop policy if exists "admins can read admin registry" on public.ttm_admins;
create policy "admins can read admin registry" on public.ttm_admins
  for select to authenticated using (public.is_ttm_admin());
-- no insert/update/delete policies: manage membership from the SQL editor only

-- ── gate sign-in RPCs (the ONLY write path anon has to the visitor tables) ──
create or replace function public.maps_gate_signin(p_name text, p_email text, p_user_agent text)
returns void
language plpgsql security definer
set search_path = public
as $$
begin
  if p_email !~ '^[^@\s]+@[^@\s]+\.[^@\s]+$' or length(p_email) > 200
     or coalesce(length(p_name), 0) not between 1 and 120 then
    raise exception 'invalid gate input';
  end if;
  insert into public.maps_visitors (name, email, user_agent)
  values (p_name, lower(p_email), left(p_user_agent, 250))
  on conflict (email) do update
    set name = excluded.name, last_seen = now(), user_agent = excluded.user_agent;
end;
$$;

create or replace function public.ohm_gate_signin(p_name text, p_email text, p_user_agent text)
returns void
language plpgsql security definer
set search_path = public
as $$
begin
  if p_email !~ '^[^@\s]+@[^@\s]+\.[^@\s]+$' or length(p_email) > 200
     or coalesce(length(p_name), 0) not between 1 and 120 then
    raise exception 'invalid gate input';
  end if;
  insert into public.ohm_visitors (name, email, user_agent)
  values (p_name, lower(p_email), left(p_user_agent, 250))
  on conflict (email) do update
    set name = excluded.name, last_seen = now(), user_agent = excluded.user_agent;
end;
$$;

revoke all on function public.maps_gate_signin(text, text, text) from public;
revoke all on function public.ohm_gate_signin(text, text, text) from public;
grant execute on function public.maps_gate_signin(text, text, text) to anon, authenticated;
grant execute on function public.ohm_gate_signin(text, text, text) to anon, authenticated;

-- ── visitors: drop every anon policy; admin-only reads; no direct writes ────
alter table public.maps_visitors enable row level security;
alter table public.ohm_visitors  enable row level security;

drop policy if exists "anon can insert visitors" on public.maps_visitors;
drop policy if exists "anon can update own visitor row" on public.maps_visitors;
drop policy if exists "anon can read visitors (demo)" on public.maps_visitors;
drop policy if exists "admins can read visitors" on public.maps_visitors;
create policy "admins can read visitors" on public.maps_visitors
  for select to authenticated using (public.is_ttm_admin());

drop policy if exists "anon can insert ohm visitors" on public.ohm_visitors;
drop policy if exists "anon can update own ohm visitor row" on public.ohm_visitors;
drop policy if exists "anon can read ohm visitors (demo)" on public.ohm_visitors;
drop policy if exists "admins can read ohm visitors" on public.ohm_visitors;
create policy "admins can read ohm visitors" on public.ohm_visitors
  for select to authenticated using (public.is_ttm_admin());

-- ── telemetry: anon may INSERT only; admin-only reads ───────────────────────
alter table public.maps_telemetry_events enable row level security;
alter table public.ohm_telemetry_events  enable row level security;

drop policy if exists "anon can insert telemetry" on public.maps_telemetry_events;
create policy "anon can insert telemetry" on public.maps_telemetry_events
  for insert to anon, authenticated with check (true);
drop policy if exists "anon can read telemetry (demo)" on public.maps_telemetry_events;
drop policy if exists "admins can read telemetry" on public.maps_telemetry_events;
create policy "admins can read telemetry" on public.maps_telemetry_events
  for select to authenticated using (public.is_ttm_admin());

drop policy if exists "anon can insert ohm telemetry" on public.ohm_telemetry_events;
create policy "anon can insert ohm telemetry" on public.ohm_telemetry_events
  for insert to anon, authenticated with check (true);
drop policy if exists "anon can read ohm telemetry (demo)" on public.ohm_telemetry_events;
drop policy if exists "admins can read ohm telemetry" on public.ohm_telemetry_events;
create policy "admins can read ohm telemetry" on public.ohm_telemetry_events
  for select to authenticated using (public.is_ttm_admin());

-- ── site_config (whitelabel): world-readable, admin-writable ────────────────
do $$
begin
  if to_regclass('public.maps_site_config') is not null then
    alter table public.maps_site_config enable row level security;
    drop policy if exists "anon can read site config" on public.maps_site_config;
    create policy "anon can read site config" on public.maps_site_config
      for select to anon, authenticated using (true);
    drop policy if exists "anon can upsert site config" on public.maps_site_config;
    drop policy if exists "anon can update site config" on public.maps_site_config;
    drop policy if exists "anon can insert site config" on public.maps_site_config;
    drop policy if exists "admins can insert site config" on public.maps_site_config;
    create policy "admins can insert site config" on public.maps_site_config
      for insert to authenticated with check (public.is_ttm_admin());
    drop policy if exists "admins can update site config" on public.maps_site_config;
    create policy "admins can update site config" on public.maps_site_config
      for update to authenticated
      using (public.is_ttm_admin()) with check (public.is_ttm_admin());
  end if;
end $$;

-- ── enroll yourself in the admin tier ───────────────────────────────────────
insert into public.ttm_admins (email, role) values ('sonia@thetechmargin.com', 'owner')
  on conflict (email) do update set role = 'owner';

-- ═══ One-time dashboard setting (not SQL): Authentication → Providers →
-- Email must be enabled (it is by default). Admins sign into /admin/ with a
-- 6-digit email code; no password, no signup flow needed. ═══

-- ── residual honest caveats ─────────────────────────────────────────────────
-- * telemetry INSERT is open to anon by design (it's client telemetry);
--   visitor_email inside an event is client-claimed, not verified.
-- * the gate RPC rate-limits nothing; Supabase's global rate limits apply.
