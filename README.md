# Uday Kiran Padhy — Portfolio

A single-file static portfolio. No build step, no framework — vanilla HTML + CSS + ES6 JS. The whole site is `index.html`; everything else is static assets.

## Stack

- HTML5, CSS3, vanilla ES6 (no transpilation, no bundler)
- Inline SVG architecture diagrams + a manifest-driven image carousel
- Designed to be served by any static file server (Live Server, `python -m http.server`, GitHub Pages, Netlify, S3+CloudFront, etc.)

## Features

- **Dark mode** with system preference + manual toggle, persisted to `localStorage` (key: `theme`)
- **Mobile-responsive nav** — desktop nav links, mobile shows current section name + theme toggle + hamburger drop-down
- **Pre-rendered project cards** so crawlers and no-JS users see content immediately; JS only attaches interactivity
- **Per-modal carousel** — architecture diagram on slide 0, screenshots on slides 1+. Click any slide to enlarge in a lightbox
- **URL routing for modals** — every modal updates the URL to `#detail-<id>` so links are shareable and the browser back button works
- **Accessibility** — `<h2>` section headings, `prefers-reduced-motion` skips animations, hidden text fallback for screen readers, `rel="noopener noreferrer"` on every external link
- **Animation tiers** — hero + About section use a typewriter effect; everything else fades in as it enters the viewport

## File structure

```
Portfolio/
├── index.html             ← the whole site lives here
├── README.md              ← this file
├── tools/                 ← authoring helpers (NOT runtime — index.html works standalone)
│   ├── add-project.py
│   ├── add-experience.py
│   └── gen-manifest.py
└── assets/
    └── images/
        ├── manifest.json  ← maps entry IDs → screenshot filenames + labels
        ├── project/
        │   ├── <project-id>/
        │   │   └── <screenshot>.{png,jpg,webp,svg,...}
        │   └── ...
        └── experience/
            ├── <experience-id>/
            │   └── <screenshot>.{png,jpg,webp,svg,...}
            └── ...
```

> The `tools/` scripts are **authoring helpers only** — they edit the static files in-place. The site has zero runtime dependency on them. You can deploy `index.html` + `assets/` without `tools/` and everything works.

## Local development

Any static server will do. Pick whichever is least friction:

```bash
# Python
python3 -m http.server 5500

# Node
npx serve

# Or VS Code Live Server extension (auto-reload on save)
```

Then open `http://localhost:5500/index.html`.

---

## Helper scripts (recommended path)

Three scripts in `tools/` automate the multi-file edits. They use Python 3 stdlib only — no `pip install` needed.

| Script | What it does | When you'd run it |
|---|---|---|
| `tools/add-project.py` | Prompts for project fields, inserts the static HTML card AND the `projectDetails` modal entry, creates the screenshot folder. | Adding a new project. |
| `tools/add-experience.py` | Adds a new bullet under an existing role, OR adds a whole new role. Auto-assigns the next free `exp{N}-{M}` ID. | Adding an experience bullet or role. |
| `tools/gen-manifest.py` | Scans `assets/images/{project,experience}/*/` and rewrites `assets/images/manifest.json`. Preserves hand-written labels; new files get an auto-derived label from the filename. | After dropping screenshots in a folder. |

### Workflow examples

**Add a new project:**
```bash
python3 tools/add-project.py
# fill in id, title, tagline, tags, links, modal narrative
# script creates the card + modal entry + screenshot folder
# drop screenshots into the new folder
python3 tools/gen-manifest.py
# refresh the browser
```

**Add a new experience bullet:**
```bash
python3 tools/add-experience.py
# pick "1) New bullet under existing role"
# pick which role (0 = Senior SWE, 1 = SWE, 2 = Associate SWE)
# fill in bullet text, modal title, problem/approach/solution/impact
```

**Add a new screenshot to an existing entry:**
```bash
cp ~/Downloads/new-screenshot.png assets/images/project/proj-aws-rl-env/
python3 tools/gen-manifest.py
# refresh the browser
```

### Filename → label convention

`gen-manifest.py` auto-derives labels from filenames. The rules:
- A leading `NN-` or `NN_` ordering prefix is stripped (e.g. `01-`, `02_`).
- `-` and `_` separators become spaces.
- Each word is capitalised.

| Filename | Auto-derived label |
|---|---|
| `live-playground.png` | "Live Playground" |
| `01-training_curve.webp` | "Training Curve" |
| `agent-run-timeline.svg` | "Agent Run Timeline" |

If you want a label that doesn't match this pattern, hand-edit it in `manifest.json` — `gen-manifest.py` preserves any label you've already written there.

### How the scripts find their insertion points

Each script edits two regions in `index.html`, located by HTML/JS marker comments:

| Marker | Used by | Section |
|---|---|---|
| `<!-- gen:projects-featured-end -->` | add-project.py | featured grid |
| `<!-- gen:projects-secondary-end -->` | add-project.py | secondary grid |
| `<!-- gen:exp0-end -->` / `exp1-end` / `exp2-end` | add-experience.py | bullet list for each role |
| `<!-- gen:experience-roles-end -->` | add-experience.py | end of the experience timeline (for adding new roles) |
| `// gen:exp-details-end` | add-experience.py | `const projectDetails = {...}` |
| `// gen:proj-details-end` | add-project.py | `Object.assign(projectDetails, {...})` |

Don't delete these markers. If you add a new role via the script, a fresh `<!-- gen:exp{N}-end -->` marker is inserted for it; update `KNOWN_ROLES` in `tools/add-experience.py` if you want bullets to be addable to that new role via the script.

---

## How to add content (manual — fallback if you don't want to use the scripts)

There are four operations you'll do most often. Each one tells you which file(s) to edit, the exact pattern to follow, and the gotchas.

> **ID convention.** Every "thing" in the portfolio is keyed by a stable, human-readable ID:
> - Experience bullets: `exp{role}-{bullet}` where role is 0 (Senior SWE), 1 (SWE), 2 (Associate). e.g. `exp0-3` is the 3rd bullet of the Senior SWE role.
> - Projects: `proj-<slug>`. e.g. `proj-aws-rl-env`, `proj-leetcode-companion`.
>
> The same ID is used for the HTML `data-detail-id` / `data-project-id`, the JS `projectDetails` entry, the screenshot folder (`assets/images/.../<id>/`), and the manifest key. Keep them in lockstep.

### 1. Add a new experience role

This is the biggest addition — a whole new job. Two HTML edits, no JS.

**Location:** `index.html`, the Experience section (~line 1919).

**Pattern:** roles are `<div class="timeline-item">` blocks in chronological order, most recent first. Copy the structure from an existing role:

```html
<!-- New Role Name -->
<div class="timeline-item animate-up">
    <div class="timeline-header">
        <h3 class="role-title type-animate">Your Role Title</h3>
        <span class="date-badge type-animate">Mon YYYY - Mon YYYY</span>
    </div>
    <a href="https://company.example.com" target="_blank" rel="noopener noreferrer">
        <div class="company-name type-animate">Company Name</div>
    </a>
    <ul class="bullet-list">
        <li data-detail-id="exp9-1"><span class="type-animate">First bullet text.</span></li>
        <li data-detail-id="exp9-2"><span class="type-animate">Second bullet text.</span></li>
    </ul>
</div>
```

**Important fields:**
- `data-detail-id="exp{role}-{N}"` — must be unique. If you're inserting between existing roles, pick a fresh role index (e.g., `exp3-N`). Don't reuse numbers.
- `target="_blank" rel="noopener noreferrer"` — always set both for external links (security).
- `class="type-animate"` on the inner span — wraps the text in the fade-in animation system. Don't omit it.

> **A bullet shown in the timeline is not the same as a bullet with a clickable modal.** Add `data-detail-id` only on bullets that should be clickable to open a modal. If you skip it, the bullet renders but won't have a chevron or open anything when clicked.

### 2. Add a new bullet to an existing experience role

Inside the existing role's `<ul class="bullet-list">`, append:

```html
<li data-detail-id="exp{role}-{next-N}"><span class="type-animate">Bullet text.</span></li>
```

Then (optionally) add a modal entry — see next section. If you don't add a modal entry, the bullet still appears in the timeline but won't have a chevron / won't open anything when clicked.

### 3. Add or update modal detail for an experience bullet

This is where the rich content lives — the Problem / Approach / Solution / Impact narrative, performance metrics, and architecture diagram you see when you click a bullet.

**Location:** `index.html`, the `const projectDetails = {...}` object (~line 2273).

**Pattern:** add or edit an entry keyed by the same `data-detail-id` you used in the HTML.

```js
'exp9-1': {
    title: 'Short title for the modal header',
    tagline: 'Optional one-liner shown under the title.',
    problem: 'What was broken / what was the gap.',
    approach: 'The shape of the solution you chose.',
    solution: 'Specifically what you built.',
    impact: 'Outcome / numbers / what changed.',
    perf: [
        { v: '120+',     l: 'Some Metric' },
        { v: '89%',      l: 'Another Metric' },
    ],
    heroDiagram: `<svg viewBox="0 0 700 280" xmlns="http://www.w3.org/2000/svg">
        <!-- inline SVG architecture diagram. Use var() colors so it adapts to dark mode -->
        <rect x="20" y="40" width="170" height="200" rx="12"
              fill="var(--diag-yellow-bg)" stroke="var(--diag-yellow-stroke)"/>
        <text x="105" y="65" fill="var(--text-strong)">Some Label</text>
        <!-- ... -->
    </svg>`,
}
```

**All fields are optional except `title`.** Skipping `problem` / `approach` / `solution` / `impact` means those sections won't render. Skipping `heroDiagram` means slide 0 of the carousel is omitted (the carousel will just show the screenshots, if any).

**Where to put it** — append it inside the `const projectDetails = {...}` object. The opening brace is at line ~2273. Match the existing indentation; keys are quoted strings.

> **Diagram colors.** Always use the CSS custom properties (`var(--diag-blue-bg)`, `var(--blue-accent)`, `var(--text-muted)`, etc.) instead of hex codes. The dark-mode override flips all of them automatically. Hex-coded SVGs will look harsh in dark mode.

### 4. Add a new project

Three edits: static HTML for the card, JS entry for the modal data, optional manifest entry for screenshots.

#### 4a. Static project card HTML

**Location:** `index.html`, inside `<div id="projects-grid-featured">` (~line 1793) for featured projects, or `<div id="projects-grid-secondary">` (~line 1869) for secondary ones.

**Pattern:** copy the structure of an existing card.

```html
<!-- New Project Title (featured or secondary) -->
<div class="card animate-up project-card project-card-{featured|secondary}"
     data-project-id="proj-your-slug">

    <!-- Only on featured cards -->
    <span class="featured-pill type-animate">Featured</span>

    <div class="project-link">
        <span class="type-animate">Your Project Title</span>
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round"
             stroke-linejoin="round" aria-hidden="true">
            <polyline points="9 18 15 12 9 6"/>
        </svg>
    </div>

    <p class="project-tagline">
        <span class="type-animate">One-line tagline that hooks the reader.</span>
    </p>

    <div class="skills-container">
        <span class="skill-tag type-animate">Python</span>
        <span class="skill-tag type-animate">FastAPI</span>
        <!-- ... -->
    </div>

    <div class="card-actions">
        <button class="card-action-chip primary" data-open-modal="proj-your-slug" type="button">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round"
                 stroke-linejoin="round" aria-hidden="true">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="16" x2="12" y2="12"/>
                <line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
            <span>View Details</span>
        </button>

        <!-- Optional external links -->
        <a class="card-action-chip primary" href="https://demo.example.com"
           target="_blank" rel="noopener noreferrer" data-link-chip="1">
            <!-- play icon for Live Demo -->
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round"
                 stroke-linejoin="round" aria-hidden="true">
                <polygon points="5 3 19 12 5 21 5 3"/>
            </svg>
            <span>Live Demo</span>
        </a>
        <a class="card-action-chip" href="https://github.com/you/repo"
           target="_blank" rel="noopener noreferrer" data-link-chip="1">
            <!-- github icon -->
            <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M12 0c-6.626 0-12 5.373-12 12 ... /* full GitHub mark path */"/>
            </svg>
            <span>GitHub</span>
        </a>
    </div>
</div>
```

**Critical attributes:**
- `data-project-id="proj-your-slug"` on the outer div — used by the click handler to find the modal entry
- `data-open-modal="proj-your-slug"` on the View Details button — must match the same slug
- `data-link-chip="1"` on every external `<a>` — tells the card-click handler "don't open the modal when this link is clicked"
- `target="_blank" rel="noopener noreferrer"` on every external link
- The chevron and icon SVGs are decorative — copy them as-is from any existing card

#### 4b. Modal entry in JS

**Location:** `index.html`, inside `Object.assign(projectDetails, {...})` (~line 2878). This is where project modals are appended to the projectDetails store, separate from the initial experience entries.

**Pattern:** same as the experience modal entry, with optional `links`, `tags`, and a longer `heroDiagram`.

```js
'proj-your-slug': {
    title: 'Your Project Title',
    tagline: 'One-line tagline (shown in the modal header too).',
    tags: ['Python', 'FastAPI', /* ... */],
    links: [
        { label: 'Live Demo', url: 'https://demo.example.com', kind: 'primary' },
        { label: 'GitHub',    url: 'https://github.com/you/repo', kind: 'secondary' },
    ],
    problem: '...',
    approach: '...',
    solution: '...',
    impact: '...',
    perf: [
        { v: 'X',    l: 'Label' },
        { v: 'Y%',   l: 'Label' },
    ],
    heroDiagram: `<svg viewBox="0 0 700 280">...</svg>`,
}
```

> **Why two places (HTML card + JS modal data)?** The card content (title, tagline, tags, link buttons) is what crawlers and no-JS users see — that's why it's pre-rendered as static HTML. The modal content is richer and JS-rendered. The card and the modal share the title/tagline/tags/links by design; if you change one, change the other.

### 5. Add screenshots to any entry

Two steps: drop the file, list it in the manifest.

#### 5a. Drop the file

Pick the entry ID (e.g., `proj-aws-rl-env` or `exp0-2`). Create the folder if it doesn't exist and drop your image:

```
assets/images/project/proj-your-slug/screenshot-1.png
assets/images/experience/exp0-2/retrieval-flow.webp
```

The folder must match the entry ID exactly. Supported formats: `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`, `.svg`. The carousel uses an `<img>` tag, so anything a browser can render in `<img>` will work.

#### 5b. Add an entry to `assets/images/manifest.json`

```json
{
  "proj-your-slug": [
    { "src": "screenshot-1.png", "label": "Main dashboard" },
    { "src": "screenshot-2.png", "label": "Settings page" }
  ],
  "exp0-2": [
    { "src": "retrieval-flow.webp", "label": "Retrieval flow diagram" }
  ]
}
```

- `src` is **relative** to the entry's folder — don't repeat the full path.
- `label` shows up in the carousel label pill and in the lightbox caption.
- Order in the array = order in the carousel (slide 1, 2, 3, …).

**Reload the page.** The screenshots replace the auto-generated `placehold.co` placeholders.

> **Entries not in the manifest still work** — they fall back to two generic `placehold.co` placeholder slides. Once you add the first manifest entry for a given ID, the placeholders are replaced entirely.

---

## How the carousel resolves images (data flow)

1. At page load, the JS runs `injectPlaceholderScreenshots()` — every projectDetails entry without its own `screenshots` field gets two `placehold.co` placeholder slides assigned.
2. Then `loadScreenshotManifest()` fetches `assets/images/manifest.json` asynchronously. For every entry listed there, it overrides the placeholders with `{ src: 'assets/images/<folder>/<id>/<file>', label }` objects.
3. When you click a card / bullet, `openModal(id)` builds a `slides` array: `[ heroDiagram-as-slide-0, ...screenshots ]`, and passes it to `renderCarousel()`.
4. The carousel injects the slides, wires prev/next/dots, and binds keyboard arrows + touch swipe.
5. Clicking a slide opens the lightbox with the same content scaled up.

If the manifest is missing or fetch fails, you get a `console.warn` and placeholders remain. The site never breaks.

---

## Theme + accessibility notes

- **Dark mode lives on `<html data-theme="dark">`.** Set on every load by a tiny inline script in `<head>` *before* any CSS paints. localStorage value `theme` (`light` or `dark`) overrides the system preference; delete the localStorage key to go back to "follow OS".
- **Diagrams must use CSS custom properties** (`var(--diag-blue-bg)`, `var(--blue-accent)`, etc.) not hex codes. The dark-mode override flips all of them.
- **`prefers-reduced-motion: reduce`** is respected — the typewriter and carousel slide transitions are skipped entirely, content reveals instantly.
- **`html.js-enabled`** is added by the inline head script. CSS rules that hide animated content (`opacity: 0` on `.type-animate`) are gated on this class, so no-JS users see everything.
- **Animation tiers**:
  - Hero h1/h2 → typewriter with cursor (existing `startHeroSequence()`)
  - Inside `#about` → typewriter, sequential queue (set by `.is-typewriter` class)
  - Everywhere else → simple opacity-fade up, parallel as elements enter the viewport (`.is-fade` class)

---

## URL routing

Every modal open pushes a history state and updates the URL to `#detail-<id>`:

- Sharing the URL takes the reader straight to that modal (`DOMContentLoaded` parses the hash and auto-opens).
- Browser back closes the modal.
- Closing the modal via X / outside-click / ESC calls `history.back()` so the hash clears.

Section anchors (`#about`, `#projects`, …) and modal anchors (`#detail-…`) live in separate namespaces — the smooth-scroll handler only fires for the former.

---

## Deployment

Drop the `Portfolio/` folder onto any static host. No build, no env vars, no secrets.

Examples:
- **GitHub Pages** — push the repo, point Pages at the root (or `/docs`).
- **Netlify** — drag-and-drop or git connect; no build command needed.
- **S3 + CloudFront** — upload everything as-is.

Make sure your host serves `.svg` with `image/svg+xml` and `.json` with `application/json` — both are standard so this only matters on custom servers.

---

## Conventions cheat sheet

| Thing | Convention |
|---|---|
| Experience bullet ID | `exp{0=senior\|1=swe\|2=associate}-{1-indexed}` |
| Project ID | `proj-<kebab-case-slug>` |
| Image folder | `assets/images/{project\|experience}/<id>/<file>` |
| Animation class on text | `class="type-animate"` (inside `<span>` if mid-sentence) |
| External link | always `target="_blank" rel="noopener noreferrer"` |
| Modal trigger button | `data-open-modal="<id>"` |
| Modal trigger bullet | `data-detail-id="<id>"` |
| External link chip | `data-link-chip="1"` (so card click skips it) |
| Diagram colors | `var(--diag-…)` / `var(--text-…)` / `var(--blue-accent)` — never hex |
