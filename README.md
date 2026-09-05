# research-city

**Live: [dipan010.github.io/research-city](https://dipan010.github.io/research-city/)**

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

[**Read the analysis →**](https://dipan010.github.io/research-city/bbmp-complaints-vs-spending/)

Reproducible end to end — `src/fetch.py` through `src/build_web.py` regenerates
every figure and the web page from the source files. `build_web.py` writes into
this repo's `docs/`, which is what GitHub Pages serves.

### [mumbai-slums-vs-amenities](mumbai-slums-vs-amenities/)

Overlays 2,541 Mumbai slum cluster polygons on ten of BMC's amenity layers, per
ward and per cluster, asking whether the densest and poorest settlements are
furthest from public services.

They are not: slum land is *closer* to every one of ten service types than the
rest of the city, and to a public toilet in 21 of 21 wards — because 51.5% of
Mumbai's toilet seats stand on 7.1% of its land. The deficit is real but
invisible to a distance measure; against Census 2011's public-latrine dependence
it is 14.0 households per seat. Also documents a disagreement between BMC's
published map layer and BMC's own RTI replies about the female share of seats.

[**Read the analysis →**](https://dipan010.github.io/research-city/mumbai-slums-vs-amenities/)

## Working notes

Research that preceded and framed the projects above:

- [opencity-background.md](opencity-background.md) — what OpenCity holds (1,098
  datasets) and how its data stories relate to it, from a full API sweep
- [project-ideas-blr-mum-kol.md](project-ideas-blr-mum-kol.md) — feasibility of
  cross-city work across Bengaluru, Mumbai and Kolkata
- [per-city-project-plan.md](per-city-project-plan.md) — the per-city plan both
  projects came out of

## Conventions

Each project is self-contained: its own `src/`, `data/`, virtualenv and README.
Raw data is never committed — fetch scripts pull it from source and record the
resolved URLs in a manifest, so any run can be traced to its snapshot.
