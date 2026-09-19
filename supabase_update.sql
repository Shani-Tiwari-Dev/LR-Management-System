-- =====================================================================
-- LR Desk — database update (run once, safe to run again)
-- =====================================================================
-- Brings a database that was created from supabase_setup.sql (or by an
-- earlier `manage.py migrate`) up to date with this version:
--
--   1. LR inquiry gets a "Bill date" column.
--   2. LR coming keeps only "LR coming" and "LR not coming". Any old
--      Half day / On leave / Week off rows become "LR not coming" and keep
--      their old wording at the start of the remark.
--   3. Three indexes so the day board, the unsolved count and the monthly
--      report stay fast as the tables grow.
--   4. The matching Django migrations are recorded as done, so a later
--      `python manage.py migrate` will not try to repeat any of this.
--
-- How: Supabase -> SQL Editor -> New query -> paste everything -> Run.
-- Starting from an empty database? Run supabase_setup.sql first, then this.
-- Nothing here deletes data. The "Cartoon" rename is display-only; the
-- column is still lr_no, so no data moves.
-- =====================================================================

BEGIN;

-- 1. Bill date ---------------------------------------------------------
ALTER TABLE lrinquiry_inquiry ADD COLUMN IF NOT EXISTS bill_date date NULL;

-- 2. Two attendance statuses --------------------------------------------
UPDATE attendance_attendance
   SET reason = CASE WHEN reason = '' THEN 'Half day' ELSE 'Half day: ' || reason END,
       status = 'A'
 WHERE status = 'H';

UPDATE attendance_attendance
   SET reason = CASE WHEN reason = '' THEN 'On leave' ELSE 'On leave: ' || reason END,
       status = 'A'
 WHERE status = 'L';

UPDATE attendance_attendance
   SET reason = CASE WHEN reason = '' THEN 'Week off' ELSE 'Week off: ' || reason END,
       status = 'A'
 WHERE status = 'W';

-- 3. Speed-ups ----------------------------------------------------------
CREATE INDEX IF NOT EXISTS lrinquiry_inquiry_inquiry_date_0924fd8f
    ON lrinquiry_inquiry (inquiry_date);
CREATE INDEX IF NOT EXISTS lrinquiry_status_idx
    ON lrinquiry_inquiry (status);
CREATE INDEX IF NOT EXISTS attendance_attendance_date_3c949aa8
    ON attendance_attendance (date);

-- 4. Record the Django migrations as applied -----------------------------
INSERT INTO django_migrations (app, name, applied)
SELECT v.app, v.name, now()
  FROM (VALUES
        ('lrinquiry',  '0002_alter_inquiry_status'),
        ('lrinquiry',  '0003_bill_date_cartoon_and_indexes'),
        ('attendance', '0002_alter_attendance_options_alter_attendance_reason_and_more'),
        ('attendance', '0003_alter_attendance_reason_alter_attendance_status_and_more'),
        ('attendance', '0004_convert_removed_statuses'),
        ('attendance', '0005_two_statuses_and_date_index')
       ) AS v(app, name)
 WHERE NOT EXISTS (
        SELECT 1 FROM django_migrations m WHERE m.app = v.app AND m.name = v.name
       );

COMMIT;
