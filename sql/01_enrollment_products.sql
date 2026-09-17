IF OBJECT_ID('dbo.stg_members') IS NULL
CREATE TABLE dbo.stg_members (
    file_id VARCHAR(64), attempt_id VARCHAR(36), member_ordinal VARCHAR(32), member_id VARCHAR(64), family_id VARCHAR(64),
    is_subscriber VARCHAR(8), relationship VARCHAR(8), dob VARCHAR(32), has_ssn VARCHAR(8), ssn_last4 VARCHAR(8),
    employee_id VARCHAR(64), interchange_control VARCHAR(32), group_control VARCHAR(32), transaction_control VARCHAR(32), source_segment VARCHAR(32)
);
GO
IF OBJECT_ID('dbo.stg_coverage') IS NULL
CREATE TABLE dbo.stg_coverage (
    file_id VARCHAR(64), attempt_id VARCHAR(36), member_ordinal VARCHAR(32), coverage_ordinal VARCHAR(32), benefit VARCHAR(32),
    plan_id VARCHAR(64), coverage_level VARCHAR(32), effective_date VARCHAR(32), end_date VARCHAR(32), source_segment VARCHAR(32)
);
GO
IF OBJECT_ID('dbo.stg_issues') IS NULL
CREATE TABLE dbo.stg_issues (
    file_id VARCHAR(64), attempt_id VARCHAR(36), member_ordinal VARCHAR(32), source_segment VARCHAR(32), issue_code VARCHAR(64), severity VARCHAR(16)
);
GO
IF OBJECT_ID('dbo.stg_manifest') IS NULL
CREATE TABLE dbo.stg_manifest (
    file_id VARCHAR(64), attempt_id VARCHAR(36), file_name VARCHAR(256), file_bytes VARCHAR(32), parser_version VARCHAR(32),
    rule_version VARCHAR(64), started_at VARCHAR(64), finished_at VARCHAR(64), status VARCHAR(16), member_count VARCHAR(32),
    subscriber_count VARCHAR(32), dependent_count VARCHAR(32), coverage_count VARCHAR(32), issue_count VARCHAR(32), failure_code VARCHAR(128)
);
GO
IF OBJECT_ID('dbo.ref_settings') IS NULL
CREATE TABLE dbo.ref_settings (rule_version VARCHAR(64), as_of_date DATE, child_age_limit INT, medical_benefit VARCHAR(32), rx_benefit VARCHAR(32));
IF OBJECT_ID('dbo.ref_fields') IS NULL
CREATE TABLE dbo.ref_fields (rule_version VARCHAR(64), is_subscriber INT, field_name VARCHAR(32));
IF OBJECT_ID('dbo.ref_relationships') IS NULL
CREATE TABLE dbo.ref_relationships (rule_version VARCHAR(64), relationship VARCHAR(8), is_exempt INT);
IF OBJECT_ID('dbo.ref_benefits') IS NULL
CREATE TABLE dbo.ref_benefits (rule_version VARCHAR(64), benefit VARCHAR(32));
IF OBJECT_ID('dbo.ref_plans') IS NULL
CREATE TABLE dbo.ref_plans (rule_version VARCHAR(64), benefit VARCHAR(32), plan_id VARCHAR(64));
IF OBJECT_ID('dbo.ref_pairs') IS NULL
CREATE TABLE dbo.ref_pairs (rule_version VARCHAR(64), medical_plan VARCHAR(64), rx_plan VARCHAR(64));
GO
IF OBJECT_ID('dbo.audit_run') IS NULL
CREATE TABLE dbo.audit_run (
    attempt_id VARCHAR(36), file_id VARCHAR(64), file_name VARCHAR(256), file_bytes BIGINT, parser_version VARCHAR(32), rule_version VARCHAR(64),
    started_at VARCHAR(64), finished_at VARCHAR(64), parse_status VARCHAR(16), publication_status VARCHAR(16),
    member_count BIGINT, subscriber_count BIGINT, dependent_count BIGINT, coverage_count BIGINT, issue_count BIGINT, failure_code VARCHAR(128)
);
IF OBJECT_ID('dbo.members') IS NULL
CREATE TABLE dbo.members (
    file_id VARCHAR(64), rule_version VARCHAR(64), attempt_id VARCHAR(36), member_ordinal BIGINT, member_id VARCHAR(64), family_id VARCHAR(64),
    is_subscriber INT, relationship VARCHAR(8), dob DATE, has_ssn INT, ssn_last4 VARCHAR(8), employee_id VARCHAR(64),
    interchange_control VARCHAR(32), group_control VARCHAR(32), transaction_control VARCHAR(32), source_segment BIGINT
);
IF OBJECT_ID('dbo.coverage') IS NULL
CREATE TABLE dbo.coverage (
    file_id VARCHAR(64), rule_version VARCHAR(64), attempt_id VARCHAR(36), member_ordinal BIGINT, coverage_ordinal INT,
    benefit VARCHAR(32), plan_id VARCHAR(64), coverage_level VARCHAR(32), effective_date DATE, end_date DATE, source_segment BIGINT
);
IF OBJECT_ID('dbo.exception_result') IS NULL
CREATE TABLE dbo.exception_result (
    file_id VARCHAR(64), rule_version VARCHAR(64), attempt_id VARCHAR(36), member_ordinal BIGINT,
    rule_code VARCHAR(96), benefit VARCHAR(32), severity VARCHAR(16), source_segment BIGINT
);
IF OBJECT_ID('dbo.report_members') IS NULL
CREATE TABLE dbo.report_members (
    member_ordinal BIGINT, member_id VARCHAR(64), family_id VARCHAR(64), member_role VARCHAR(16),
    relationship VARCHAR(8), exception_count BIGINT, source_segment BIGINT, file_id VARCHAR(64), attempt_id VARCHAR(36)
);
IF OBJECT_ID('dbo.report_exceptions') IS NULL
CREATE TABLE dbo.report_exceptions (
    member_ordinal BIGINT, rule_code VARCHAR(96), benefit VARCHAR(32), severity VARCHAR(16), source_segment BIGINT,
    file_id VARCHAR(64), rule_version VARCHAR(64), attempt_id VARCHAR(36)
);
IF OBJECT_ID('dbo.report_health') IS NULL
CREATE TABLE dbo.report_health (
    file_name VARCHAR(256), file_id VARCHAR(64), attempt_id VARCHAR(36), rule_version VARCHAR(64), as_of_date DATE,
    member_count BIGINT, subscriber_count BIGINT, dependent_count BIGINT, coverage_count BIGINT,
    exception_count BIGINT, affected_members BIGINT, parse_issue_count BIGINT, publication_status VARCHAR(16)
);
GO
CREATE OR ALTER VIEW dbo.v_active_coverage AS
SELECT coverage.* FROM dbo.coverage AS coverage
JOIN dbo.ref_settings AS settings ON settings.rule_version = coverage.rule_version
WHERE coverage.effective_date <= settings.as_of_date AND (coverage.end_date IS NULL OR coverage.end_date >= settings.as_of_date);
GO
CREATE OR ALTER VIEW dbo.v_coverage_rollup AS
SELECT file_id, rule_version, member_ordinal, benefit, COUNT_BIG(*) AS election_count, MIN(plan_id) AS plan_id
FROM dbo.v_active_coverage GROUP BY file_id, rule_version, member_ordinal, benefit;
GO
CREATE OR ALTER VIEW dbo.v_rule_findings AS
WITH base AS (
    SELECT member.*, settings.as_of_date, settings.child_age_limit, settings.medical_benefit, settings.rx_benefit,
           COUNT_BIG(*) OVER (PARTITION BY member.file_id, member.rule_version, member.member_id) AS member_key_count,
           SUM(member.is_subscriber) OVER (PARTITION BY member.file_id, member.rule_version, member.family_id) AS family_subscribers,
           MAX(CASE WHEN member.is_subscriber = 1 THEN member.member_ordinal END)
               OVER (PARTITION BY member.file_id, member.rule_version, member.family_id) AS subscriber_ordinal
    FROM dbo.members AS member JOIN dbo.ref_settings AS settings ON settings.rule_version = member.rule_version
), findings AS (
    SELECT file_id, rule_version, member_ordinal, CAST('DUPLICATE_MEMBER' AS VARCHAR(96)) AS rule_code, CAST('' AS VARCHAR(32)) AS benefit
    FROM base WHERE member_key_count > 1
    UNION ALL
    SELECT file_id, rule_version, member_ordinal, 'MULTIPLE_SUBSCRIBERS', '' FROM base WHERE is_subscriber = 1 AND family_subscribers > 1
    UNION ALL
    SELECT file_id, rule_version, member_ordinal, 'ORPHAN_DEPENDENT', '' FROM base WHERE is_subscriber = 0 AND family_subscribers = 0
    UNION ALL
    SELECT file_id, rule_version, member_ordinal, 'AMBIGUOUS_SUBSCRIBER', '' FROM base WHERE is_subscriber = 0 AND family_subscribers > 1
    UNION ALL
    SELECT base.file_id, base.rule_version, base.member_ordinal, 'MISSING_' + UPPER(fields.field_name), ''
    FROM base JOIN dbo.ref_fields AS fields ON fields.rule_version = base.rule_version AND fields.is_subscriber = base.is_subscriber
    WHERE (fields.field_name = 'ssn' AND base.has_ssn = 0) OR (fields.field_name = 'dob' AND base.dob IS NULL)
       OR (fields.field_name = 'employee_id' AND NULLIF(base.employee_id, '') IS NULL)
    UNION ALL
    SELECT file_id, rule_version, member_ordinal, 'FUTURE_DOB', '' FROM base WHERE dob > as_of_date
    UNION ALL
    SELECT file_id, rule_version, member_ordinal, 'MISSING_COVERAGE_EFFECTIVE_DATE', benefit FROM dbo.coverage WHERE effective_date IS NULL
    UNION ALL
    SELECT file_id, rule_version, member_ordinal, 'INVALID_COVERAGE_PERIOD', benefit FROM dbo.coverage WHERE end_date < effective_date
    UNION ALL
    SELECT base.file_id, base.rule_version, base.member_ordinal, 'OVERAGE_DEPENDENT', ''
    FROM base JOIN dbo.ref_relationships AS relation ON relation.rule_version = base.rule_version AND relation.relationship = base.relationship
    WHERE base.is_subscriber = 0 AND relation.is_exempt = 0 AND base.dob IS NOT NULL
      AND DATEDIFF(YEAR, base.dob, base.as_of_date) - CASE WHEN MONTH(base.as_of_date) < MONTH(base.dob)
          OR (MONTH(base.as_of_date) = MONTH(base.dob) AND DAY(base.as_of_date) < DAY(base.dob)) THEN 1 ELSE 0 END >= base.child_age_limit
    UNION ALL
    SELECT file_id, rule_version, member_ordinal, 'DUPLICATE_COVERAGE', benefit FROM dbo.v_active_coverage
    GROUP BY file_id, rule_version, member_ordinal, benefit, plan_id, effective_date, end_date HAVING COUNT_BIG(*) > 1
    UNION ALL
    SELECT file_id, rule_version, member_ordinal, 'AMBIGUOUS_COVERAGE', benefit FROM dbo.v_coverage_rollup WHERE election_count > 1
    UNION ALL
    SELECT election.file_id, election.rule_version, election.member_ordinal, 'UNKNOWN_PLAN', election.benefit
    FROM dbo.v_active_coverage AS election LEFT JOIN dbo.ref_plans AS known_plan
      ON known_plan.rule_version = election.rule_version AND known_plan.benefit = election.benefit AND known_plan.plan_id = election.plan_id
    WHERE known_plan.plan_id IS NULL
    UNION ALL
    SELECT base.file_id, base.rule_version, base.member_ordinal, 'DEPENDENT_PLAN_DIFFERENCE', child.benefit
    FROM base JOIN dbo.v_coverage_rollup AS child ON child.file_id = base.file_id AND child.rule_version = base.rule_version AND child.member_ordinal = base.member_ordinal
    JOIN dbo.ref_benefits AS comparable ON comparable.rule_version = base.rule_version AND comparable.benefit = child.benefit
    JOIN dbo.v_coverage_rollup AS parent ON parent.file_id = base.file_id AND parent.rule_version = base.rule_version
      AND parent.member_ordinal = base.subscriber_ordinal AND parent.benefit = child.benefit
    JOIN dbo.ref_plans AS child_plan ON child_plan.rule_version = child.rule_version AND child_plan.benefit = child.benefit AND child_plan.plan_id = child.plan_id
    JOIN dbo.ref_plans AS parent_plan ON parent_plan.rule_version = parent.rule_version AND parent_plan.benefit = parent.benefit AND parent_plan.plan_id = parent.plan_id
    WHERE base.is_subscriber = 0 AND base.family_subscribers = 1 AND child.election_count = 1 AND parent.election_count = 1 AND child.plan_id <> parent.plan_id
    UNION ALL
    SELECT base.file_id, base.rule_version, base.member_ordinal, 'SUBSCRIBER_COVERAGE_MISSING', child.benefit
    FROM base JOIN dbo.v_coverage_rollup AS child ON child.file_id = base.file_id AND child.rule_version = base.rule_version AND child.member_ordinal = base.member_ordinal
    JOIN dbo.ref_benefits AS comparable ON comparable.rule_version = base.rule_version AND comparable.benefit = child.benefit
    LEFT JOIN dbo.v_coverage_rollup AS parent ON parent.file_id = base.file_id AND parent.rule_version = base.rule_version
      AND parent.member_ordinal = base.subscriber_ordinal AND parent.benefit = child.benefit
    WHERE base.is_subscriber = 0 AND base.family_subscribers = 1 AND parent.member_ordinal IS NULL
    UNION ALL
    SELECT base.file_id, base.rule_version, base.member_ordinal,
           CASE WHEN medical.member_ordinal IS NULL THEN 'MEDICAL_COVERAGE_MISSING' ELSE 'RX_COVERAGE_MISSING' END, ''
    FROM base LEFT JOIN dbo.v_coverage_rollup AS medical ON medical.file_id = base.file_id AND medical.rule_version = base.rule_version
      AND medical.member_ordinal = base.member_ordinal AND medical.benefit = base.medical_benefit
    LEFT JOIN dbo.v_coverage_rollup AS rx ON rx.file_id = base.file_id AND rx.rule_version = base.rule_version
      AND rx.member_ordinal = base.member_ordinal AND rx.benefit = base.rx_benefit
    WHERE (medical.member_ordinal IS NULL AND rx.member_ordinal IS NOT NULL) OR (medical.member_ordinal IS NOT NULL AND rx.member_ordinal IS NULL)
    UNION ALL
    SELECT base.file_id, base.rule_version, base.member_ordinal, 'MEDICAL_RX_MISMATCH', ''
    FROM base JOIN dbo.v_coverage_rollup AS medical ON medical.file_id = base.file_id AND medical.rule_version = base.rule_version
      AND medical.member_ordinal = base.member_ordinal AND medical.benefit = base.medical_benefit AND medical.election_count = 1
    JOIN dbo.v_coverage_rollup AS rx ON rx.file_id = base.file_id AND rx.rule_version = base.rule_version
      AND rx.member_ordinal = base.member_ordinal AND rx.benefit = base.rx_benefit AND rx.election_count = 1
    JOIN dbo.ref_plans AS med_plan ON med_plan.rule_version = medical.rule_version AND med_plan.benefit = medical.benefit AND med_plan.plan_id = medical.plan_id
    JOIN dbo.ref_plans AS rx_plan ON rx_plan.rule_version = rx.rule_version AND rx_plan.benefit = rx.benefit AND rx_plan.plan_id = rx.plan_id
    LEFT JOIN dbo.ref_pairs AS pairing ON pairing.rule_version = base.rule_version AND pairing.medical_plan = medical.plan_id AND pairing.rx_plan = rx.plan_id
    WHERE pairing.medical_plan IS NULL
)
SELECT DISTINCT file_id, rule_version, member_ordinal, rule_code, benefit FROM findings;
GO
CREATE OR ALTER PROCEDURE dbo.record_enrollment_attempt AS
BEGIN
    SET NOCOUNT ON;
    IF (SELECT COUNT_BIG(*) FROM dbo.stg_manifest) <> 1 THROW 52001, 'One manifest is required per serialized run.', 1;
    IF EXISTS (SELECT 1 FROM dbo.stg_manifest WHERE LEN(COALESCE(file_id, '')) <> 64
      OR file_id LIKE '%[^0-9a-f]%' OR LEN(COALESCE(attempt_id, '')) <> 36
      OR NULLIF(file_name, '') IS NULL OR NULLIF(parser_version, '') IS NULL OR NULLIF(rule_version, '') IS NULL
      OR COALESCE(status, '') NOT IN ('Succeeded', 'Failed')
      OR TRY_CONVERT(DATETIME2(6), started_at) IS NULL
      OR (status = 'Succeeded' AND TRY_CONVERT(DATETIME2(6), finished_at) IS NULL)
      OR COALESCE(TRY_CONVERT(BIGINT, NULLIF(file_bytes, '')), 0) <= 0
      OR COALESCE(TRY_CONVERT(BIGINT, NULLIF(member_count, '')), -1) < 0
      OR COALESCE(TRY_CONVERT(BIGINT, NULLIF(subscriber_count, '')), -1) < 0
      OR COALESCE(TRY_CONVERT(BIGINT, NULLIF(dependent_count, '')), -1) < 0
      OR COALESCE(TRY_CONVERT(BIGINT, NULLIF(coverage_count, '')), -1) < 0
      OR COALESCE(TRY_CONVERT(BIGINT, NULLIF(issue_count, '')), -1) < 0
      OR TRY_CONVERT(BIGINT, subscriber_count) + TRY_CONVERT(BIGINT, dependent_count) <> TRY_CONVERT(BIGINT, member_count))
      THROW 52006, 'Manifest fields are missing, malformed or inconsistent.', 1;
    INSERT INTO dbo.audit_run
    SELECT attempt_id, file_id, file_name, TRY_CONVERT(BIGINT, file_bytes), parser_version, rule_version, started_at, finished_at, status,
           CASE WHEN status = 'Succeeded' THEN 'Pending' ELSE 'Blocked' END,
           TRY_CONVERT(BIGINT, member_count), TRY_CONVERT(BIGINT, subscriber_count), TRY_CONVERT(BIGINT, dependent_count),
           TRY_CONVERT(BIGINT, coverage_count), TRY_CONVERT(BIGINT, issue_count), failure_code
    FROM dbo.stg_manifest AS manifest WHERE NOT EXISTS (SELECT 1 FROM dbo.audit_run AS audit WHERE audit.attempt_id = manifest.attempt_id);
END;
GO
CREATE OR ALTER PROCEDURE dbo.publish_enrollment_products AS
BEGIN
    SET NOCOUNT ON;
    EXEC dbo.record_enrollment_attempt;
    DECLARE @file_id VARCHAR(64), @attempt_id VARCHAR(36), @rule_version VARCHAR(64);
    SELECT @file_id = file_id, @attempt_id = attempt_id, @rule_version = rule_version FROM dbo.stg_manifest;
    BEGIN TRY
        IF EXISTS (SELECT 1 FROM dbo.stg_manifest WHERE COALESCE(status, '') <> 'Succeeded' OR TRY_CONVERT(BIGINT, member_count) <= 0)
          THROW 52002, 'Failed or empty parse cannot publish.', 1;
        IF (SELECT COUNT(*) FROM dbo.ref_settings WHERE rule_version = @rule_version) <> 1 THROW 52003, 'Rule version must resolve uniquely.', 1;
        IF EXISTS (
            SELECT 1 FROM dbo.stg_manifest WHERE TRY_CONVERT(BIGINT, member_count) <> (SELECT COUNT_BIG(*) FROM dbo.stg_members)
              OR TRY_CONVERT(BIGINT, coverage_count) <> (SELECT COUNT_BIG(*) FROM dbo.stg_coverage)
              OR TRY_CONVERT(BIGINT, issue_count) <> (SELECT COUNT_BIG(*) FROM dbo.stg_issues)
              OR TRY_CONVERT(BIGINT, subscriber_count) <> (SELECT COUNT_BIG(*) FROM dbo.stg_members WHERE is_subscriber = '1')
              OR TRY_CONVERT(BIGINT, dependent_count) <> (SELECT COUNT_BIG(*) FROM dbo.stg_members WHERE is_subscriber = '0')
        ) THROW 52004, 'Staging counts do not reconcile with the parser manifest.', 1;
          IF EXISTS (SELECT TRY_CONVERT(BIGINT, member_ordinal) FROM dbo.stg_members GROUP BY TRY_CONVERT(BIGINT, member_ordinal) HAVING COUNT_BIG(*) <> 1)
            OR EXISTS (SELECT TRY_CONVERT(BIGINT, member_ordinal), TRY_CONVERT(INT, coverage_ordinal) FROM dbo.stg_coverage
                   GROUP BY TRY_CONVERT(BIGINT, member_ordinal), TRY_CONVERT(INT, coverage_ordinal) HAVING COUNT_BIG(*) <> 1)
            OR EXISTS (SELECT 1 FROM dbo.stg_members WHERE COALESCE(file_id, '') <> @file_id OR COALESCE(attempt_id, '') <> @attempt_id
                   OR COALESCE(TRY_CONVERT(BIGINT, NULLIF(member_ordinal, '')), 0) <= 0
                   OR COALESCE(TRY_CONVERT(BIGINT, NULLIF(source_segment, '')), 0) <= 0
                   OR COALESCE(is_subscriber, '') NOT IN ('0', '1') OR COALESCE(has_ssn, '') NOT IN ('0', '1')
                   OR NULLIF(member_id, '') IS NULL OR NULLIF(family_id, '') IS NULL OR NULLIF(relationship, '') IS NULL
                   OR NULLIF(interchange_control, '') IS NULL OR NULLIF(group_control, '') IS NULL OR NULLIF(transaction_control, '') IS NULL
                   OR (NULLIF(dob, '') IS NOT NULL AND TRY_CONVERT(DATE, dob, 23) IS NULL)
                   OR (has_ssn = '1' AND (LEN(COALESCE(ssn_last4, '')) <> 4 OR ssn_last4 LIKE '%[^0-9]%')))
           OR EXISTS (SELECT 1 FROM dbo.stg_coverage AS election LEFT JOIN dbo.stg_members AS member ON member.member_ordinal = election.member_ordinal
                   WHERE member.member_ordinal IS NULL OR COALESCE(election.file_id, '') <> @file_id OR COALESCE(election.attempt_id, '') <> @attempt_id
                   OR COALESCE(TRY_CONVERT(INT, NULLIF(election.coverage_ordinal, '')), 0) <= 0
                   OR COALESCE(TRY_CONVERT(BIGINT, NULLIF(election.source_segment, '')), 0) <= 0
                   OR NULLIF(election.benefit, '') IS NULL
                   OR (NULLIF(election.effective_date, '') IS NOT NULL AND TRY_CONVERT(DATE, election.effective_date, 23) IS NULL)
                   OR (NULLIF(election.end_date, '') IS NOT NULL AND TRY_CONVERT(DATE, election.end_date, 23) IS NULL))
            OR EXISTS (SELECT 1 FROM dbo.stg_issues AS issue LEFT JOIN dbo.stg_members AS member ON member.member_ordinal = issue.member_ordinal
                   WHERE member.member_ordinal IS NULL OR COALESCE(issue.file_id, '') <> @file_id OR COALESCE(issue.attempt_id, '') <> @attempt_id
                   OR COALESCE(TRY_CONVERT(BIGINT, NULLIF(issue.source_segment, '')), 0) <= 0 OR NULLIF(issue.issue_code, '') IS NULL)
            THROW 52005, 'Staging lineage or ordinal keys are invalid.', 1;
        BEGIN TRANSACTION;
        DELETE FROM dbo.exception_result WHERE file_id = @file_id AND rule_version = @rule_version;
        DELETE FROM dbo.coverage WHERE file_id = @file_id AND rule_version = @rule_version;
        DELETE FROM dbo.members WHERE file_id = @file_id AND rule_version = @rule_version;
        INSERT INTO dbo.members
        SELECT file_id, @rule_version, attempt_id, CONVERT(BIGINT, member_ordinal), member_id, family_id, CONVERT(INT, is_subscriber), relationship,
               CONVERT(DATE, NULLIF(dob, ''), 23), CONVERT(INT, has_ssn), ssn_last4, employee_id, interchange_control, group_control,
               transaction_control, CONVERT(BIGINT, source_segment) FROM dbo.stg_members;
        INSERT INTO dbo.coverage
        SELECT file_id, @rule_version, attempt_id, CONVERT(BIGINT, member_ordinal), CONVERT(INT, coverage_ordinal), benefit, plan_id, coverage_level,
               CONVERT(DATE, NULLIF(effective_date, ''), 23), CONVERT(DATE, NULLIF(end_date, ''), 23), CONVERT(BIGINT, source_segment) FROM dbo.stg_coverage;
        INSERT INTO dbo.exception_result
        SELECT findings.file_id, findings.rule_version, @attempt_id, findings.member_ordinal, findings.rule_code, findings.benefit, 'Review', member.source_segment
        FROM dbo.v_rule_findings AS findings JOIN dbo.members AS member ON member.file_id = findings.file_id
          AND member.rule_version = findings.rule_version AND member.member_ordinal = findings.member_ordinal
        WHERE findings.file_id = @file_id AND findings.rule_version = @rule_version;
        INSERT INTO dbo.exception_result
        SELECT file_id, @rule_version, attempt_id, CONVERT(BIGINT, member_ordinal), 'PARSE_' + issue_code, '', severity, CONVERT(BIGINT, source_segment)
        FROM dbo.stg_issues;
        DELETE FROM dbo.report_members;
        DELETE FROM dbo.report_exceptions;
        DELETE FROM dbo.report_health;
        INSERT INTO dbo.report_members
        SELECT member.member_ordinal, member.member_id, member.family_id, CASE WHEN member.is_subscriber = 1 THEN 'Subscriber' ELSE 'Dependent' END,
               member.relationship, COUNT_BIG(finding.rule_code), member.source_segment, member.file_id, member.attempt_id
        FROM dbo.members AS member LEFT JOIN dbo.exception_result AS finding ON finding.file_id = member.file_id
          AND finding.rule_version = member.rule_version AND finding.member_ordinal = member.member_ordinal
        WHERE member.file_id = @file_id AND member.rule_version = @rule_version
        GROUP BY member.member_ordinal, member.member_id, member.family_id, member.is_subscriber, member.relationship, member.source_segment, member.file_id, member.attempt_id;
        INSERT INTO dbo.report_exceptions
        SELECT member_ordinal, rule_code, benefit, severity, source_segment, file_id, rule_version, attempt_id
        FROM dbo.exception_result WHERE file_id = @file_id AND rule_version = @rule_version;
        INSERT INTO dbo.report_health
        SELECT audit.file_name, @file_id, @attempt_id, @rule_version, settings.as_of_date, audit.member_count, audit.subscriber_count,
               audit.dependent_count, audit.coverage_count, (SELECT COUNT_BIG(*) FROM dbo.report_exceptions),
               (SELECT COUNT_BIG(*) FROM dbo.report_members WHERE exception_count > 0), audit.issue_count, 'Succeeded'
        FROM dbo.audit_run AS audit JOIN dbo.ref_settings AS settings ON settings.rule_version = audit.rule_version WHERE audit.attempt_id = @attempt_id;
        UPDATE dbo.audit_run SET publication_status = 'Succeeded' WHERE attempt_id = @attempt_id;
        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        UPDATE dbo.audit_run SET publication_status = 'Failed', failure_code = 'WAREHOUSE_PUBLICATION_FAILED' WHERE attempt_id = @attempt_id;
        THROW;
    END CATCH;
END;
GO
CREATE OR ALTER VIEW dbo.v_exception_review AS
SELECT member.member_id, member.family_id, finding.* FROM dbo.exception_result AS finding
JOIN dbo.members AS member ON member.file_id = finding.file_id AND member.rule_version = finding.rule_version AND member.member_ordinal = finding.member_ordinal;
GO