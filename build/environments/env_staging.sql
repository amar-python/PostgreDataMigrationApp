-- =============================================================================
-- ENVIRONMENT: STAGING
-- Usage: psql -U postgres -f environments/env_staging.sql
-- =============================================================================

-- ── ★ EDIT THESE VALUES TO RECONFIGURE THE STAGING ENVIRONMENT ★ ─────────────

\set env_label          STAGING

-- Database
\set db_name            te_mgmt_staging
\set db_owner           postgres

-- Schema
\set schema_name        te_staging

-- Application user
\set app_user           te_stg_user
\set app_password       Stg@Secure#2025!
\set conn_limit         20

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

-- Seed data: false for staging — schema only, no pre-loaded data
-- Load your own anonymised data snapshot after deployment if needed
\set include_seed_data  false

-- ── END OF CONFIGURATION ─────────────────────────────────────────────────────

\i te_core_schema.sql
