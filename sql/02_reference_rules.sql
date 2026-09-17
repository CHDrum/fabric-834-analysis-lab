IF EXISTS (SELECT 1 FROM dbo.ref_settings WHERE rule_version = 'SYNTHETIC-2027-v1')
BEGIN
IF (SELECT COUNT_BIG(*) FROM dbo.ref_settings WHERE rule_version = 'SYNTHETIC-2027-v1') <> 1 OR EXISTS (SELECT rule_version, as_of_date, child_age_limit, medical_benefit, rx_benefit FROM dbo.ref_settings WHERE rule_version = 'SYNTHETIC-2027-v1' EXCEPT SELECT * FROM (VALUES ('SYNTHETIC-2027-v1', '2027-01-01', '26', 'HLT', 'PDG')) AS expected (rule_version, as_of_date, child_age_limit, medical_benefit, rx_benefit)) OR EXISTS (SELECT * FROM (VALUES ('SYNTHETIC-2027-v1', '2027-01-01', '26', 'HLT', 'PDG')) AS expected (rule_version, as_of_date, child_age_limit, medical_benefit, rx_benefit) EXCEPT SELECT rule_version, as_of_date, child_age_limit, medical_benefit, rx_benefit FROM dbo.ref_settings WHERE rule_version = 'SYNTHETIC-2027-v1')
THROW 52101, 'RULE_VERSION_IMMUTABLE: use a new version for changed rules.', 1;
IF (SELECT COUNT_BIG(*) FROM dbo.ref_fields WHERE rule_version = 'SYNTHETIC-2027-v1') <> 5 OR EXISTS (SELECT rule_version, is_subscriber, field_name FROM dbo.ref_fields WHERE rule_version = 'SYNTHETIC-2027-v1' EXCEPT SELECT * FROM (VALUES ('SYNTHETIC-2027-v1', '1', 'ssn'),
('SYNTHETIC-2027-v1', '1', 'dob'),
('SYNTHETIC-2027-v1', '1', 'employee_id'),
('SYNTHETIC-2027-v1', '0', 'ssn'),
('SYNTHETIC-2027-v1', '0', 'dob')) AS expected (rule_version, is_subscriber, field_name)) OR EXISTS (SELECT * FROM (VALUES ('SYNTHETIC-2027-v1', '1', 'ssn'),
('SYNTHETIC-2027-v1', '1', 'dob'),
('SYNTHETIC-2027-v1', '1', 'employee_id'),
('SYNTHETIC-2027-v1', '0', 'ssn'),
('SYNTHETIC-2027-v1', '0', 'dob')) AS expected (rule_version, is_subscriber, field_name) EXCEPT SELECT rule_version, is_subscriber, field_name FROM dbo.ref_fields WHERE rule_version = 'SYNTHETIC-2027-v1')
THROW 52101, 'RULE_VERSION_IMMUTABLE: use a new version for changed rules.', 1;
IF (SELECT COUNT_BIG(*) FROM dbo.ref_relationships WHERE rule_version = 'SYNTHETIC-2027-v1') <> 1 OR EXISTS (SELECT rule_version, relationship, is_exempt FROM dbo.ref_relationships WHERE rule_version = 'SYNTHETIC-2027-v1' EXCEPT SELECT * FROM (VALUES ('SYNTHETIC-2027-v1', '19', '0')) AS expected (rule_version, relationship, is_exempt)) OR EXISTS (SELECT * FROM (VALUES ('SYNTHETIC-2027-v1', '19', '0')) AS expected (rule_version, relationship, is_exempt) EXCEPT SELECT rule_version, relationship, is_exempt FROM dbo.ref_relationships WHERE rule_version = 'SYNTHETIC-2027-v1')
THROW 52101, 'RULE_VERSION_IMMUTABLE: use a new version for changed rules.', 1;
IF (SELECT COUNT_BIG(*) FROM dbo.ref_benefits WHERE rule_version = 'SYNTHETIC-2027-v1') <> 2 OR EXISTS (SELECT rule_version, benefit FROM dbo.ref_benefits WHERE rule_version = 'SYNTHETIC-2027-v1' EXCEPT SELECT * FROM (VALUES ('SYNTHETIC-2027-v1', 'HLT'),
('SYNTHETIC-2027-v1', 'PDG')) AS expected (rule_version, benefit)) OR EXISTS (SELECT * FROM (VALUES ('SYNTHETIC-2027-v1', 'HLT'),
('SYNTHETIC-2027-v1', 'PDG')) AS expected (rule_version, benefit) EXCEPT SELECT rule_version, benefit FROM dbo.ref_benefits WHERE rule_version = 'SYNTHETIC-2027-v1')
THROW 52101, 'RULE_VERSION_IMMUTABLE: use a new version for changed rules.', 1;
IF (SELECT COUNT_BIG(*) FROM dbo.ref_plans WHERE rule_version = 'SYNTHETIC-2027-v1') <> 4 OR EXISTS (SELECT rule_version, benefit, plan_id FROM dbo.ref_plans WHERE rule_version = 'SYNTHETIC-2027-v1' EXCEPT SELECT * FROM (VALUES ('SYNTHETIC-2027-v1', 'HLT', 'MED-A'),
('SYNTHETIC-2027-v1', 'HLT', 'MED-B'),
('SYNTHETIC-2027-v1', 'PDG', 'RX-A'),
('SYNTHETIC-2027-v1', 'PDG', 'RX-B')) AS expected (rule_version, benefit, plan_id)) OR EXISTS (SELECT * FROM (VALUES ('SYNTHETIC-2027-v1', 'HLT', 'MED-A'),
('SYNTHETIC-2027-v1', 'HLT', 'MED-B'),
('SYNTHETIC-2027-v1', 'PDG', 'RX-A'),
('SYNTHETIC-2027-v1', 'PDG', 'RX-B')) AS expected (rule_version, benefit, plan_id) EXCEPT SELECT rule_version, benefit, plan_id FROM dbo.ref_plans WHERE rule_version = 'SYNTHETIC-2027-v1')
THROW 52101, 'RULE_VERSION_IMMUTABLE: use a new version for changed rules.', 1;
IF (SELECT COUNT_BIG(*) FROM dbo.ref_pairs WHERE rule_version = 'SYNTHETIC-2027-v1') <> 2 OR EXISTS (SELECT rule_version, medical_plan, rx_plan FROM dbo.ref_pairs WHERE rule_version = 'SYNTHETIC-2027-v1' EXCEPT SELECT * FROM (VALUES ('SYNTHETIC-2027-v1', 'MED-A', 'RX-A'),
('SYNTHETIC-2027-v1', 'MED-B', 'RX-B')) AS expected (rule_version, medical_plan, rx_plan)) OR EXISTS (SELECT * FROM (VALUES ('SYNTHETIC-2027-v1', 'MED-A', 'RX-A'),
('SYNTHETIC-2027-v1', 'MED-B', 'RX-B')) AS expected (rule_version, medical_plan, rx_plan) EXCEPT SELECT rule_version, medical_plan, rx_plan FROM dbo.ref_pairs WHERE rule_version = 'SYNTHETIC-2027-v1')
THROW 52101, 'RULE_VERSION_IMMUTABLE: use a new version for changed rules.', 1;
END
ELSE
BEGIN
BEGIN TRY
BEGIN TRANSACTION;
INSERT INTO dbo.ref_settings VALUES
('SYNTHETIC-2027-v1', '2027-01-01', '26', 'HLT', 'PDG');
INSERT INTO dbo.ref_fields VALUES
('SYNTHETIC-2027-v1', '1', 'ssn'),
('SYNTHETIC-2027-v1', '1', 'dob'),
('SYNTHETIC-2027-v1', '1', 'employee_id'),
('SYNTHETIC-2027-v1', '0', 'ssn'),
('SYNTHETIC-2027-v1', '0', 'dob');
INSERT INTO dbo.ref_relationships VALUES
('SYNTHETIC-2027-v1', '19', '0');
INSERT INTO dbo.ref_benefits VALUES
('SYNTHETIC-2027-v1', 'HLT'),
('SYNTHETIC-2027-v1', 'PDG');
INSERT INTO dbo.ref_plans VALUES
('SYNTHETIC-2027-v1', 'HLT', 'MED-A'),
('SYNTHETIC-2027-v1', 'HLT', 'MED-B'),
('SYNTHETIC-2027-v1', 'PDG', 'RX-A'),
('SYNTHETIC-2027-v1', 'PDG', 'RX-B');
INSERT INTO dbo.ref_pairs VALUES
('SYNTHETIC-2027-v1', 'MED-A', 'RX-A'),
('SYNTHETIC-2027-v1', 'MED-B', 'RX-B');
COMMIT TRANSACTION;
END TRY
BEGIN CATCH
IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
THROW;
END CATCH
END;
