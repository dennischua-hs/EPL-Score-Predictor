# EPL Score Predictor — Project Handoff

A brief to start a **fresh Claude Code session** for this app. Paste the contents of this file as
your first message in the new session, and attach `eplpredictor.html`, `proxy.py`, `proxy.js`, and
`start.command`.

---

## What this is
An **EPL (English Premier League) score prediction web app**. For every fixture in a chosen
gameweek it predicts the scoreline, result odds, and likely scorers — and for gameweeks that have
already been played it shows the actual results and grades the model's accuracy. It is a static HTML page
(inline CSS + JS, no framework, no build step) plus a tiny local proxy, because the data source
(the official Fantasy Premier League API) does not send CORS headers and cannot be called from the
browser directly.

**Deliverables — three files, all in this folder:**
- `eplpredictor.html` — the whole app (UI + model + rendering).
- `proxy.py` — zero-dependency Python 3 proxy + static server (**the one to run**; Node is not
  installed on the current machine).
- `proxy.js` — identical Node.js proxy, kept for environments that have Node.
- `start.command` — double-click launcher (macOS): starts the proxy if needed and opens the app.

## How to run
Easiest: **double-click `start.command`** in Finder (first time: right-click → Open to clear the
Gatekeeper warning). It starts the proxy and opens the app in your browser; keep its Terminal
window open, Ctrl+C or close it to stop.

Manually instead:
```bash
cd "<this folder>"
python3 proxy.py            # serves http://localhost:8080  (python3 proxy.py 9000 for another port)
```
Then open **http://localhost:8080/**. The refresh button re-fetches live data. (With Node instead:
`node proxy.js`.)

**Always open the app via http://localhost:8080/ — never by double-clicking the HTML file.** Opened
as a `file://` URL its `/fpl/…` calls can't reach the proxy and it shows a "couldn't reach the FPL
proxy" error.

## Confirmed design decisions (already made — don't re-ask)
- **App type:** auto predictor (the app predicts; the user does not guess).
- **Stack:** static single-page HTML/CSS/JS + a small local proxy. No framework, no npm, no build.
- **Data source:** the **official Fantasy Premier League API** (`fantasy.premierleague.com/api/…`),
  free, no key, no signup. Reached through the local proxy (see below).
- **Model:** expected goals from home/away attack & defence strength + recent form, then **10,000
  Monte-Carlo simulations per match** with a **Dixon-Coles** low-score adjustment (rho = -0.13).
  This simulation core is unchanged from the original TheSportsDB version.
- **Per-match outputs:** headline scoreline, result confidence %, derived odds (both teams to
  score, over 2.5, clean sheet each side, upset), **and the most likely scorers per team**.
- **Headline scoreline matches the predicted result:** the big score shown is the top *simulated
  scoreline consistent with* the most likely result (e.g. a predicted home win headlines 2-1, never
  an overall-modal 1-1 draw). The "other simulated scores" row still lists the next-most-likely
  scorelines overall. (This deliberately differs from a plain most-common-scoreline display, which
  can contradict the win/draw call.)
- **Gameweek selector:** the app lists **all 38 gameweeks** — past ones marked "(played)", the
  current one "(next)" — and defaults to the next gameweek. Shows every fixture in the selected
  gameweek (played and upcoming).
- **Past matches & accuracy:** for a finished fixture the card headlines the **actual final score**
  (labelled "final score") and grades the model's pre-match call inline (✓/✗, e.g. "✓ Model
  predicted Arsenal win (86%) · would-be score 3-0"). When a gameweek has finished games the status
  banner summarises accuracy: **results called right** (home/draw/away) and **exact scores** matched
  (against the would-be scoreline shown on the card).

## Why a proxy (important context)
The previous version used TheSportsDB's free tier, which is CORS-enabled and keyless but **truncates
the standings table to 5 teams** and returns very few upcoming fixtures — so most fixtures couldn't
be rated. We switched to the FPL API (full 20 teams, all 380 fixtures, plus per-player data). FPL
does **not** send CORS headers, so a browser `fetch` from the page is blocked. `proxy.py` / `proxy.js`
solve this by serving the page and relaying only two allowlisted FPL endpoints with a CORS header
added — same origin, no open relay.

## Proxy endpoints
The page fetches these **relative** paths (same origin as the proxy):
- `GET /fpl/bootstrap` → relays `https://fantasy.premierleague.com/api/bootstrap-static/`
  (teams with 1–5 strength tiers; `elements` = all players with form, xG, goals, availability).
- `GET /fpl/fixtures` → relays `https://fantasy.premierleague.com/api/fixtures/`
  (all 380 fixtures: `event` = gameweek, `kickoff_time`, `team_h`/`team_a`, scores, `finished`).
- Everything else is served as a static file from the app folder (`/` → `eplpredictor.html`).

## How the code is structured (inside `eplpredictor.html`'s `<script>`)
- `buildStrengthsFPL(teamsArr, finished)` — per-team attack/defence. Uses real goals for/against
  once ~2 rounds are played (`goalsMode`, total finished ≥ 40); before that falls back to FPL's 1–5
  `strength_overall_home/away` tiers so early-season predictions still work.
- `topScorers(playersOfTeam, teamGoals)` — likely scorers as **anytime-scorer probabilities**:
  players ranked by a form-weighted attacking index (form + xG/90 + goals), each given a share of
  the team's predicted goals, then `P(scores) = 1 - e^(-share * teamGoals)`.
- `buildForm(finished)` — recent-form multiplier per team (last 5 finished games, newest first).
- `dcMatrix(lh, la, rho)` / `dcTau(...)` — Dixon-Coles adjusted scoreline probability grid.
- `mulberry32(seed)` / `hashStr(str)` — seeded RNG (seeded per fixture id) so results are stable
  across refreshes.
- `simulate(cells, rng, N)` — draws N=10,000 scorelines, tallies W/D/A + derived odds. Returns the
  full `ranked` array of scorelines (most likely first) so the card can pick a result-matching one.
- `predict(...)` — computes expected goals, runs the sim, returns everything (incl. `ranked`).
- `fixtureCard(ev, pr)` — renders one card. Picks the predicted result (max of pHome/pDraw/pAway),
  then headlines the first entry of `pr.ranked` that matches that result; reads `pr.scHome`/
  `pr.scAway` for the scorers block. If `pr.actual` is set (a finished match), it headlines that
  actual score instead and shows the ✓/✗ pre-match grade.
- `allGameweeks()` / `nextGameweek(gws)` / `gwIsPlayed(g)` — build the gameweek list, find the
  default (first gameweek with an unplayed fixture), and label played ones.
- `renderGW(gw)` — renders every fixture in the gameweek; attaches `pr.actual` for finished ones,
  tallies result/exact-score accuracy, and writes the accuracy summary into the status banner.
- `loadAll()` / `init()` — data-loading flow + selector population (defaults to the next gameweek).
- Crests: `CREST(code)` → `resources.premierleague.com/premierleague/badges/70/t{code}.png`.
- Constants at the top of the script: `HOME_ADV`, `AWAY_ADJ`, `FORM_N`, `FORM_MAX`, `SIMS`,
  `DC_RHO`, `TIER_SPREAD` (tier→goals multiplier), `N_SCORERS` (scorers shown per team).

## Current state / known good
- Verified live end-to-end through the proxy: 20 teams, all 380 fixtures, 38 gameweeks in the
  selector, 10 cards for a full round, scorers rendering (e.g. Saka/Ødegaard for Arsenal), no
  console errors. Kickoff times are localised to the viewer's timezone. Played gameweeks show final
  scores + an accuracy summary (verified: a completed round graded 8/10 results, 2 exact scores).
- Early-season handling is solid: with no results yet, ratings come from FPL strength tiers and a
  status banner explains it; the old "blank page at season start" bug is gone.
- Styling is a warm **dark** theme with a red accent (Playfair Display + DM Sans fonts). The whole
  palette is defined as CSS variables on `:root`; there is no light-mode toggle. The old "HOPE"
  logo has been removed from the header.
- Includes a "for fun, not betting advice" disclaimer.

## Notes / constraints for the new session
- **The proxy must be running** or the page shows a clear "couldn't reach the FPL proxy" error.
- If the environment's network policy blocks `fantasy.premierleague.com`, the proxy relay will fail;
  test on a normal network.
- No personal data is involved (public football data only).
- The proxy is deliberately minimal and safe (only two allowlisted upstream paths, path-traversal
  guarded static serving). If deploying beyond localhost, put it behind a real host.

## Possible next steps (ideas, not committed)
- Gameweek aggregate table: simulate the whole round and show expected points per team.
- Cache FPL responses in `localStorage` (proxy already sends a short `max-age`) for quicker reloads.
- Let the user tweak model constants (home advantage, form weight, rho, tier spread) from the UI.
- Deploy the proxy as a Cloudflare Worker / Vercel function for a shareable public URL, so the app
  isn't tied to a local machine.
- Richer scorer model once the season progresses and FPL's detailed attack/defence ratings populate
  (they are 0 at season start).

## Starter prompt for the new session
> I have an EPL score prediction app: a static `eplpredictor.html` (HTML/CSS/JS, 10,000 Monte-Carlo
> sims per match with a Dixon-Coles adjustment) that reads the official Fantasy Premier League API
> through a tiny local proxy (`proxy.py`, or `proxy.js` for Node). It shows predicted scorelines,
> odds, and likely scorers per gameweek. Here are the files — help me continue working on it.
> Run it with `python3 proxy.py` then open http://localhost:8080/. [attach the three files]
