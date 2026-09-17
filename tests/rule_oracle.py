"""Small-fixture oracle only; the production-sized rule path runs in Warehouse SQL."""

from collections import Counter, defaultdict
from datetime import date


def evaluate(members, coverage, rules):
    as_of = date.fromisoformat(rules["as_of_date"])
    known_plans = {(plan["benefit"], plan["plan_id"]) for plan in rules["plans"]}
    allowed_pairs = {tuple(pair) for pair in rules["allowed_medical_rx_pairs"]}
    member_counts = Counter(member["member_id"] for member in members)
    families = defaultdict(list)
    active = defaultdict(lambda: defaultdict(list))
    for member in members:
        if member["is_subscriber"]:
            families[member["family_id"]].append(member)
    for election in coverage:
        if (election["effective_date"] and election["effective_date"] <= rules["as_of_date"]
                and (not election["end_date"] or election["end_date"] >= rules["as_of_date"])):
            active[election["member_ordinal"]][election["benefit"]].append(election)
    findings = set()
    for member in members:
        ordinal = member["member_ordinal"]

        def add(code, benefit=""):
            findings.add((ordinal, code, benefit))

        if member_counts[member["member_id"]] > 1:
            add("DUPLICATE_MEMBER")
        subscribers = families[member["family_id"]]
        if member["is_subscriber"] and len(subscribers) > 1:
            add("MULTIPLE_SUBSCRIBERS")
        if not member["is_subscriber"] and len(subscribers) != 1:
            add("ORPHAN_DEPENDENT" if not subscribers else "AMBIGUOUS_SUBSCRIBER")
        fields = rules["required_subscriber_fields"] if member["is_subscriber"] else rules["required_dependent_fields"]
        for field in fields:
            if not (member["has_ssn"] if field == "ssn" else member[field]):
                add(f"MISSING_{field.upper()}")
        if member["dob"]:
            birthday = date.fromisoformat(member["dob"])
            age = as_of.year - birthday.year - ((as_of.month, as_of.day) < (birthday.month, birthday.day))
            if birthday > as_of:
                add("FUTURE_DOB")
            if (not member["is_subscriber"] and member["relationship"] in rules["child_relationships"]
                    and member["relationship"] not in rules["exempt_relationships"] and age >= rules["child_age_limit"]):
                add("OVERAGE_DEPENDENT")
        for benefit, elections in active[ordinal].items():
            keys = [(entry["plan_id"], entry["effective_date"], entry["end_date"]) for entry in elections]
            if len(set(keys)) < len(keys):
                add("DUPLICATE_COVERAGE", benefit)
            if len(elections) > 1:
                add("AMBIGUOUS_COVERAGE", benefit)
            if any((benefit, entry["plan_id"]) not in known_plans for entry in elections):
                add("UNKNOWN_PLAN", benefit)
            if not member["is_subscriber"] and len(subscribers) == 1 and benefit in rules["comparable_benefits"]:
                parent = active[subscribers[0]["member_ordinal"]][benefit]
                if len(elections) == len(parent) == 1:
                    if ((benefit, elections[0]["plan_id"]) in known_plans and (benefit, parent[0]["plan_id"]) in known_plans
                            and elections[0]["plan_id"] != parent[0]["plan_id"]):
                        add("DEPENDENT_PLAN_DIFFERENCE", benefit)
                elif not parent:
                    add("SUBSCRIBER_COVERAGE_MISSING", benefit)
        medical = active[ordinal][rules["medical_benefit"]]
        rx = active[ordinal][rules["rx_benefit"]]
        if medical and not rx:
            add("RX_COVERAGE_MISSING")
        elif rx and not medical:
            add("MEDICAL_COVERAGE_MISSING")
        elif len(medical) == len(rx) == 1:
            pair = (medical[0]["plan_id"], rx[0]["plan_id"])
            if ((rules["medical_benefit"], pair[0]) in known_plans and (rules["rx_benefit"], pair[1]) in known_plans
                    and pair not in allowed_pairs):
                add("MEDICAL_RX_MISMATCH")
    return sorted(findings)