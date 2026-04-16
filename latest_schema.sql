-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.abdm_mock_records (
  abha_id text NOT NULL,
  basic_health_details jsonb DEFAULT '{}'::jsonb,
  pre_existing_conditions jsonb DEFAULT '[]'::jsonb,
  medication_history jsonb DEFAULT '[]'::jsonb,
  allergies jsonb DEFAULT '[]'::jsonb,
  raw_fhir_bundle jsonb,
  last_updated timestamp with time zone DEFAULT timezone('utc'::text, now()),
  CONSTRAINT abdm_mock_records_pkey PRIMARY KEY (abha_id),
  CONSTRAINT abdm_mock_records_abha_id_fkey FOREIGN KEY (abha_id) REFERENCES public.patients(abha_id)
);
CREATE TABLE public.access_requests (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  pharmacist_id uuid NOT NULL,
  patient_id uuid NOT NULL,
  status text NOT NULL DEFAULT 'PENDING'::text,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT access_requests_pkey PRIMARY KEY (id),
  CONSTRAINT access_requests_pharmacist_fkey FOREIGN KEY (pharmacist_id) REFERENCES public.pharmacists(id),
  CONSTRAINT access_requests_patient_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id)
);
CREATE TABLE public.admins (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL,
  username text NOT NULL UNIQUE,
  password text NOT NULL,
  CONSTRAINT admins_pkey PRIMARY KEY (id)
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
CREATE TABLE public.patients (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  abha_id text NOT NULL UNIQUE,
  name text NOT NULL,
  phone text,
  password text NOT NULL,
  registered_by uuid NOT NULL,
  CONSTRAINT patients_pkey PRIMARY KEY (id),
  CONSTRAINT patients_registered_by_fkey FOREIGN KEY (registered_by) REFERENCES public.pharmacists(id)
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