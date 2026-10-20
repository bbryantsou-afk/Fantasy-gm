-- Run once in your own Supabase SQL Editor. No user data or credentials in this file.
create table if not exists public.fgm_profiles (
  owner text primary key check (owner ~ '^[a-f0-9]{64}$'),
  revision bigint not null default 1,
  payload jsonb not null,
  updated_at timestamptz not null default now()
);
alter table public.fgm_profiles enable row level security;
revoke all on public.fgm_profiles from public, anon, authenticated;
grant select, insert, update on public.fgm_profiles to service_role;

create or replace function public.fgm_save_profile(p_owner text, p_expected bigint, p_payload jsonb)
returns bigint language plpgsql security invoker set search_path = '' as $$
declare new_revision bigint;
begin
  if p_owner !~ '^[a-f0-9]{64}$' or octet_length(p_payload::text)>4000000 then
    raise exception 'Invalid profile' using errcode='22023';
  end if;
  if p_expected=0 then
    insert into public.fgm_profiles(owner,revision,payload) values(p_owner,1,p_payload)
    on conflict(owner) do nothing returning revision into new_revision;
  else
    update public.fgm_profiles set payload=p_payload,revision=revision+1,updated_at=now()
    where owner=p_owner and revision=p_expected returning revision into new_revision;
  end if;
  if new_revision is null then
    raise exception 'Profile changed on another device' using errcode='40001';
  end if;
  return new_revision;
end;
$$;
revoke all on function public.fgm_save_profile(text,bigint,jsonb) from public,anon,authenticated;
grant execute on function public.fgm_save_profile(text,bigint,jsonb) to service_role;
