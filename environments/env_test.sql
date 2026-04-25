-- =============================================================================
-- ENVIRONMENT: TEST
-- Usage: psql -U postgres -f environments/env_test.sql
-- =============================================================================

-- ── ★ EDIT THESE VALUES TO RECONFIGURE THE TEST ENVIRONMENT ★ ───────────────

\set env_label          TEST

-- Database
\set db_name            te_mgmt_test
\set db_owner           postgres

-- Schema
\set schema_name        te_test

-- Application user
\set app_user           te_test_user
\set app_password       Test@Env#2025!
\set conn_limit         15

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

-- Seed data: full realistic seed — same as dev so tests run against known data
\set include_seed_data  true

-- ── END OF CONFIGURATION ─────────────────────────────────────────────────────

\i te_core_schema.sql
