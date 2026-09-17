WITH expected AS (
    SELECT CAST(1 AS BIGINT) AS member_ordinal, CAST('DUPLICATE_MEMBER' AS VARCHAR(96)) AS rule_code, CAST('' AS VARCHAR(32)) AS benefit
    UNION ALL SELECT 1, 'MULTIPLE_SUBSCRIBERS', ''
    UNION ALL SELECT 2, 'AMBIGUOUS_SUBSCRIBER', ''
    UNION ALL SELECT 2, 'OVERAGE_DEPENDENT', ''
    UNION ALL SELECT 4, 'DEPENDENT_PLAN_DIFFERENCE', 'HLT'
    UNION ALL SELECT 4, 'DEPENDENT_PLAN_DIFFERENCE', 'PDG'
    UNION ALL SELECT 5, 'MISSING_DOB', ''
    UNION ALL SELECT 5, 'MISSING_EMPLOYEE_ID', ''
    UNION ALL SELECT 5, 'MISSING_SSN', ''
    UNION ALL SELECT 7, 'MEDICAL_RX_MISMATCH', ''
    UNION ALL SELECT 8, 'DEPENDENT_PLAN_DIFFERENCE', 'PDG'
    UNION ALL SELECT 9, 'UNKNOWN_PLAN', 'HLT'
    UNION ALL SELECT 10, 'ORPHAN_DEPENDENT', ''
    UNION ALL SELECT 12, 'MISSING_SSN', ''
    UNION ALL SELECT 13, 'DUPLICATE_MEMBER', ''
    UNION ALL SELECT 13, 'MULTIPLE_SUBSCRIBERS', ''
), missing AS (
    SELECT member_ordinal, rule_code, benefit FROM expected
    EXCEPT SELECT member_ordinal, rule_code, benefit FROM dbo.report_exceptions
), unexpected AS (
    SELECT member_ordinal, rule_code, benefit FROM dbo.report_exceptions
    EXCEPT SELECT member_ordinal, rule_code, benefit FROM expected
)
SELECT 'Missing finding' AS failed_check, CONCAT(member_ordinal, ':', rule_code, ':', benefit) AS detail FROM missing
UNION ALL SELECT 'Unexpected finding', CONCAT(member_ordinal, ':', rule_code, ':', benefit) FROM unexpected
UNION ALL SELECT 'Member count', 'Expected 13' WHERE (SELECT COUNT_BIG(*) FROM dbo.report_members) <> 13
UNION ALL SELECT 'Subscriber count', 'Expected 7' WHERE (SELECT COUNT_BIG(*) FROM dbo.report_members WHERE member_role = 'Subscriber') <> 7
UNION ALL SELECT 'Dependent count', 'Expected 6' WHERE (SELECT COUNT_BIG(*) FROM dbo.report_members WHERE member_role = 'Dependent') <> 6
UNION ALL SELECT 'Exception count', 'Expected 16' WHERE (SELECT COUNT_BIG(*) FROM dbo.report_exceptions) <> 16
UNION ALL SELECT 'Affected members', 'Expected 10' WHERE (SELECT COUNT_BIG(*) FROM dbo.report_members WHERE exception_count > 0) <> 10
UNION ALL SELECT 'Member ordinal uniqueness', 'One row per ordinal' WHERE EXISTS (
    SELECT member_ordinal FROM dbo.report_members GROUP BY member_ordinal HAVING COUNT_BIG(*) <> 1)
UNION ALL SELECT 'Finding uniqueness', 'One row per member/rule/benefit' WHERE EXISTS (
    SELECT member_ordinal, rule_code, benefit FROM dbo.report_exceptions GROUP BY member_ordinal, rule_code, benefit HAVING COUNT_BIG(*) <> 1)
UNION ALL SELECT 'Health count', 'Exactly one latest successful publication' WHERE (SELECT COUNT_BIG(*) FROM dbo.report_health) <> 1
UNION ALL SELECT 'Health values', 'Counts, file hash, rule version or status differ' WHERE EXISTS (
    SELECT 1 FROM dbo.report_health WHERE member_count <> 13 OR subscriber_count <> 7 OR dependent_count <> 6 OR coverage_count <> 26
      OR exception_count <> 16 OR affected_members <> 10 OR parse_issue_count <> 0 OR publication_status <> 'Succeeded'
      OR file_id <> '17908648f246c1bb69d00cb238f3389aa393d809c1537fda9b070101944910e8'
      OR rule_version <> 'SYNTHETIC-2027-v1' OR as_of_date <> '2027-01-01')
UNION ALL SELECT 'Member lineage', 'Member snapshot differs from health' WHERE EXISTS (
    SELECT 1 FROM dbo.report_members AS member LEFT JOIN dbo.report_health AS health
      ON member.file_id = health.file_id AND member.attempt_id = health.attempt_id WHERE health.attempt_id IS NULL)
UNION ALL SELECT 'Finding lineage', 'Finding snapshot differs from health' WHERE EXISTS (
    SELECT 1 FROM dbo.report_exceptions AS finding LEFT JOIN dbo.report_health AS health
      ON finding.file_id = health.file_id AND finding.attempt_id = health.attempt_id AND finding.rule_version = health.rule_version
      WHERE health.attempt_id IS NULL)
UNION ALL SELECT 'Audit status', 'Latest publication has no successful attempt' WHERE EXISTS (
    SELECT 1 FROM dbo.report_health AS health LEFT JOIN dbo.audit_run AS audit ON audit.attempt_id = health.attempt_id
      WHERE audit.attempt_id IS NULL OR audit.parse_status <> 'Succeeded' OR audit.publication_status <> 'Succeeded');