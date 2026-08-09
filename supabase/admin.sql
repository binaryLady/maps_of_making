-- Admin status for the visitor table (run in the Supabase SQL editor).
-- Adds is_admin to maps_visitors; the /admin/ area only renders for
-- visitors whose row has is_admin = true. Grant it by email:
--
--   update public.maps_visitors set is_admin = true
--    where email = 'you@example.com';
--
-- (The row exists after that person signs in through the gate once.
--  To pre-grant, insert the row first.)

alter table public.maps_visitors
  add column if not exists is_admin boolean not null default false;

-- NOTE (demo-grade, same as the rest of the schema): the check is enforced
-- client-side with the anon key. Before real traffic, move admin reads
-- behind Supabase Auth + policies keyed to authenticated users.
