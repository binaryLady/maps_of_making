-- Whitelabel / site configuration for the TTM stack.
-- Paste into the Supabase SQL editor (safe to run after schema.sql, or alone).
--
-- One row per config key, JSONB values. The site reads these at load
-- (cached in the browser for 60s); the admin "Whitelabel" card writes them.
--
-- Keys the frontend understands:
--   'brand' : { "name": "maps of making", "tagline": "v0.2 · demo",
--               "footer_name": "", "footer_hidden": false,
--               "page_title": "Maps of Making — demo" }
--   'theme' : { "default": "ttm" | "terminal" | "",
--               "tokens": { "--ttm-pink": "#E904E5", ... } }
--   'gate'  : { "enabled": true, "title": "Before you explore",
--               "body": "Tell us who you are…", "fine": "Stored with…" }

create table if not exists public.maps_site_config (
  key         text primary key,
  value       jsonb not null default '{}'::jsonb,
  updated_at  timestamptz not null default now()
);

alter table public.maps_site_config enable row level security;

-- Everyone may read the whitelabel config (it is, by nature, public).
create policy "anon can read site_config" on public.maps_site_config
  for select to anon using (true);

-- DEMO-GRADE write access: the admin dashboard publishes with the anon key.
-- Before real traffic, replace these two with an authenticated-admin policy.
create policy "anon can insert site_config (demo)" on public.maps_site_config
  for insert to anon with check (true);
create policy "anon can update site_config (demo)" on public.maps_site_config
  for update to anon using (true) with check (true);

-- Sensible starting rows (idempotent).
insert into public.maps_site_config (key, value) values
  ('brand', '{"name": "maps of making", "tagline": "v0.2 · demo", "footer_name": "", "footer_hidden": false, "page_title": "Maps of Making — demo"}'),
  ('theme', '{"default": "ttm", "tokens": {}}'),
  ('gate',  '{"enabled": true, "title": "Sign in", "body": "Name and email to enter. Valid for 24 hours on this device.", "fine": "Stored by the site operator."}')
on conflict (key) do nothing;
