-- =============================================================================
-- ENVIRONMENT: DEV
-- Usage: psql -U postgres -f environments/env_dev.sql
-- =============================================================================

-- ── ★ EDIT THESE VALUES TO RECONFIGURE THE DEV ENVIRONMENT ★ ────────────────

\set env_label          DEV

-- Database
\set db_name            te_mgmt_dev
\set db_owner           postgres

-- Schema
\set schema_name        te_dev

-- Application user
\set app_user           te_dev_user
\set app_password       Dev@Local#2025!
\set conn_limit         10

-- Table names (change all here if you need to rename)
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

-- Seed data: 'true' to load realistic T&E data, 'false' for empty tables
\set include_seed_data  true

-- ── END OF CONFIGURATION ─────────────────────────────────────────────────────

\i te_core_schema.sql
