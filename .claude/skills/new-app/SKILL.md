---
name: new-app
description: Scaffold a new browser app in pages/ for GitHub Pages, styled like the hub and the WellView configurator, add its app-card to index.html, and update the Pages workflow when the app links new files.
argument-hint: "<short name> [onepage | digitize | insight]"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(uv run *), Bash(git status*)
---

# /new-app

Arguments: `$ARGUMENTS`: a short name (e.g. `lasview`, `shaly-sand`) and the pphys
feature it serves: `onepage`, `digitize` or `insight`. Ask for anything missing,
plus a one-sentence purpose and the pphys class or function it front-ends.

## Conventions (from the existing pages)

- One self-contained file `pages/<feature>-<name>.html`: inline `<style>` and one
  inline `<script>`, vanilla JS, no frameworks, no CDN scripts or external stylesheets.
- Copy the `<head>` of `pages/onepage-wellview.html` (charset, viewport,
  `color-scheme: light`, `theme-color #1B6CA8`, the inline "T" SVG favicon,
  `<title>Name &middot; Thoth</title>`, meta description) and its `:root` tokens
  (`--blue #1B6CA8`, `--gold #C9A84C`, `--bg #FAF8F4`, `--surface`, `--text`,
  `--muted`, `--border`, `--field`, `--tint`, `--nav-h`), the nav (`.brand` linking to
  https://jshiriyev.github.io/, "Apps" linking to `../index.html`) and the footer.
- Keep its responsive rules (`@media (max-width: 720px)` and `480px`) and
  `prefers-reduced-motion`. No horizontal scroll at phone width.
- Escape anything read from a user file before it goes into `innerHTML`
  (the WellView page has an `esc()` helper; reuse it).
- An app that builds a payload for pphys documents the contract in a comment at the
  top of its script, like the WellView page (`API_BASE = ''` means console-only).
- Relative links only for repo files, so the page works both on Pages and from
  `uv run python -m http.server` at the repo root.

## Steps

1. Create the page from the conventions above, with the app's real first screen,
   not a placeholder.
2. In `index.html`, copy the existing `<article class="app-card card-surface">`
   inside `.grid` and fill in: icon emoji and tone class (`tone-<feature>`) on both
   `.app-icon` and `.badge`, `<h3>` title, `.app-sub` (`pphys.<module>.<Class>`),
   `.app-desc`, `href="pages/<file>.html"`, and the guide link (a `doc/*.md` on
   GitHub) or remove that link if there is no guide.
3. If the page links any repo file other than `index.html` and `pages/*.html`
   (sample data, images): add a `cp` line for it to the "Assemble the site" step of
   `.github/workflows/pages.yml` and its path to the workflow's `on.push.paths`.
4. Run `uv run python .claude/hooks/check_links.py`; it must report 0 broken links.
5. Tell the user how to try it: `uv run python -m http.server` at the repo root,
   then http://localhost:8000/pages/<file>.html. Offer to check it in the browser.
6. Add the app to the "Web apps" section of CLAUDE.md in one or two bullets.
