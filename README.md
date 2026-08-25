# EPL Score Predictor

A single-page Premier League score predictor: every fixture in a gameweek is run through 10,000
Monte-Carlo simulations (Dixon-Coles adjusted) built from team strength and recent form, giving a
predicted scoreline, result odds, likely scorers, and — for played gameweeks — the actual result
with the model's accuracy.

Data comes from the official **Fantasy Premier League API**. Because that API can't be called from a
browser (no CORS), a scheduled **GitHub Action** saves it into `data/*.json` and the page reads those
static files.

## Files
- `index.html` — the whole app (UI + model + rendering).
- `data/bootstrap.json`, `data/fixtures.json` — FPL snapshots (auto-refreshed).
- `.github/workflows/update-data.yml` — Action that refreshes the snapshots every 3 hours.
- `proxy.py` / `proxy.js` — optional local static server for previewing (see below).
- `start.command` — double-click launcher for local preview (macOS).

## Publish it (GitHub Pages) — one-time setup
1. Create a new GitHub repo and push these files to the `main` branch.
2. In the repo: **Settings → Pages → Build and deployment → Source: Deploy from a branch**, pick
   **`main`** / **`/ (root)`**, Save.
3. In **Settings → Actions → General → Workflow permissions**, choose **Read and write
   permissions** (lets the Action commit refreshed data), Save.
4. Go to the **Actions** tab → **Update FPL data** → **Run workflow** once to seed fresh data.
5. Your link: **`https://<your-username>.github.io/<repo-name>/`** — share that.

From then on the data refreshes automatically every 3 hours; you can also hit **Run workflow**
anytime for an immediate update.

## Preview locally (optional)
The page must be served over http (not opened as a `file://`), because browsers block `fetch` of
local files. Easiest:

```bash
python3 proxy.py         # then open http://localhost:8080/
```

Or double-click `start.command` (macOS). If `data/*.json` are missing locally, run the GitHub Action
once, or fetch them manually:

```bash
mkdir -p data
curl -sfL -A "Mozilla/5.0" "https://fantasy.premierleague.com/api/bootstrap-static/" -o data/bootstrap.json
curl -sfL -A "Mozilla/5.0" "https://fantasy.premierleague.com/api/fixtures/" -o data/fixtures.json
```

## Notes
- For fun and interest only — not betting advice.
- Data freshness = the Action's schedule (every 3 hours), not live per-visit.
