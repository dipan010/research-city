# research-city

Data research on Indian cities, built on public municipal data — chiefly the
[OpenCity](https://data.opencity.in) urban data portal (a programme of Oorvani
Foundation) and the government sources it republishes.

## Projects

### [bbmp-complaints-vs-spending](bbmp-complaints-vs-spending/)

Joins 618,202 Bengaluru citizen grievances to ₹23,241 crore of BBMP work orders
across the city's 198 wards, asking whether the wards that complain most are the
wards that get spent on.

Headline results: a third of BBMP's work-order spending is attributable to no
ward at all; complaint volume and spending point at different categories; and the
geography of both flips depending on whether you divide by area or by population.
Includes a correction to a published analysis, and a reusable BBMP ward-name
crosswalk that did not previously exist publicly.

Reproducible end to end — `src/fetch.py` through `src/build_web.py` regenerates
every figure and the web page from the source files.

## Working notes

Research that preceded and framed the project above:

- [opencity-background.md](opencity-background.md) — what OpenCity holds (1,098
  datasets) and how its data stories relate to it, from a full API sweep
- [project-ideas-blr-mum-kol.md](project-ideas-blr-mum-kol.md) — feasibility of
  cross-city work across Bengaluru, Mumbai and Kolkata
- [per-city-project-plan.md](per-city-project-plan.md) — the per-city plan the
  BBMP project came out of

## Conventions

Each project is self-contained: its own `src/`, `data/`, virtualenv and README.
Raw data is never committed — fetch scripts pull it from source and record the
resolved URLs in a manifest, so any run can be traced to its snapshot.
