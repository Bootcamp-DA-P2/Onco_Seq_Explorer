-- OncoSeq Explorer - Supabase anon (publishable key) minimum access
-- This script is NOT auto-applied by the app.
-- Run it in Supabase SQL Editor after reviewing.

-- 1) DIAGNOSTIC: check if RLS is enabled on required tables
SELECT schemaname, tablename, rowsecurity, hasrules
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN (
    'patients',
    'samples',
    'predictions',
    'clinical_feedback',
    'retraining_buffer',
    'model_versions'
  )
ORDER BY tablename;

-- 2) DIAGNOSTIC: existing policies
SELECT schemaname, tablename, policyname, cmd, roles, qual, with_check
FROM pg_policies
WHERE schemaname = 'public'
  AND tablename IN (
    'patients',
    'samples',
    'predictions',
    'clinical_feedback',
    'retraining_buffer',
    'model_versions'
  )
ORDER BY tablename, policyname;

-- 3) DIAGNOSTIC: table privileges for anon
SELECT grantee, table_schema, table_name, privilege_type
FROM information_schema.table_privileges
WHERE table_schema = 'public'
  AND grantee = 'anon'
  AND table_name IN (
    'patients',
    'samples',
    'predictions',
    'clinical_feedback',
    'retraining_buffer',
    'model_versions'
  )
ORDER BY table_name, privilege_type;

-- 4) MINIMUM grants for PostgREST + anon role
GRANT USAGE ON SCHEMA public TO anon;
GRANT SELECT, INSERT, UPDATE ON TABLE public.patients TO anon;
GRANT SELECT, INSERT, UPDATE ON TABLE public.samples TO anon;
GRANT SELECT, INSERT, UPDATE ON TABLE public.predictions TO anon;
GRANT SELECT, INSERT, UPDATE ON TABLE public.clinical_feedback TO anon;
GRANT SELECT, INSERT, UPDATE ON TABLE public.retraining_buffer TO anon;
GRANT SELECT, INSERT, UPDATE ON TABLE public.model_versions TO anon;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon;

-- 5) If RLS is enabled, ensure minimal policies exist (idempotent)
-- NOTE: These policies are intentionally broad to preserve legacy app behavior.

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname='public' AND tablename='patients' AND policyname='patients_select_anon'
  ) THEN
    EXECUTE 'CREATE POLICY patients_select_anon ON public.patients FOR SELECT TO anon USING (true)';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname='public' AND tablename='patients' AND policyname='patients_insert_anon'
  ) THEN
    EXECUTE 'CREATE POLICY patients_insert_anon ON public.patients FOR INSERT TO anon WITH CHECK (true)';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname='public' AND tablename='patients' AND policyname='patients_update_anon'
  ) THEN
    EXECUTE 'CREATE POLICY patients_update_anon ON public.patients FOR UPDATE TO anon USING (true) WITH CHECK (true)';
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname='public' AND tablename='samples' AND policyname='samples_select_anon'
  ) THEN
    EXECUTE 'CREATE POLICY samples_select_anon ON public.samples FOR SELECT TO anon USING (true)';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname='public' AND tablename='samples' AND policyname='samples_insert_anon'
  ) THEN
    EXECUTE 'CREATE POLICY samples_insert_anon ON public.samples FOR INSERT TO anon WITH CHECK (true)';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname='public' AND tablename='samples' AND policyname='samples_update_anon'
  ) THEN
    EXECUTE 'CREATE POLICY samples_update_anon ON public.samples FOR UPDATE TO anon USING (true) WITH CHECK (true)';
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname='public' AND tablename='predictions' AND policyname='predictions_select_anon'
  ) THEN
    EXECUTE 'CREATE POLICY predictions_select_anon ON public.predictions FOR SELECT TO anon USING (true)';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname='public' AND tablename='predictions' AND policyname='predictions_insert_anon'
  ) THEN
    EXECUTE 'CREATE POLICY predictions_insert_anon ON public.predictions FOR INSERT TO anon WITH CHECK (true)';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname='public' AND tablename='predictions' AND policyname='predictions_update_anon'
  ) THEN
    EXECUTE 'CREATE POLICY predictions_update_anon ON public.predictions FOR UPDATE TO anon USING (true) WITH CHECK (true)';
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname='public' AND tablename='clinical_feedback' AND policyname='clinical_feedback_select_anon'
  ) THEN
    EXECUTE 'CREATE POLICY clinical_feedback_select_anon ON public.clinical_feedback FOR SELECT TO anon USING (true)';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname='public' AND tablename='clinical_feedback' AND policyname='clinical_feedback_insert_anon'
  ) THEN
    EXECUTE 'CREATE POLICY clinical_feedback_insert_anon ON public.clinical_feedback FOR INSERT TO anon WITH CHECK (true)';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname='public' AND tablename='clinical_feedback' AND policyname='clinical_feedback_update_anon'
  ) THEN
    EXECUTE 'CREATE POLICY clinical_feedback_update_anon ON public.clinical_feedback FOR UPDATE TO anon USING (true) WITH CHECK (true)';
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname='public' AND tablename='retraining_buffer' AND policyname='retraining_buffer_select_anon'
  ) THEN
    EXECUTE 'CREATE POLICY retraining_buffer_select_anon ON public.retraining_buffer FOR SELECT TO anon USING (true)';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname='public' AND tablename='retraining_buffer' AND policyname='retraining_buffer_insert_anon'
  ) THEN
    EXECUTE 'CREATE POLICY retraining_buffer_insert_anon ON public.retraining_buffer FOR INSERT TO anon WITH CHECK (true)';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname='public' AND tablename='retraining_buffer' AND policyname='retraining_buffer_update_anon'
  ) THEN
    EXECUTE 'CREATE POLICY retraining_buffer_update_anon ON public.retraining_buffer FOR UPDATE TO anon USING (true) WITH CHECK (true)';
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname='public' AND tablename='model_versions' AND policyname='model_versions_select_anon'
  ) THEN
    EXECUTE 'CREATE POLICY model_versions_select_anon ON public.model_versions FOR SELECT TO anon USING (true)';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname='public' AND tablename='model_versions' AND policyname='model_versions_insert_anon'
  ) THEN
    EXECUTE 'CREATE POLICY model_versions_insert_anon ON public.model_versions FOR INSERT TO anon WITH CHECK (true)';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname='public' AND tablename='model_versions' AND policyname='model_versions_update_anon'
  ) THEN
    EXECUTE 'CREATE POLICY model_versions_update_anon ON public.model_versions FOR UPDATE TO anon USING (true) WITH CHECK (true)';
  END IF;
END $$;

-- Optional: if any of the required tables has RLS disabled but you want a consistent model,
-- enable it manually and keep policies above.
-- ALTER TABLE public.patients ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.samples ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.predictions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.clinical_feedback ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.retraining_buffer ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.model_versions ENABLE ROW LEVEL SECURITY;
