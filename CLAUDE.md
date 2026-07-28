# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single wedding invitation site themed "The Killer" (Adrien & Séphora, 2026-08-01, Prieuré de Vernelle), doubling as a live-action party game. Static HTML/CSS/JS, no build tooling, no package.json. Deployed via GitHub Pages at `https://remy-v.github.io/the-killer-invitation/` — pushing to `main` deploys automatically.

There is no test suite, linter, or build step. "Running" the site means serving the folder statically and opening it in a browser:

```
python -m http.server 8000
```

then visit `http://localhost:8000/index.html` or `/missions.html`. After any edit, sanity-check the file instead of trusting the diff alone — these files are large (see below) and easy to leave with an unbalanced tag or brace:

```python
import html.parser
class Checker(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(); self.stack=[]; self.voids={'meta','link','br','img','input','hr'}
    def handle_starttag(self, tag, attrs):
        if tag not in self.voids: self.stack.append(tag)
    def handle_endtag(self, tag):
        if self.stack and self.stack[-1] == tag: self.stack.pop()
        else: print('mismatch at', tag)
c = Checker(); c.feed(open('index.html', encoding='utf-8').read()); print(c.stack)
```
(`data.split('<style>')[1].split('</style>')[0].count('{')` vs `.count('}')` for a quick CSS brace check.)

## Files that matter

- `index.html` — the invitation itself: hero title, a terminal-styled countdown to 2026-08-01T18:30:00+02:00, a "brief" section styled as an email from "Killer Inc." (the game rules), the invite block, and a hidden access form (double-click the title to reveal it; code `RELLIK` redirects to `missions.html`). Also has an ambient CSS-only background (drifting glow + heartbeat-rhythm flash on `body::before`/`::after`, gated by `prefers-reduced-motion`) and a sticky one-line header that fades in once the hero scrolls out of view.
- `missions.html` — the missions in a table (Junior/Confirmé/Senior columns, filterable by difficulty, plus an independent "Non distribué" checkbox that combines with the difficulty filter to show only unassigned missions). Mission count changes over time (missions get reworded/removed via direct edits to the static `<tr>` markup) and IDs are not contiguous (gaps exist, e.g. #75/#76 were deleted) — never assume `count == max(id)`, and never hardcode the mission count anywhere (check `hero__lead` text matches the actual row count after adding/removing a mission). Each row has a "Nom" field, `readonly` by default; double-clicking "Missions" + entering code `EEE` unlocks editing (remembered per-device via `localStorage`) and reveals a form to add new missions with chosen difficulty levels. Both the name assignments and any added missions are synced live across every visitor through jsonbin.io (see below) — this page has no build step either, the mission list is authored directly as static `<tr>` markup.
- `fonts.css` — the three typefaces (Nosifer for display, EB Garamond for serif/signature text, Courier Prime for "mail"/dispatch/data text) embedded as base64 `@font-face` data URIs, shared via `<link>` from both HTML files' `<head>`. This is why the file is ~165KB and why it's factored out instead of inlined per-page.
- `print/` — a standalone, **not linked from the live site**, business-card print sheet. `print/build_cards.py` reads the mission list straight out of `missions.html` (regex on `<span class="mission__text">`) and regenerates `print/cartes-killer.html`: 85×55mm cards, 2×5 per A4 page. **Recto** = mission text only, one card per mission, plus one extra fully-blank recto page at the end (for missions added after a print run — hand-write those). **Verso** = the fixed card-back rules styled like the site's mail section (De:/Objet: header, corner brackets matching recto), identical on every card, with the QR code (links to the live site) in its top-right corner sitting *behind* the mail header (`z-index` layering — see `.card__qr` / `.card__mailhead` in the generated CSS). Everything is black ink only (assumes red/colored card stock, where colored ink would be invisible — emphasis is done with bold, never color). Regenerate after any mission-list or rules-text change:
  ```
  python print/build_cards.py
  ```
  Print workflow: all RECTO pages first, flip the stack (orientation doesn't matter — every VERSO page is identical), then print VERSO on top.

  Two binary assets are committed alongside the script rather than fetched at build time:
  - `print/qr_b64.txt` — base64 PNG QR code pointing at `https://remy-v.github.io/the-killer-invitation/`. Regenerate only if that URL ever changes:
    ```powershell
    $u = "https://api.qrserver.com/v1/create-qr-code/?size=400x400&ecc=H&margin=0&data=" + [System.Uri]::EscapeDataString("https://remy-v.github.io/the-killer-invitation/")
    Invoke-WebRequest -Uri $u -OutFile qr.png -UseBasicParsing
    ```
    then base64-encode `qr.png` and overwrite `print/qr_b64.txt` with the raw base64 (no data-URI prefix).
  - `fonts.css` (from the repo root) is reused as-is for the print doc's typefaces — no separate font asset needed there. A calligraphic mission-text font (Dancing Script) was tried and reverted per user preference; don't reintroduce it without asking.

## jsonbin.io sync (missions.html)

`missions.html` talks directly to a jsonbin.io bin from client-side JS (no backend of our own — GitHub Pages is static-only, and this was the lightest option that didn't require exposing a GitHub token client-side). The bin ID and a scoped access key are inline in `missions.html`'s `<script>`. The key has `read`+`update` only (no `delete`/`create`), but jsonbin has no per-bin key scoping, so it technically grants access to every bin on that account — keep that account dedicated to this project.

Record shape:
```json
{
  "assignments": { "<mission id>": "<assigned name>" },
  "custom": [ { "id": 77, "text": "...", "junior": true, "confirme": false, "senior": true } ]
}
```
Every write does a read-merge-write (fetch `/latest`, patch one field, PUT the whole record back) to reduce — not eliminate — clobbering concurrent edits from other guests. That's an accepted tradeoff for a single-evening, low-stakes party game, not a general pattern to defend elsewhere.

## Keeping the Claude Artifact in sync

There's a published Claude Artifact mirroring **`index.html` only** (not `missions.html` — its RELLIK redirect would 404 inside the artifact's sandboxed preview since that's a single-file environment). The user expects it resynced after every `index.html` change. The Artifact tool requires body-only content (no `<!doctype>`/`<html>`/`<head>`/`<body>`) and can't fetch external files, so a plain `<link rel="stylesheet" href="fonts.css">` would 404 there — inline `fonts.css`'s contents directly into the extracted content before each republish:
```
sed -n '<body-open-line+1>,<script-close-line>p' index.html
```
prefixed with `<style>` + the full contents of `fonts.css` + `</style>`, then publish that combined file to the existing artifact URL (pass the same `url` each time so it updates in place rather than minting a new one).

## Environment quirk (this machine)

Avast's HTTPS scanning MITMs TLS locally; tools whose trust store doesn't include its injected root cert fail with certificate errors (git, curl, pip inside Git Bash all hit this). Fixed for git via `git config --global http.sslbackend schannel` (uses the Windows cert store, which trusts Avast). curl/pip in Git Bash still fail — use PowerShell (`Invoke-WebRequest`/`Invoke-RestMethod`, also backed by the OS trust store) for HTTPS calls when a Bash tool errors with `SSL: CERTIFICATE_VERIFY_FAILED` or similar. Worth checking for on a fresh machine too if the same antivirus is installed there.
