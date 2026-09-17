"""Write deterministic synthetic 005010X220A1 teaching fixtures in a bounded stream."""

import argparse
import json
from pathlib import Path


def member_segments(ordinal, adversarial=True):
    family_number = (ordinal + 1) // 2
    subscriber = ordinal % 2 == 1
    member_id = f"{'S' if subscriber else 'D'}{family_number:04d}"
    family_id = f"F{family_number:04d}"
    dob = "19800101" if subscriber else "20150101"
    ssn = f"9{ordinal:08d}"
    employee_id = f"EMP{family_number:06d}" if subscriber else ""
    medical, rx = "MED-A", "RX-A"
    if adversarial:
        if ordinal == 2:
            dob = "20010101"
        if ordinal == 4:
            medical, rx = "MED-B", "RX-B"
        if ordinal == 5:
            ssn, dob, employee_id = "", "", ""
        if ordinal == 7:
            rx = "RX-B"
        if ordinal == 9:
            medical = "UNKNOWN"
        if ordinal == 10:
            family_id = "F9999"
        if ordinal == 12:
            ssn = ""
        if ordinal == 13:
            member_id, family_id = "S0001", "F0001"
    segments = [f"INS*{'Y' if subscriber else 'N'}*{'18' if subscriber else '19'}*030*XN*A",
                f"REF*0F*{family_id}", f"REF*17*{member_id}"]
    if employee_id:
        segments.append(f"REF*ZZ*{employee_id}")
    name_segment = f"NM1*IL*1*SYNTHETIC*MEMBER{ordinal:06d}"
    segments.append(name_segment + (f"****34*{ssn}" if ssn else ""))
    if dob:
        segments.append(f"DMG*D8*{dob}*U")
    for benefit, plan in [("HLT", medical), ("PDG", rx)]:
        segments.extend([f"HD*030**{benefit}*{plan}*{'EMP' if subscriber else 'CHD'}",
                         "DTP*348*D8*20270101"])
    return segments


def generate(destination, members=13, element="*", terminator="~", adversarial=True):
    if members < 1 or members > 9999999:
        raise ValueError("Choose 1 through 9,999,999 total members")
    if len({element, terminator, ":", "^"}) != 4:
        raise ValueError("Element, segment, component and repetition delimiters must differ")
    destination.parent.mkdir(parents=True, exist_ok=True)
    header = ["ISA", "00", " " * 10, "00", " " * 10, "ZZ", "SYNTHSENDER".ljust(15),
              "ZZ", "SYNTHRECEIVER".ljust(15), "260916", "1200", "^", "00501", "000000001", "0", "T", ":"]
    with destination.open("w", encoding="ascii", newline="") as output:
        output.write(element.join(header) + terminator)
        output.write("GS*BE*SYNTHSENDER*SYNTHRECEIVER*20260916*1200*1*X*005010X220A1".replace("*", element) + terminator)
        transaction = ["ST*834*0001*005010X220A1", "BGN*00*SYNTHETIC-ONLY*20260916*1200",
                       "N1*P5*SYNTHETIC EMPLOYER*FI*900000001", "N1*IN*SYNTHETIC HEALTH PLAN*FI*900000002"]
        count = 0
        for segment in transaction:
            output.write(segment.replace("*", element) + terminator)
            count += 1
        for ordinal in range(1, members + 1):
            for segment in member_segments(ordinal, adversarial):
                output.write(segment.replace("*", element) + terminator)
                count += 1
        output.write(f"SE*{count + 1}*0001".replace("*", element) + terminator)
        output.write("GE*1*1".replace("*", element) + terminator)
        output.write("IEA*1*000000001".replace("*", element) + terminator)
    return {"file": destination.name, "total_members": members, "subscribers": (members + 1) // 2,
            "dependents": members // 2, "coverage_records": members * 2, "bytes": destination.stat().st_size,
            "synthetic_only": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--members", type=int, default=13)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "sample" / "synthetic_834.edi")
    parser.add_argument("--clean", action="store_true")
    arguments = parser.parse_args()
    print(json.dumps(generate(arguments.output, arguments.members, adversarial=not arguments.clean)))