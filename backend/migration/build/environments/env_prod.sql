-- =============================================================================
-- ENVIRONMENT: PROD
-- Usage: psql -U postgres -f environments/env_prod.sql
--
-- ⚠  PRODUCTION — Run with care.
--    - Seed data is DISABLED (schema only).
--    - Use a secrets manager (e.g. Azure Key Vault, HashiCorp Vault)
--      to inject app_password rather than storing it here.
--    - Rotate the password after first deployment.
-- =============================================================================

-- ── ★ EDIT THESE VALUES TO RECONFIGURE THE PROD ENVIRONMENT ★ ───────────────

\set env_label          PROD

-- Database
\set db_name            te_mgmt_prod
\set db_owner           postgres

-- Schema
\set schema_name        te_prod

-- Application user
\set app_user           te_prod_user
\set conn_limit         50

-- ⚠ app_password MUST be injected from your secrets manager.
--   Pass via: psql -v app_password="$(az keyvault secret show ...)" -f env_prod.sql
--   The line below is INTENTIONALLY commented out — uncommenting it for
--   production is a security incident.
-- \set app_password 'do-not-commit-real-passwords-here'

-- Table names
\set tbl_organisations  organisations
\set tbl_personnel      personnel
\set tbl_test_programs  test_programs
\set tbl_temp_documents temp_documents
\set tbl_test_phases    test_phases
\set tbl_requirements   requirements
\set tbl_test_cases     test_cases
\set tbl_vcrm_entries   vcrm_entries
\set tbl_test_events    test_events
\set tbl_test_results   test_results
\set tbl_defect_reports defect_reports
\set tbl_evidence_artifacts evidence_artifacts

-- Seed data: always false for production
\set include_seed_data  false

-- ── END OF CONFIGURATION ─────────────────────────────────────────────────────

-- Fail fast if caller did not inject app_password.
\if :{?app_password}
\else
   \echo 'ERROR: -v app_password=<value> is required for env_prod.sql.'
   \echo 'Example: psql -v app_password="$(az keyvault secret show ...)" -f env_prod.sql'
   \quit
\endif

\ir ../te_core_schema.sql
