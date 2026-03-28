# WT META Center

Analytics tool for War Thunder — META ratings, farm efficiency,
tech tree progression analysis and more.

**[→ Open app](https://ultra119.github.io/wt_meta_center/)**

---

## What it does

- **META Rating** — vehicle performance score based on WR, K/D, kills per spawn, weighted by role
- **BR Grid** — nation vs BR bracket heatmap
- **Lineup** — optimal farm lineup builder for a target BR
- **Tech Tree** — visual progression analyzer with MUST/SKIP/FILL verdicts per vehicle
- **Red Book** — vehicles with critically low play counts

## Data sources

- Vehicle statistics — community-aggregated gameplay data
- Vehicle characteristics, tech tree structure — [War Thunder Datamine](https://github.com/gszabi99/War-Thunder-Datamine)

> This project is not affiliated with or endorsed by Gaijin Entertainment.
> "War Thunder" is a trademark of Gaijin Entertainment.

## Local setup
```bash
# 1. Generate dataset
pip install -r requirements.txt
python build_data.py

# 2. Run frontend
cd frontend
npm install
npm run dev
```

## License

Code: [AGPL-3.0](LICENSE) 

Data in `dataset/` is not covered by this license — see LICENSE for details.
