-- =============================================================================
-- TEST SUITE: SCHEMA STRUCTURE, INDEXES, TRIGGERS & BUSINESS RULES
-- File: tests/suites/test_05_schema_and_business_rules.sql
-- =============================================================================

\echo '   [suite 05] schema structure, indexes, triggers & business rules'

DO
$$
DECLARE
   v_count     BIGINT;
   v_value     TEXT;
   v_ts1       TIMESTAMPTZ;
   v_ts2       TIMESTAMPTZ;
BEGIN

-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION P: SCHEMA STRUCTURE — Table existence
-- ─────────────────────────────────────────────────────────────────────────────

   -- P01–P12: all 12 tables exist in the schema
   SELECT COUNT(*) INTO v_count FROM information_schema.tables
   WHERE table_schema = :'schema_name' AND table_name = :'tbl_organisations';
   PERFORM :"schema_name".assert_equals(
      'schema', 'P01 — Table organisations exists', 1::BIGINT, v_count);

   SELECT COUNT(*) INTO v_count FROM information_schema.tables
   WHERE table_schema = :'schema_name' AND table_name = :'tbl_personnel';
   PERFORM :"schema_name".assert_equals(
      'schema', 'P02 — Table personnel exists', 1::BIGINT, v_count);

   SELECT COUNT(*) INTO v_count FROM information_schema.tables
   WHERE table_schema = :'schema_name' AND table_name = :'tbl_test_programs';
   PERFORM :"schema_name".assert_equals(
      'schema', 'P03 — Table test_programs exists', 1::BIGINT, v_count);

   SELECT COUNT(*) INTO v_count FROM information_schema.tables
   WHERE table_schema = :'schema_name' AND table_name = :'tbl_temp_documents';
   PERFORM :"schema_name".assert_equals(
      'schema', 'P04 — Table temp_documents exists', 1::BIGINT, v_count);

   SELECT COUNT(*) INTO v_count FROM information_schema.tables
   WHERE table_schema = :'schema_name' AND table_name = :'tbl_test_phases';
   PERFORM :"schema_name".assert_equals(
      'schema', 'P05 — Table test_phases exists', 1::BIGINT, v_count);

   SELECT COUNT(*) INTO v_count FROM information_schema.tables
   WHERE table_schema = :'schema_name' AND table_name = :'tbl_requirements';
   PERFORM :"schema_name".assert_equals(
      'schema', 'P06 — Table requirements exists', 1::BIGINT, v_count);

   SELECT COUNT(*) INTO v_count FROM information_schema.tables
   WHERE table_schema = :'schema_name' AND table_name = :'tbl_test_cases';
   PERFORM :"schema_name".assert_equals(
      'schema', 'P07 — Table test_cases exists', 1::BIGINT, v_count);

   SELECT COUNT(*) INTO v_count FROM information_schema.tables
   WHERE table_schema = :'schema_name' AND table_name = :'tbl_vcrm_entries';
   PERFORM :"schema_name".assert_equals(
      'schema', 'P08 — Table vcrm_entries exists', 1::BIGINT, v_count);

   SELECT COUNT(*) INTO v_count FROM information_schema.tables
   WHERE table_schema = :'schema_name' AND table_name = :'tbl_test_events';
   PERFORM :"schema_name".assert_equals(
      'schema', 'P09 — Table test_events exists', 1::BIGINT, v_count);

   SELECT COUNT(*) INTO v_count FROM information_schema.tables
   WHERE table_schema = :'schema_name' AND table_name = :'tbl_test_results';
   PERFORM :"schema_name".assert_equals(
      'schema', 'P10 — Table test_results exists', 1::BIGINT, v_count);

   SELECT COUNT(*) INTO v_count FROM information_schema.tables
   WHERE table_schema = :'schema_name' AND table_name = :'tbl_defect_reports';
   PERFORM :"schema_name".assert_equals(
      'schema', 'P11 — Table defect_reports exists', 1::BIGINT, v_count);

   SELECT COUNT(*) INTO v_count FROM information_schema.tables
   WHERE table_schema = :'schema_name' AND table_name = :'tbl_evidence_artifacts';
   PERFORM :"schema_name".assert_equals(
      'schema', 'P12 — Table evidence_artifacts exists', 1::BIGINT, v_count);

-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION Q: INDEXES — Critical indexes exist
-- ─────────────────────────────────────────────────────────────────────────────

   -- Q01: personnel org index
   SELECT COUNT(*) INTO v_count FROM pg_indexes
   WHERE schemaname = :'schema_name' AND indexname = 'idx_personnel_org';
   PERFORM :"schema_name".assert_equals(
      'schema', 'Q01 — Index idx_personnel_org exists', 1::BIGINT, v_count);

   -- Q02: programs status index
   SELECT COUNT(*) INTO v_count FROM pg_indexes
   WHERE schemaname = :'schema_name' AND indexname = 'idx_programs_status';
   PERFORM :"schema_name".assert_equals(
      'schema', 'Q02 — Index idx_programs_status exists', 1::BIGINT, v_count);

   -- Q03: test cases phase index
   SELECT COUNT(*) INTO v_count FROM pg_indexes
   WHERE schemaname = :'schema_name' AND indexname = 'idx_testcases_phase';
   PERFORM :"schema_name".assert_equals(
      'schema', 'Q03 — Index idx_testcases_phase exists', 1::BIGINT, v_count);

   -- Q04: test results verdict index
   SELECT COUNT(*) INTO v_count FROM pg_indexes
   WHERE schemaname = :'schema_name' AND indexname = 'idx_results_verdict';
   PERFORM :"schema_name".assert_equals(
      'schema', 'Q04 — Index idx_results_verdict exists', 1::BIGINT, v_count);

   -- Q05: defects severity index
   SELECT COUNT(*) INTO v_count FROM pg_indexes
   WHERE schemaname = :'schema_name' AND indexname = 'idx_defects_severity';
   PERFORM :"schema_name".assert_equals(
      'schema', 'Q05 — Index idx_defects_severity exists', 1::BIGINT, v_count);

   -- Q06: VCRM req index
   SELECT COUNT(*) INTO v_count FROM pg_indexes
   WHERE schemaname = :'schema_name' AND indexname = 'idx_vcrm_req';
   PERFORM :"schema_name".assert_equals(
      'schema', 'Q06 — Index idx_vcrm_req exists', 1::BIGINT, v_count);

   -- Q07: trigram index on personnel email
   SELECT COUNT(*) INTO v_count FROM pg_indexes
   WHERE schemaname = :'schema_name' AND indexname = 'idx_personnel_email_trgm';
   PERFORM :"schema_name".assert_equals(
      'schema', 'Q07 — GIN trigram index idx_personnel_email_trgm exists', 1::BIGINT, v_count);

-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION R: TRIGGERS — updated_at fires on UPDATE
-- ─────────────────────────────────────────────────────────────────────────────

   -- R01: updating organisations updates updated_at
   DECLARE
      v_org_id UUID;
   BEGIN
      SELECT org_id INTO v_org_id FROM :"schema_name".:"tbl_organisations" LIMIT 1;
      SELECT updated_at INTO v_ts1
      FROM :"schema_name".:"tbl_organisations" WHERE org_id = v_org_id;

      PERFORM pg_sleep(0.01);   -- tiny delay to ensure clock ticks

      EXECUTE format(
         'UPDATE %I.%I SET is_active = is_active WHERE org_id = %L',
         :'schema_name', :'tbl_organisations', v_org_id
      );
      SELECT updated_at INTO v_ts2
      FROM :"schema_name".:"tbl_organisations" WHERE org_id = v_org_id;

      PERFORM :"schema_name".assert_true(
         'schema', 'R01 — Trigger fires: organisations.updated_at advances on UPDATE',
         $b$ $b$ || v_ts2::TEXT || ' > ' || v_ts1::TEXT
      );
   END;

   -- R02: updating test_programs updates updated_at
   DECLARE
      v_prog_id UUID;
   BEGIN
      SELECT program_id INTO v_prog_id FROM :"schema_name".:"tbl_test_programs" LIMIT 1;
      SELECT updated_at INTO v_ts1
      FROM :"schema_name".:"tbl_test_programs" WHERE program_id = v_prog_id;

      PERFORM pg_sleep(0.01);

      EXECUTE format(
         'UPDATE %I.%I SET status = status WHERE program_id = %L',
         :'schema_name', :'tbl_test_programs', v_prog_id
      );
      SELECT updated_at INTO v_ts2
      FROM :"schema_name".:"tbl_test_programs" WHERE program_id = v_prog_id;

      PERFORM :"schema_name".assert_true(
         'schema', 'R02 — Trigger fires: test_programs.updated_at advances on UPDATE',
         $b$ $b$ || v_ts2::TEXT || ' > ' || v_ts1::TEXT
      );
   END;

   -- R03: trigger registered on personnel table
   SELECT COUNT(*) INTO v_count
   FROM information_schema.triggers
   WHERE trigger_schema = :'schema_name'
   AND   event_object_table = :'tbl_personnel'
   AND   trigger_name = 'trg_updated_at';
   PERFORM :"schema_name".assert_equals(
      'schema', 'R03 — Trigger trg_updated_at registered on personnel', 1::BIGINT, v_count);

   -- R04: trigger registered on defect_reports table
   SELECT COUNT(*) INTO v_count
   FROM information_schema.triggers
   WHERE trigger_schema = :'schema_name'
   AND   event_object_table = :'tbl_defect_reports'
   AND   trigger_name = 'trg_updated_at';
   PERFORM :"schema_name".assert_equals(
      'schema', 'R04 — Trigger trg_updated_at registered on defect_reports', 1::BIGINT, v_count);

-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION S: BUSINESS RULES — Cross-table logic
-- ─────────────────────────────────────────────────────────────────────────────

   -- S01: every test result's test case belongs to the same program as its event
   SELECT COUNT(*) INTO v_count
   FROM :"schema_name".:"tbl_test_results" tr
   JOIN :"schema_name".:"tbl_test_events"  ev ON ev.event_id = tr.event_id
   JOIN :"schema_name".:"tbl_test_phases"  ph ON ph.phase_id = ev.phase_id
   JOIN :"schema_name".:"tbl_test_cases"   tc ON tc.tc_id    = tr.tc_id
   WHERE tc.phase_id != ev.phase_id;    -- test case phase should match event phase
   PERFORM :"schema_name".assert_equals(
      'business_rules', 'S01 — All results: test case phase matches event phase',
      0::BIGINT, v_count
   );

   -- S02: fail verdicts all have a DR raised against the same program
   SELECT COUNT(*) INTO v_count
   FROM :"schema_name".:"tbl_test_results" tr
   JOIN :"schema_name".:"tbl_test_events"  ev ON ev.event_id  = tr.event_id
   JOIN :"schema_name".:"tbl_test_phases"  ph ON ph.phase_id  = ev.phase_id
   JOIN :"schema_name".:"tbl_test_programs" tp ON tp.program_id = ph.program_id
   WHERE tr.verdict = 'fail'
   AND NOT EXISTS (
      SELECT 1 FROM :"schema_name".:"tbl_defect_reports" dr
      WHERE dr.result_id  = tr.result_id
      AND   dr.program_id = tp.program_id
   );
   PERFORM :"schema_name".assert_equals(
      'business_rules', 'S02 — All fail verdicts have a matching DR raised',
      0::BIGINT, v_count
   );

   -- S03: no test results exist for events that are still 'planned'
   SELECT COUNT(*) INTO v_count
   FROM :"schema_name".:"tbl_test_results" tr
   JOIN :"schema_name".:"tbl_test_events"  ev ON ev.event_id = tr.event_id
   WHERE ev.status = 'planned';
   PERFORM :"schema_name".assert_equals(
      'business_rules', 'S03 — No results recorded against planned (future) events',
      0::BIGINT, v_count
   );

   -- S04: all open defects belong to an active program
   SELECT COUNT(*) INTO v_count
   FROM :"schema_name".:"tbl_defect_reports" dr
   JOIN :"schema_name".:"tbl_test_programs"  tp ON tp.program_id = dr.program_id
   WHERE dr.status = 'open'
   AND   tp.status NOT IN ('active');
   PERFORM :"schema_name".assert_equals(
      'business_rules', 'S04 — All open DRs belong to an active program',
      0::BIGINT, v_count
   );

   -- S05: no personnel have a clearance level lower than NV1 assigned to PROTECTED programs
   SELECT COUNT(*) INTO v_count
   FROM :"schema_name".:"tbl_test_cases" tc
   JOIN :"schema_name".:"tbl_test_phases"   ph ON ph.phase_id   = tc.phase_id
   JOIN :"schema_name".:"tbl_test_programs" tp ON tp.program_id = ph.program_id
   JOIN :"schema_name".:"tbl_personnel"     p  ON p.person_id   = tc.author_id
   WHERE tp.classification IN ('PROTECTED','SECRET','TOP SECRET')
   AND   p.clearance = 'baseline';
   PERFORM :"schema_name".assert_equals(
      'business_rules',
      'S05 — No baseline-cleared personnel authoring cases in PROTECTED+ programs',
      0::BIGINT, v_count
   );

   -- S06: all VCRM entries belong to the same program as their requirement
   SELECT COUNT(*) INTO v_count
   FROM :"schema_name".:"tbl_vcrm_entries" v
   JOIN :"schema_name".:"tbl_requirements" r  ON r.req_id   = v.req_id
   JOIN :"schema_name".:"tbl_test_cases"   tc ON tc.tc_id   = v.tc_id
   JOIN :"schema_name".:"tbl_test_phases"  ph ON ph.phase_id = tc.phase_id
   WHERE r.program_id != ph.program_id;
   PERFORM :"schema_name".assert_equals(
      'business_rules', 'S06 — All VCRM entries: requirement and test case share same program',
      0::BIGINT, v_count
   );

   -- S07: no event has planned_end before planned_start
   SELECT COUNT(*) INTO v_count
   FROM :"schema_name".:"tbl_test_events"
   WHERE planned_end IS NOT NULL AND planned_end < planned_start;
   PERFORM :"schema_name".assert_equals(
      'business_rules', 'S07 — No test events have planned_end before planned_start',
      0::BIGINT, v_count
   );

   -- S08: evidence_artifacts table exists and is empty (no results linked yet)
   SELECT COUNT(*) INTO v_count FROM :"schema_name".:"tbl_evidence_artifacts";
   PERFORM :"schema_name".assert_equals(
      'business_rules', 'S08 — evidence_artifacts table is empty (no files uploaded yet)',
      0::BIGINT, v_count
   );

END;
$$;
