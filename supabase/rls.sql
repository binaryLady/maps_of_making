-- ═══════════════════════════════════════════════════════════════════════════
-- RLS v2 — member/super-admin tiers, both apps (maps_* and ohm_*).
-- Run in the Supabase SQL editor. Idempotent — safe to re-run.
--
-- Tiers:
--   anon           : pre-gate visitors. May insert telemetry and read
--                    site_config. Read NOTHING personal, write nothing else.
--   admin (member) : the gate itself is instant (name + email, no code).
--                    Member powers — READ everything, CRUD own visitor row —
--                    require the OTP sign-in at /admin/ (Supabase Auth), so
--                    they attach to a verified email.
--   super admin    : emails enrolled in ttm_admins (ecosystem protection).
--                    Full CRUD on all our tables, sole writer of site_config.
--
-- Identity note: the member tier is real Auth identity, so "own row" is the
-- row matching the signed-in JWT email — not a client-claimed string.
-- ═══════════════════════════════════════════════════════════════════════════

-- ── super-admin registry ────────────────────────────────────────────────────
create table if not exists public.ttm_admins (
  email      text primary key,
  role       text not null default 'super',
  added_at   timestamptz not null default now()
);
alter table public.ttm_admins enable row level security;

create or replace function public.ttm_is_super()
returns boolean
language sql stable security definer
set search_path = public
as $$
  select exists (
    select 1 from public.ttm_admins a
    where lower(a.email) = lower(coalesce(auth.jwt()->>'email', ''))
  );
$$;
revoke all on function public.ttm_is_super() from public;
grant execute on function public.ttm_is_super() to authenticated, anon;

-- convenience: the signed-in member's email, lowercased
create or replace function public.ttm_jwt_email()
returns text
language sql stable
as $$ select lower(coalesce(auth.jwt()->>'email', '')) $$;
grant execute on function public.ttm_jwt_email() to authenticated, anon;

drop policy if exists "admins can read admin registry" on public.ttm_admins;
drop policy if exists "supers manage admin registry" on public.ttm_admins;
create policy "supers manage admin registry" on public.ttm_admins
  for all to authenticated
  using (public.ttm_is_super()) with check (public.ttm_is_super());

-- ── gate sign-in RPCs ───────────────────────────────────────────────────────
-- The gate is deliberately frictionless (name + email, no code), so this RPC
-- is anon-callable and the email is visitor-claimed. Verified identity lives
-- at the /admin/ door (OTP) — visitor rows are directory data, not authority.
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

drop function if exists public.maps_gate_signin(text, text);
drop function if exists public.ohm_gate_signin(text, text);
revoke all on function public.maps_gate_signin(text, text, text) from public;
revoke all on function public.ohm_gate_signin(text, text, text) from public;
grant execute on function public.maps_gate_signin(text, text, text) to anon, authenticated;
grant execute on function public.ohm_gate_signin(text, text, text) to anon, authenticated;

-- ── visitors: members read all, CRUD own row; supers CRUD all ───────────────
alter table public.maps_visitors enable row level security;
alter table public.ohm_visitors  enable row level security;

-- retire every earlier policy generation
drop policy if exists "anon can insert visitors" on public.maps_visitors;
drop policy if exists "anon can update own visitor row" on public.maps_visitors;
drop policy if exists "anon can read visitors (demo)" on public.maps_visitors;
drop policy if exists "admins can read visitors" on public.maps_visitors;
drop policy if exists "members read visitors" on public.maps_visitors;
create policy "members read visitors" on public.maps_visitors
  for select to authenticated using (true);
drop policy if exists "members update own row" on public.maps_visitors;
create policy "members update own row" on public.maps_visitors
  for update to authenticated
  using (lower(email) = public.ttm_jwt_email())
  with check (lower(email) = public.ttm_jwt_email());
drop policy if exists "members delete own row" on public.maps_visitors;
create policy "members delete own row" on public.maps_visitors
  for delete to authenticated using (lower(email) = public.ttm_jwt_email());
drop policy if exists "supers full access visitors" on public.maps_visitors;
create policy "supers full access visitors" on public.maps_visitors
  for all to authenticated
  using (public.ttm_is_super()) with check (public.ttm_is_super());

drop policy if exists "anon can insert ohm visitors" on public.ohm_visitors;
drop policy if exists "anon can update own ohm visitor row" on public.ohm_visitors;
drop policy if exists "anon can read ohm visitors (demo)" on public.ohm_visitors;
drop policy if exists "admins can read ohm visitors" on public.ohm_visitors;
drop policy if exists "members read ohm visitors" on public.ohm_visitors;
create policy "members read ohm visitors" on public.ohm_visitors
  for select to authenticated using (true);
drop policy if exists "members update own ohm row" on public.ohm_visitors;
create policy "members update own ohm row" on public.ohm_visitors
  for update to authenticated
  using (lower(email) = public.ttm_jwt_email())
  with check (lower(email) = public.ttm_jwt_email());
drop policy if exists "members delete own ohm row" on public.ohm_visitors;
create policy "members delete own ohm row" on public.ohm_visitors
  for delete to authenticated using (lower(email) = public.ttm_jwt_email());
drop policy if exists "supers full access ohm visitors" on public.ohm_visitors;
create policy "supers full access ohm visitors" on public.ohm_visitors
  for all to authenticated
  using (public.ttm_is_super()) with check (public.ttm_is_super());

-- ecosystem protection: nobody but a super can grant the legacy is_admin flag
-- (column is display-only now; a member updating their own row must not be
-- able to flip it)
create or replace function public.ttm_guard_visitor_flags()
returns trigger
language plpgsql security definer
set search_path = public
as $$
begin
  if new.is_admin is distinct from old.is_admin and not public.ttm_is_super() then
    raise exception 'is_admin is managed by super admins';
  end if;
  return new;
end;
$$;
drop trigger if exists ttm_guard_flags on public.maps_visitors;
create trigger ttm_guard_flags before update on public.maps_visitors
  for each row execute function public.ttm_guard_visitor_flags();
drop trigger if exists ttm_guard_flags on public.ohm_visitors;
create trigger ttm_guard_flags before update on public.ohm_visitors
  for each row execute function public.ttm_guard_visitor_flags();

-- ── telemetry: anyone may emit; members read all; only supers mutate ────────
alter table public.maps_telemetry_events enable row level security;
alter table public.ohm_telemetry_events  enable row level security;

drop policy if exists "anon can insert telemetry" on public.maps_telemetry_events;
create policy "anon can insert telemetry" on public.maps_telemetry_events
  for insert to anon, authenticated with check (true);
drop policy if exists "anon can read telemetry (demo)" on public.maps_telemetry_events;
drop policy if exists "admins can read telemetry" on public.maps_telemetry_events;
drop policy if exists "members read telemetry" on public.maps_telemetry_events;
create policy "members read telemetry" on public.maps_telemetry_events
  for select to authenticated using (true);
drop policy if exists "supers mutate telemetry" on public.maps_telemetry_events;
create policy "supers mutate telemetry" on public.maps_telemetry_events
  for delete to authenticated using (public.ttm_is_super());

drop policy if exists "anon can insert ohm telemetry" on public.ohm_telemetry_events;
create policy "anon can insert ohm telemetry" on public.ohm_telemetry_events
  for insert to anon, authenticated with check (true);
drop policy if exists "anon can read ohm telemetry (demo)" on public.ohm_telemetry_events;
drop policy if exists "admins can read ohm telemetry" on public.ohm_telemetry_events;
drop policy if exists "members read ohm telemetry" on public.ohm_telemetry_events;
create policy "members read ohm telemetry" on public.ohm_telemetry_events
  for select to authenticated using (true);
drop policy if exists "supers mutate ohm telemetry" on public.ohm_telemetry_events;
create policy "supers mutate ohm telemetry" on public.ohm_telemetry_events
  for delete to authenticated using (public.ttm_is_super());

-- ── site_config: world-readable; super-admin writable (ecosystem control) ───
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
    drop policy if exists "admins can update site config" on public.maps_site_config;
    drop policy if exists "supers insert site config" on public.maps_site_config;
    create policy "supers insert site config" on public.maps_site_config
      for insert to authenticated with check (public.ttm_is_super());
    drop policy if exists "supers update site config" on public.maps_site_config;
    create policy "supers update site config" on public.maps_site_config
      for update to authenticated
      using (public.ttm_is_super()) with check (public.ttm_is_super());
  end if;
end $$;

-- ── retire earlier helper names ─────────────────────────────────────────────
drop function if exists public.is_ttm_admin();
drop function if exists public.ttm_is_admin();

-- ── enroll the super admin ──────────────────────────────────────────────────
-- EDIT THIS: your own operator email before running, or run the insert
-- separately. Nothing else in this file is deployment-specific.
insert into public.ttm_admins (email, role) values ('you@example.com', 'super')
  on conflict (email) do update set role = 'super';

-- ═══ Dashboard settings (not SQL, one-time) ═══
-- 1. Authentication → Providers → Email: enabled (default).
-- 2. Authentication → Email Templates → Magic Link: body must include
--    {{ .Token }} so members receive the 6-digit gate code.
-- 3. Authentication → URL Configuration → Site URL: your production domain.

-- ── residual honest caveats ─────────────────────────────────────────────────
-- * telemetry INSERT stays open to anon (pre-gate page_views); visitor_email
--   inside an event is client-claimed.
-- * every gated member can read all visitor emails + telemetry BY DESIGN
--   (the requested model); tighten "members read *" policies if that changes.
