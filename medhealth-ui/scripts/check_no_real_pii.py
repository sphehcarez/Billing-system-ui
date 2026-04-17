#!/usr/bin/env python3
"""Pre-commit hook: fail if any seed file contains a Luhn-valid 13-digit SA ID pattern."""
import re
import sys
from pathlib import Path

SA_ID_PATTERN = re.compile(r'\b(\d{13})\b')


def luhn_valid(number: str) -> bool:
    digits = [int(d) for d in number]
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def check_file(path: Path) -> list[str]:
    violations = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in SA_ID_PATTERN.finditer(text):
            candidate = match.group(1)
            if luhn_valid(candidate):
                line_no = text[:match.start()].count('\n') + 1
                violations.append(f"{path}:{line_no}: Luhn-valid 13-digit SA ID pattern: {candidate[:4]}XXXXXXXXX")
    except Exception:
        pass
    return violations


def main():
    seed_files = list(Path(".").rglob("*seed*.py")) + list(Path(".").rglob("*fixture*.py"))
    all_violations = []
    for f in seed_files:
        if ".git" not in str(f):
            all_violations.extend(check_file(f))

    if all_violations:
        print("ERROR: Potential real SA ID numbers found in seed files (POPIA risk):")
        for v in all_violations:
            print(f"  {v}")
        sys.exit(1)

    print(f"OK: Checked {len(seed_files)} seed files — no Luhn-valid SA ID patterns found.")


if __name__ == "__main__":
    main()
