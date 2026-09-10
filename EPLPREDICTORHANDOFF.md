# EPL Score Predictor — Project Handoff

A brief to start a **fresh Claude Code session** for this app. Paste the contents of this file as
your first message in the new session, and attach `index.html` (plus `README.md` for the hosting
setup if relevant).

---

## What this is
An **EPL (English Premier League) score prediction web app**. For every fixture in a chosen
gameweek it predicts the scoreline, result odds, and likely scorers — and for gameweeks already
played it shows the actual results and grades the model's accuracy. It is a single static HTML page
(inline CSS + JS, no framework, no build step).

The data source is the official **Fantasy Premier League API**, which does **not** send CORS headers
and cannot be called from a browser directly. Instead of a live proxy, a scheduled **GitHub Action**
saves two FPL snapshots into `data/*.json`, and the page reads those static files (same origin, no
CORS problem). Deployed on **GitHub Pages**.

**Deliverables (all in this folder / repo):**
- `index.html` — the whole app (UI + model + rendering). Reads `data/bootstrap.json` and
  `data/fixtures.json`.
- `data/bootstrap.json`, `data/fixtures.json` — FPL snapshots, auto-refreshed by the Action.
- `.github/workflows/update-data.yml` — GitHub Action; refreshes the snapshots every 3 hours
  (also on manual "Run workflow" and on push).
- `README.md` — end-user hosting/setup steps.
- `proxy.py` / `proxy.js` — optional zero-dependency local static server, for previewing only.
- `start.command` — optional macOS double-click launcher for local preview.

## Hosting (production)
Deployed via **GitHub Pages** from the repo's `main` branch (root). Live under
`https://<username>.github.io/<repo-name>/`. Setup steps are in `README.md`:
1. Push the folder to a public GitHub repo (`main`).
2. Settings → Pages → Deploy from a branch → `main` / root.
3. Settings → Actions → General → Workflow permissions → **Read and write** (so the Action can
   commit refreshed data).
4. Actions tab → "Update FPL data" → Run workflow once to seed fresh data.

Data freshness = the Action's schedule (every 3 hours), **not** live per-visit — fine for a
predictor. The `data/*.json` are committed to the repo, so the site works even before the Action's
first run.

Note: the `<username>.github.io` host is fixed on free GitHub Pages; only the repo-name path is
editable (rename the repo), or attach a custom domain. Current repo:
`https://github.com/dennischua-hs/EPL-Score-Predictor`.

## Preview locally (optional)
The page must be served over http (not opened as `file://`), because browsers block `fetch` of
local files. Run `python3 proxy.py` (or double-click `start.command`) → open http://localhost:8080/.
If `data/*.json` are missing locally, run the Action once or fetch them manually (see README).

## Confirmed design decisions (already made — don't re-ask)
- **App type:** auto predictor (the app predicts; the user does not guess).
- **Stack:** single static HTML/CSS/JS page + static JSON data. No framework, no npm, no build, no
  live server in production.
- **Data source:** the **official Fantasy Premier League API** (`fantasy.premierleague.com/api/…`),
  free, no key, no signup — snapshotted into `data/*.json` by the GitHub Action.
- **Model:** expected goals from home/away attack & defence strength + recent form, then **10,000
  Monte-Carlo simulations per match** with a **Dixon-Coles** low-score adjustment (rho = -0.13).
- **Per-match outputs:** headline scoreline, result confidence %, derived odds (both teams to
  score, over 2.5, clean sheet each side, upset), **and the most likely scorers per team**.
- **Headline scoreline matches the predicted result:** the big score shown is the top *simulated
  scoreline consistent with* the most likely result (e.g. a predicted home win headlines 2-1, never
  an overall-modal 1-1 draw). The "other simulated scores" row still lists the next-most-likely
  scorelines overall.
- **Gameweek selector:** lists **all 38 gameweeks** — past ones marked "(played)", the current one
  "(next)" — defaults to the next gameweek. Shows every fixture in the selected gameweek.
- **Past matches & accuracy:** for a finished fixture the card headlines the **actual final score**
  ("final score") and grades the model's pre-match call inline (✓/✗, e.g. "✓ Model predicted Arsenal
  win (86%) · would-be score 3-0"). When a gameweek has finished games the status banner summarises
  accuracy: **results called right** (home/draw/away) and **exact scores** matched.

## Data endpoints / shapes
The Action fetches and stores:
- `data/bootstrap.json` ← `https://fantasy.premierleague.com/api/bootstrap-static/`
  (`teams` with 1–5 `strength_overall_home/away` tiers and `code` for crests; `elements` = all
  players with `form`, `expected_goals_per_90`, `goals_scored`, `minutes`, `status`, `element_type`).
- `data/fixtures.json` ← `https://fantasy.premierleague.com/api/fixtures/`
  (all 380 fixtures: `event` = gameweek, `kickoff_time`, `team_h`/`team_a`, `team_h_score`/
  `team_a_score`, `finished`).
The page reads them via the relative paths `data/bootstrap.json` / `data/fixtures.json`
(constants `DATA_BOOT` / `DATA_FIX` near the top of the script).

## How the code is structured (inside `index.html`'s `<script>`)
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
- `fetchData()` — loads `DATA_BOOT` / `DATA_FIX`; `loadAll()` / `init()` — data-loading flow +
  selector population (defaults to the next gameweek).
- Crests: `CREST(code)` → `resources.premierleague.com/premierleague/badges/70/t{code}.png`.
- Constants at the top of the script: `HOME_ADV`, `AWAY_ADJ`, `FORM_N`, `FORM_MAX`, `SIMS`,
  `DC_RHO`, `TIER_SPREAD` (tier→goals multiplier), `N_SCORERS` (scorers shown per team).

## Current state / known good
- Verified end-to-end reading the static data files: 20 teams, all 380 fixtures, 38 gameweeks in the
  selector, 10 cards for a full round, scorers rendering, no console errors. Kickoff times localised
  to the viewer's timezone. Played gameweeks show final scores + an accuracy summary (verified: a
  completed round graded 8/10 results, 2 exact scores).
- Repo verified live: `index.html`, `data/bootstrap.json` (20 teams / 612 players),
  `data/fixtures.json` (380 fixtures), and the workflow file are all present and valid on `main`.
- Early-season handling is solid: with no results yet, ratings come from FPL strength tiers and a
  status banner explains it.
- Styling is a warm **dark** theme with a red accent (Playfair Display + DM Sans fonts); palette in
  CSS variables on `:root`, no light-mode toggle. No "HOPE" logo; page `<title>` is "EPL Score
  Predictor".
- Includes a "for fun, not betting advice" disclaimer.

## Notes / constraints for the new session
- **Production has no server** — data is static JSON refreshed by the Action. To change the refresh
  cadence, edit the cron in `.github/workflows/update-data.yml`.
- Locally, the page must be served over http (use `proxy.py`), not opened as a `file://`.
- If GitHub blocks or the FPL endpoints change, the Action's fetch step fails and the JSON goes
  stale; the page keeps showing the last committed snapshot.
- No personal data is involved (public football data only).

## Possible next steps (ideas, not committed)
- Gameweek aggregate table: simulate the whole round and show expected points per team.
- Cache the JSON in `localStorage` for instant reloads / brief offline use.
- Let the user tweak model constants (home advantage, form weight, rho, tier spread) from the UI.
- Custom domain on GitHub Pages for a cleaner URL (Settings → Pages → Custom domain).
- Richer scorer model once FPL's detailed attack/defence ratings populate later in the season.

## Starter prompt for the new session
> I have an EPL score prediction app: a single static `index.html` (HTML/CSS/JS, 10,000 Monte-Carlo
> sims per match with a Dixon-Coles adjustment). It reads two static FPL snapshots
> (`data/bootstrap.json`, `data/fixtures.json`) that a GitHub Action refreshes every few hours, and
> it's hosted on GitHub Pages. It shows predicted scorelines, odds, likely scorers, and — for played
> gameweeks — actual results with the model's accuracy. Here are the files — help me continue.
> Preview locally with `python3 proxy.py` then open http://localhost:8080/. [attach index.html]
