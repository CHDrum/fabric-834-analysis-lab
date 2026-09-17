# Semantic Model Reference

Generated from the same definition used for deployment. All data is synthetic.

Create an explicit Direct Lake model over these physical Warehouse tables; do not select the views.

## Members (dbo.report_members)

Columns: `member_ordinal`, `member_id`, `family_id`, `member_role`, `relationship`, `exception_count`, `source_segment`, `file_id`, `attempt_id`

### Member Count

```dax
Member Count = COUNTROWS('Members')
```
Format: `#,0`

### Subscribers

```dax
Subscribers = CALCULATE(COUNTROWS('Members'), 'Members'[member_role] = "Subscriber")
```
Format: `#,0`

### Dependents

```dax
Dependents = CALCULATE(COUNTROWS('Members'), 'Members'[member_role] = "Dependent")
```
Format: `#,0`

## Exceptions (dbo.report_exceptions)

Columns: `member_ordinal`, `rule_code`, `benefit`, `severity`, `source_segment`, `file_id`, `rule_version`, `attempt_id`

### Exception Count

```dax
Exception Count = COUNTROWS('Exceptions')
```
Format: `#,0`

### Affected Members

```dax
Affected Members = DISTINCTCOUNT('Exceptions'[member_ordinal])
```
Format: `#,0`

### Exception Member Rate

```dax
Exception Member Rate = DIVIDE([Affected Members], [Member Count])
```
Format: `0.0%`

## Health (dbo.report_health)

Columns: `file_name`, `file_id`, `attempt_id`, `rule_version`, `as_of_date`, `member_count`, `subscriber_count`, `dependent_count`, `coverage_count`, `exception_count`, `affected_members`, `parse_issue_count`, `publication_status`

### Source Members

```dax
Source Members = SUM('Health'[member_count])
```
Format: `#,0`

### Coverage Elections

```dax
Coverage Elections = SUM('Health'[coverage_count])
```
Format: `#,0`

### Parser Issues

```dax
Parser Issues = SUM('Health'[parse_issue_count])
```
Format: `#,0`

### Member Reconciliation Difference

```dax
Member Reconciliation Difference = [Source Members] - CALCULATE([Member Count], REMOVEFILTERS('Members'))
```
Format: `#,0`

## Relationships

Use single-direction filtering from the one side to the many side.

- `Members.member_ordinal` (one) to `Exceptions.member_ordinal` (many)
