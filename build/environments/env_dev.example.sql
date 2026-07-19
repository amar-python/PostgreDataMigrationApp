-- env_dev.example.sql  (TEMPLATE - safe to commit; no real secrets)
-- Copy to env_dev.sql (gitignored) and fill in, or inject app_password at deploy.
\set env_label          DEV
\set db_name            te_mgmt_dev
\set db_owner           postgres
\set schema_name        te_dev
\set app_user           te_dev_user
\set app_password       '__INJECT_AT_DEPLOY__'
\set conn_limit         10
\set include_seed_data  true
\ir ../te_core_schema.sql
