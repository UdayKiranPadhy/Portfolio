#!/usr/bin/env python3
"""
Interactive helper to add a new project. Inserts the static HTML card
into the right grid AND the projectDetails entry in one go, then creates
the screenshot folder.

Usage:
    python3 tools/add-project.py

You'll be prompted for: id, title, tagline, featured?, tags, links,
and the Problem/Approach/Solution/Impact modal narrative.

A stub architecture-diagram SVG is inserted; replace it manually later.
"""

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
IMAGES_DIR = ROOT / "assets" / "images" / "project"

# ---- Inline SVG constants (must match the ones already inlined in index.html) ----
GITHUB_SVG = (
    '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
    '<path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234'
    'c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 '
    '1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604'
    '-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176'
    ' 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552'
    ' 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807'
    ' 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086'
    ' 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>'
)
PLAY_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" '
    'stroke-linejoin="round" aria-hidden="true"><polygon points="5 3 19 12 5 21 5 3"/></svg>'
)
HF_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" '
    'stroke-linejoin="round" aria-hidden="true">'
    '<circle cx="12" cy="12" r="9"/>'
    '<path d="M8 14s1.5 2 4 2 4-2 4-2"/>'
    '<circle cx="9" cy="10" r="1" fill="currentColor"/>'
    '<circle cx="15" cy="10" r="1" fill="currentColor"/></svg>'
)
EXTERNAL_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" '
    'stroke-linejoin="round" aria-hidden="true">'
    '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>'
    '<polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>'
)
INFO_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" '
    'stroke-linejoin="round" aria-hidden="true">'
    '<circle cx="12" cy="12" r="10"/>'
    '<line x1="12" y1="16" x2="12" y2="12"/>'
    '<line x1="12" y1="8" x2="12.01" y2="8"/></svg>'
)
CHEVRON_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" '
    'stroke-linejoin="round" aria-hidden="true"><polyline points="9 18 15 12 9 6"/></svg>'
)
DIAGRAM_STUB = (
    '<svg viewBox="0 0 700 280" xmlns="http://www.w3.org/2000/svg">'
    '<rect width="700" height="280" rx="12" fill="var(--surface-hover)" stroke="var(--border-color)"/>'
    '<text x="350" y="145" text-anchor="middle" fill="var(--text-muted)" '
    'font-family="system-ui, sans-serif" font-size="20" font-weight="500">'
    'Architecture diagram TBD</text></svg>'
)


def pick_link_icon(label: str) -> str:
    lower = label.lower()
    if "github" in lower:
        return GITHUB_SVG
    if "live" in lower or "demo" in lower:
        return PLAY_SVG
    if "hf" in lower or "hugging" in lower:
        return HF_SVG
    return EXTERNAL_SVG


# ---- Prompt helpers ----
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


def prompt_bool(label, default=False):
    d = "Y/n" if default else "y/N"
    val = input(f"{label} [{d}]: ").strip().lower()
    if not val:
        return default
    return val in ("y", "yes")


def prompt_list(label, helper):
    val = input(f"{label} ({helper}): ").strip()
    return [v.strip() for v in val.split(",") if v.strip()]


def prompt_links():
    links = []
    print("\nLinks (label blank to stop):")
    while True:
        lbl = input(f"  Link {len(links) + 1} label: ").strip()
        if not lbl:
            break
        url = prompt("  URL", required=True)
        kind = input("  Kind (primary/secondary) [secondary]: ").strip() or "secondary"
        if kind not in ("primary", "secondary"):
            kind = "secondary"
        links.append({"label": lbl, "url": url, "kind": kind})
    return links


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
def esc_html(s: str) -> str:
    return html.escape(s, quote=True)


def esc_js_str(s: str) -> str:
    """Escape for embedding inside a single-quoted JS string."""
    return s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ").replace("\r", "")


# ---- Renderers ----
def render_card(data: dict) -> str:
    pid = data["id"]
    featured = data["featured"]
    card_class = "project-card-featured" if featured else "project-card-secondary"
    featured_pill = (
        '\n                        <span class="featured-pill type-animate">Featured</span>'
        if featured
        else ""
    )

    tag_chips = "\n                            ".join(
        f'<span class="skill-tag type-animate">{esc_html(t)}</span>' for t in data["tags"]
    )

    link_chips = ""
    for link in data["links"]:
        icon = pick_link_icon(link["label"])
        primary_cls = " primary" if link["kind"] == "primary" else ""
        link_chips += (
            f'\n                            <a class="card-action-chip{primary_cls}" '
            f'href="{esc_html(link["url"])}" target="_blank" rel="noopener noreferrer" '
            f'data-link-chip="1">\n'
            f"                                {icon}\n"
            f"                                <span>{esc_html(link['label'])}</span>\n"
            f"                            </a>"
        )

    return f"""                    <!-- {esc_html(data['title'])} ({'featured' if featured else 'secondary'}) -->
                    <div class="card animate-up project-card {card_class}" data-project-id="{pid}">{featured_pill}
                        <div class="project-link">
                            <span class="type-animate">{esc_html(data['title'])}</span>
                            {CHEVRON_SVG}
                        </div>
                        <p class="project-tagline"><span class="type-animate">{esc_html(data['tagline'])}</span></p>
                        <div class="skills-container">
                            {tag_chips}
                        </div>
                        <div class="card-actions">
                            <button class="card-action-chip primary" data-open-modal="{pid}" type="button">
                                {INFO_SVG}
                                <span>View Details</span>
                            </button>{link_chips}
                        </div>
                    </div>

"""


def render_js_entry(data: dict) -> str:
    pid = data["id"]

    def s(key):
        return esc_js_str(data.get(key, ""))

    tags_lines = ", ".join(f"'{esc_js_str(t)}'" for t in data["tags"])
    tags_str = f"[{tags_lines}]"

    if data["links"]:
        link_lines = ",\n                        ".join(
            f"{{ label: '{esc_js_str(l['label'])}', url: '{esc_js_str(l['url'])}', kind: '{l['kind']}' }}"
            for l in data["links"]
        )
        links_str = f"[\n                        {link_lines},\n                    ]"
    else:
        links_str = "[]"

    if data["perf"]:
        perf_lines = ",\n                        ".join(
            f"{{ v: '{esc_js_str(p['v'])}', l: '{esc_js_str(p['l'])}' }}"
            for p in data["perf"]
        )
        perf_str = f"[\n                        {perf_lines},\n                    ]"
    else:
        perf_str = "[]"

    return f"""                '{pid}': {{
                    title: '{s('title')}',
                    tagline: '{s('tagline')}',
                    tags: {tags_str},
                    links: {links_str},
                    problem: '{s('problem')}',
                    approach: '{s('approach')}',
                    solution: '{s('solution')}',
                    impact: '{s('impact')}',
                    perf: {perf_str},
                    heroDiagram: `{DIAGRAM_STUB}`,
                }},
"""


# ---- ID validation ----
ID_PATTERN = re.compile(r"^proj-[a-z0-9-]+$")


def validate_id(pid: str) -> str | None:
    if not ID_PATTERN.match(pid):
        return "id must look like 'proj-kebab-case-slug' (lowercase, hyphens)."
    return None


def insert_before_marker(text: str, marker: str, payload: str) -> str:
    """Insert payload as fresh lines immediately above the marker line.
    The marker's own leading indent is preserved; payload supplies its own indentation."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if marker in line:
            # payload may have a trailing newline; split into lines and drop empty trailing
            payload_lines = payload.rstrip("\n").split("\n")
            return "\n".join(lines[:i] + payload_lines + lines[i:])
    sys.exit(f"ERROR: marker '{marker}' not found in {INDEX.name}.")


def main():
    print("\nAdd a new project\n=================\n")

    pid = prompt("Project ID (e.g. proj-tutor-agent)", required=True, validator=validate_id)
    title = prompt("Title", required=True)
    tagline = prompt("Tagline (one-line hook)", required=True)
    featured = prompt_bool("Featured?", default=False)
    tags = prompt_list("Tags", "comma-separated, e.g. Python,FastAPI,React")
    links = prompt_links()

    print("\n--- Modal narrative (blank line to skip each section) ---")
    problem = prompt_multiline("Problem")
    approach = prompt_multiline("Approach")
    solution = prompt_multiline("Solution")
    impact = prompt_multiline("Impact")
    perf = prompt_perf()

    data = {
        "id": pid,
        "title": title,
        "tagline": tagline,
        "featured": featured,
        "tags": tags,
        "links": links,
        "problem": problem,
        "approach": approach,
        "solution": solution,
        "impact": impact,
        "perf": perf,
    }

    content = INDEX.read_text()

    if f'data-project-id="{pid}"' in content or f"'{pid}'" in content:
        sys.exit(f"\nERROR: a project with id '{pid}' already exists in index.html.")

    html_marker = (
        "<!-- gen:projects-featured-end -->"
        if featured
        else "<!-- gen:projects-secondary-end -->"
    )
    content = insert_before_marker(content, html_marker, render_card(data))
    content = insert_before_marker(content, "// gen:proj-details-end", render_js_entry(data))

    INDEX.write_text(content)

    folder = IMAGES_DIR / pid
    folder.mkdir(parents=True, exist_ok=True)

    print(f"\n✓ Inserted card into #projects-grid-{'featured' if featured else 'secondary'}")
    print(f"✓ Inserted projectDetails entry for '{pid}'")
    print(f"✓ Created {folder.relative_to(ROOT)}/")
    print("\nNext steps:")
    print(f"  1. Drop screenshots into {folder.relative_to(ROOT)}/")
    print("  2. Run: python3 tools/gen-manifest.py")
    print(f"  3. Edit the heroDiagram SVG in projectDetails['{pid}'] when ready")
    print("  4. Refresh the browser")


if __name__ == "__main__":
    main()
