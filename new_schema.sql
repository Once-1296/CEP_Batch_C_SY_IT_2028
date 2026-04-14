-- WARNING: This schema is executable. Running it will wipe existing data.

DROP TABLE IF EXISTS public.access_requests CASCADE;
DROP TABLE IF EXISTS public.family_relationships CASCADE;
DROP TABLE IF EXISTS public.patients CASCADE;
DROP TABLE IF EXISTS public.pharmacists CASCADE;
DROP TABLE IF EXISTS public.admins CASCADE;

CREATE TABLE public.admins (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL,
  username text NOT NULL UNIQUE,
  password text NOT NULL,
  CONSTRAINT admins_pkey PRIMARY KEY (id)
);

CREATE TABLE public.pharmacists (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL,
  username text NOT NULL UNIQUE,
  password text NOT NULL,
  phone text,
  license_number text NOT NULL UNIQUE,
  CONSTRAINT pharmacists_pkey PRIMARY KEY (id)
);

CREATE TABLE public.patients (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  abha_id text UNIQUE,
  name text NOT NULL,
  phone text,
  password text NOT NULL,
  current_medications text[] DEFAULT '{}'::text[],
  current_conditions text[] DEFAULT '{}'::text[],
  medical_history text[] DEFAULT '{}'::text[],
  medicines_to_avoid text[] DEFAULT '{}'::text[],
  registered_by uuid NOT NULL,
  CONSTRAINT patients_pkey PRIMARY KEY (id),
  CONSTRAINT patients_registered_by_fkey FOREIGN KEY (registered_by) REFERENCES public.pharmacists(id)
);

CREATE TABLE public.family_relationships (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  patient_id uuid NOT NULL,
  relative_id uuid NOT NULL,
  relationship_type text NOT NULL,
  CONSTRAINT family_relationships_pkey PRIMARY KEY (id),
  CONSTRAINT family_relationships_patient_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id),
  CONSTRAINT family_relationships_relative_fkey FOREIGN KEY (relative_id) REFERENCES public.patients(id)
);

CREATE TABLE public.access_requests (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    pharmacist_id uuid NOT NULL,
    patient_id uuid NOT NULL,
    status text NOT NULL DEFAULT 'PENDING', -- PENDING, ACCEPTED, REJECTED
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT access_requests_pkey PRIMARY KEY (id),
    CONSTRAINT access_requests_pharmacist_fkey FOREIGN KEY (pharmacist_id) REFERENCES public.pharmacists(id),
    CONSTRAINT access_requests_patient_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id),
    UNIQUE(pharmacist_id, patient_id)
);