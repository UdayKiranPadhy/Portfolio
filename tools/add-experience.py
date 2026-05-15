#!/usr/bin/env python3
"""
Interactive helper to add experience content. Two modes:

  1) Add a NEW BULLET to an existing role (most common).
     Inserts the <li> in the role's bullet-list AND the projectDetails entry.

  2) Add a NEW ROLE (job).
     Inserts a fresh <div class="timeline-item"> in the experience timeline.
     You can then run this script again in mode 1 to add bullets.

Usage:
    python3 tools/add-experience.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
IMAGES_DIR = ROOT / "assets" / "images" / "experience"

# Roles already defined in the HTML, in display order (most recent first)
KNOWN_ROLES = {
    "0": {"label": "Senior Software Engineer (Aug 2025 - Present)", "marker": "<!-- gen:exp0-end -->"},
    "1": {"label": "Software Engineer (Aug 2023 - Aug 2025)",       "marker": "<!-- gen:exp1-end -->"},
    "2": {"label": "Associate Software Engineer (Aug 2022 - Aug 2023)", "marker": "<!-- gen:exp2-end -->"},
}

DIAGRAM_STUB = (
    '<svg viewBox="0 0 700 280" xmlns="http://www.w3.org/2000/svg">'
    '<rect width="700" height="280" rx="12" fill="var(--surface-hover)" stroke="var(--border-color)"/>'
    '<text x="350" y="145" text-anchor="middle" fill="var(--text-muted)" '
    'font-family="system-ui, sans-serif" font-size="20" font-weight="500">'
    'Architecture diagram TBD</text></svg>'
)


# ---- Prompt helpers (same shape as add-project.py) ----
def prompt(label, default=None, required=False, validator=None):
    suffix = f" [{default}]" if default else (" *" if required else "")
    while True:
        try:
            val = input(f"{label}{suffix}: ").strip()
        except EOFError:
            val = ""
        if not val:
            if default is not None:
                val = default
            elif not required:
                return ""
            else:
                print("  required.")
                continue
        if validator:
            err = validator(val)
            if err:
                print(f"  {err}")
                continue
        return val


def prompt_multiline(label):
    print(f"{label} (end with an empty line):")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if not line:
            break
        lines.append(line)
    return " ".join(lines)


def prompt_choice(label, choices):
    print(f"{label}")
    for k, v in choices.items():
        print(f"  {k}) {v}")
    while True:
        val = input("> ").strip()
        if val in choices:
            return val
        print("  pick one of:", ", ".join(choices.keys()))


def prompt_perf():
    metrics = []
    print("\nPerformance metrics (value blank to stop):")
    while True:
        v = input(f"  Metric {len(metrics) + 1} value (e.g. '99%'): ").strip()
        if not v:
            break
        lbl = prompt("  Metric label", required=True)
        metrics.append({"v": v, "l": lbl})
    return metrics


# ---- Escaping ----
def esc_js_str(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ").replace("\r", "")


def esc_html(s: str) -> str:
    import html
    return html.escape(s, quote=True)


# ---- Insertion ----
def insert_before_marker(text: str, marker: str, payload: str) -> str:
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if marker in line:
            payload_lines = payload.rstrip("\n").split("\n")
            return "\n".join(lines[:i] + payload_lines + lines[i:])
    sys.exit(f"ERROR: marker '{marker}' not found in {INDEX.name}.")


# ---- Find next free bullet number for a role ----
def next_bullet_id(content: str, role_index: str) -> str:
    pattern = re.compile(rf'data-detail-id="exp{role_index}-(\d+)"')
    existing = [int(m.group(1)) for m in pattern.finditer(content)]
    n = max(existing) + 1 if existing else 1
    return f"exp{role_index}-{n}"


# ---- Bullet render ----
def render_bullet_html(bid: str, text: str) -> str:
    return f'                        <li data-detail-id="{bid}"><span class="type-animate">{esc_html(text)}</span></li>'


def render_bullet_js(bid: str, data: dict) -> str:
    def s(k):
        return esc_js_str(data.get(k, ""))

    if data["perf"]:
        perf_lines = ",\n                        ".join(
            f"{{ v: '{esc_js_str(p['v'])}', l: '{esc_js_str(p['l'])}' }}"
            for p in data["perf"]
        )
        perf_str = f"[\n                        {perf_lines},\n                    ]"
    else:
        perf_str = "[]"

    return f"""                '{bid}': {{
                    title: '{s('title')}',
                    problem: '{s('problem')}',
                    approach: '{s('approach')}',
                    solution: '{s('solution')}',
                    impact: '{s('impact')}',
                    perf: {perf_str},
                    heroDiagram: `{DIAGRAM_STUB}`,
                }},
"""


# ---- Role render ----
def next_role_index(content: str) -> str:
    """Roles use index 0 (most recent), 1, 2... Find the next free."""
    pattern = re.compile(r"<!-- gen:exp(\d+)-end -->")
    existing = [int(m.group(1)) for m in pattern.finditer(content)]
    n = (max(existing) + 1) if existing else 0
    return str(n)


def render_role_html(role_idx: str, data: dict) -> str:
    company_link = data.get("company_url", "").strip()
    link_open = (
        f'<a href="{esc_html(company_link)}" target="_blank" rel="noopener noreferrer">'
        if company_link
        else ""
    )
    link_close = "</a>" if company_link else ""

    return f"""
                <!-- {esc_html(data['title'])} -->
                <div class="timeline-item animate-up">
                    <div class="timeline-header">
                        <h3 class="role-title type-animate">{esc_html(data['title'])}</h3>
                        <span class="date-badge type-animate">{esc_html(data['dates'])}</span>
                    </div>
                    {link_open}
                        <div class="company-name type-animate">{esc_html(data['company'])}</div>
                    {link_close}
                    <ul class="bullet-list">
                        <!-- gen:exp{role_idx}-end -->
                    </ul>
                </div>
"""


# ---- Modes ----
def mode_add_bullet():
    content = INDEX.read_text()

    role = prompt_choice("\nWhich role does this bullet belong to?", {
        k: v["label"] for k, v in KNOWN_ROLES.items()
    })
    bid = next_bullet_id(content, role)
    print(f"\nAuto-assigned ID: {bid}")

    bullet_text = prompt_multiline("\nBullet text (the short line shown in the timeline)")
    if not bullet_text.strip():
        sys.exit("Bullet text is required.")

    print("\n--- Modal narrative ---")
    title = prompt("Modal title (e.g. 'Public API for Customer Integrations')", required=True)
    problem = prompt_multiline("Problem")
    approach = prompt_multiline("Approach")
    solution = prompt_multiline("Solution")
    impact = prompt_multiline("Impact")
    perf = prompt_perf()

    data = {
        "title": title,
        "problem": problem,
        "approach": approach,
        "solution": solution,
        "impact": impact,
        "perf": perf,
    }

    # Insert HTML bullet
    content = insert_before_marker(
        content, KNOWN_ROLES[role]["marker"], render_bullet_html(bid, bullet_text)
    )
    # Insert JS entry
    content = insert_before_marker(
        content, "// gen:exp-details-end", render_bullet_js(bid, data)
    )
    INDEX.write_text(content)

    # Create folder for screenshots
    folder = IMAGES_DIR / bid
    folder.mkdir(parents=True, exist_ok=True)

    print(f"\n✓ Inserted bullet (data-detail-id='{bid}')")
    print(f"✓ Inserted projectDetails['{bid}'] modal entry")
    print(f"✓ Created {folder.relative_to(ROOT)}/")
    print("\nNext steps:")
    print(f"  1. Drop screenshots into {folder.relative_to(ROOT)}/ if you have any")
    print("  2. Run: python3 tools/gen-manifest.py")
    print(f"  3. Edit the heroDiagram SVG in projectDetails['{bid}'] when ready")


def mode_add_role():
    content = INDEX.read_text()
    role_idx = next_role_index(content)
    print(f"\nNew role will get index 'exp{role_idx}' (the next free slot).")

    title = prompt("Role title (e.g. 'Staff Software Engineer')", required=True)
    dates = prompt("Date range (e.g. 'Aug 2026 - Present')", required=True)
    company = prompt("Company name", required=True)
    company_url = prompt("Company URL (optional)")

    data = {"title": title, "dates": dates, "company": company, "company_url": company_url}

    content = insert_before_marker(content, "<!-- gen:experience-roles-end -->", render_role_html(role_idx, data))
    INDEX.write_text(content)

    print(f"\n✓ Inserted new role (exp{role_idx})")
    print(f"✓ New marker <!-- gen:exp{role_idx}-end --> available for future bullets")
    print(f"\nNote: update KNOWN_ROLES in tools/add-experience.py to make exp{role_idx} pickable in bullet mode.")


def main():
    print("\nAdd experience content\n======================\n")
    mode = prompt_choice("What do you want to add?", {
        "1": "A new bullet under an existing role",
        "2": "A whole new role (job)",
    })
    if mode == "1":
        mode_add_bullet()
    else:
        mode_add_role()


if __name__ == "__main__":
    main()
