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
-- ⚠ Replace this password with a vault-managed secret before deploying
\set app_user           te_prod_user
\set app_password       ChangeMe!Pr0d@Vault
\set conn_limit         50

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

\i te_core_schema.sql
