# Kolkata's ponds, ward by ward

Chapter three of three, after `bbmp-complaints-vs-spending` (Bengaluru) and
`mumbai-slums-vs-amenities` (Mumbai). Same method, ward-level civic equity;
different data, and a deliberately smaller scope.

**Page:** [`docs/kolkata-water-bodies/`](../docs/kolkata-water-bodies/)

India's first water bodies census enumerated **3,051 ponds and tanks inside the
Kolkata Municipal Corporation**, covering 1,175 hectares. This reads that census
ward by ward, which nobody appears to have done, and reports what KMC's other
published data does and does not support.

## What it found

| | |
|---|---|
| Water bodies inside KMC | **3,051**, covering **1,175 ha** |
| Wards holding any | **93 of 144**; 51 hold none |
| Concentration | Gini **0.804** on counts; the top 20 wards hold **74.2%** |
| Ward 108 and ward 58 | **54.5%** of the city's entire water surface |
| Ownership | **92.5% private**; KMC owns **228 (7.5%)** |
| In Boroughs XIII-XVI | 45.6% of the city's water bodies, KMC owns **1.4%** of them |
| Recorded not in use | **906 (29.7%)** |
| Boroughs XIV and XV | 22.5% of the stock, **39.7%** of every disused water body |
| Disuse gradient | east-west, rho **-0.35** (p = 0.015, n = 47, 5% critical 0.29) |

Three results were tested and are reported as **nulls**: municipal ownership does
not predict lower disuse at ward level; pond-rich wards are not more disused once
the share rests on more than a couple of records; and the water-body-level
chi-square on ownership against use is an artifact of treating 3,051 clustered
points as independent.

Two census fields are **dead** and no figure is published from either:
`waterbody_encroached` reads `No` for all 3,051 records, and `water_body_nature`
reads `Man-made` for all 3,051. The encroachment field especially: the census
collects it nationally, so a column with no variance in a city with a litigated
pond-filling history is evidence it was never filled in.

## What Kolkata's data does not support

The project began as ward-level amenity access, in the shape of the Mumbai
chapter. Most of that turned out to be unanswerable, which is itself reportable.

- **Ward-level spending: no.** KMC's budgets are consolidated across all sixteen
  boroughs. One line item is ward-attributed, the Councillors' Elaka Unnayan
  Prakalpa, and it allocates an identical ₹15.00 lakh to each of the 144 wards
  (₹12.50 lakh in 2019-20 and 2021-22). That is ₹21.6 crore against ₹5,639.56
  crore of budgeted expenditure: **0.38% of the budget, flat by design.** There is
  no KMC equivalent of BBMP's work-order archive to analyse.
- **Drainage networks: no.** `Kolkata Drainage Maps` is 80 scanned PDFs covering
  80 of 144 wards. Reading it as data is a digitisation project.
- **Amenity access: no.** Only five of the fourteen KMC amenity tables carry a
  ward column, and they cover 127, 106, 55, 53 and 21 of the 144 wards. With 91
  wards absent from the parks table there is no way to separate a real zero from
  a registry gap, and the gap will not be randomly distributed. (Fourteen counts
  the amenity resources across the five amenity datasets, excluding the three
  administrative tables: KMC Departments, Borough Committees Office and the
  e-Kolkata service centres. One of the fourteen is the duplicate below.)
- **`KMC Pay-and-use Toilets (2018)` is a byte-identical copy of `KMC Schools`**
  (MD5 `1c0ce93ca1f54407777bcec4ea582c8e`). Kolkata publishes no public toilet
  data at all. `src/fetch.py` re-verifies this on every run, so a corrected upload
  will show up as a corrected finding.

## Traps this project had to defuse

- **The ward KML is the pre-2015 boundary set.** It holds 141 placemarks and is
  named "Kolkata Wards Map 2022". KMC has had 144 wards since the 2015 poll, when
  the Joka area was annexed. The 2010 election file has exactly 141 wards, the
  2015 file exactly 144. **68 water bodies sit in wards 142-144, which have no
  polygon**, so the panel is keyed on the census's own ward label rather than on
  geometry. The two orderings agree at rho 0.93.
- **The boundary caveat.** Kolkata district is smaller than KMC's jurisdiction.
  Nothing here uses a district-sourced denominator; elector counts come from KMC's
  own 2015 election returns for exactly that reason.
- **The 51 empty wards are real.** This decides whether the analysis has 144 units
  or 93, so it was tested: enumerators recorded ponds down to 0.02 ha inside the
  dense old-city core, at a higher small-pond share than the middle band, so no
  size threshold was suppressing them. Zeros are carried, and every concentration
  figure is also reported on the 93-ward restriction.
- **It is not the East Kolkata Wetlands.** 1,175 ha against the Ramsar site's
  ~12,500, a largest single body of 38.93 ha, and an easternmost record at 88.458 E
  where KMC stops. The framing was tested before the writing started.
- **Vintages are mislabelled in both directions.** The ward file is named 2022 and
  is pre-2015; the water bodies file is described as 2018-19, named 2023, and its
  own `enumeration_date` timestamps put fieldwork in November 2020 to November 2021.

## A small artifact worth reusing

`data/out/borough_ward_crosswalk.csv` maps all 16 KMC boroughs to all 144 wards,
two columns, checked to partition 1-144 exactly once. KMC publishes this only as
a free-text column (`123,124,125,126,142,143 &144`) inside an office-address
table, and it is the only way to place the borough-only amenity registries. No
published version appears to exist.

## Prior work

Mohit Ray, *Water bodies of Kolkata* (Centre for Science and Environment) is the
standing reference. It records KMC's own pond counts of 1,786 (1997) and 3,873
(2006) against NATMO's 8,731 and 4,889 counted from satellite imagery, and argues
roughly 44% were filled in over two decades. That argument is already published
and is not restated here as a new finding. This page extends the record by reading
the national census ward by ward. The gap between 3,051 and 8,731 is treated as a
question about what four different instruments were measuring, not as a loss
estimate.

## Running it

```
uv venv .venv && uv pip install --python .venv/bin/python \
    pandas geopandas shapely matplotlib scipy requests
cd src
../.venv/bin/python fetch.py          # resolve + download from CKAN, verify the duplicate
../.venv/bin/python build_panel.py    # spatial + attribute join, 144-ward panel
../.venv/bin/python analyse.py        # every number the page quotes -> results.json
../.venv/bin/python robustness.py     # seven judgement calls, bounded
../.venv/bin/python make_figures.py   # figures/
../.venv/bin/python export_web.py     # ward SVG paths + points -> web_data.json
../.venv/bin/python build_web.py      # -> ../../docs/kolkata-water-bodies/
```

`src/kolkata.py` holds the shared loaders. `web/template.html` is the page source;
`docs/kolkata-water-bodies/index.html` is generated, so edit the template.

## Layout

```
src/kolkata.py       KML parsing, ward identity, borough and elector loaders
src/fetch.py         CKAN resolution by title + resource name, duplicate check
src/build_panel.py   join, agreement report, 144-ward panel
src/analyse.py       results.json - descriptives, the one gradient, the nulls
src/robustness.py    seven sensitivity tests -> robustness.json
src/make_figures.py  five figures
src/export_web.py    geometry -> SVG paths, payload for the page
src/build_web.py     template + payload -> docs/
data/raw/            downloads and manifest.json (gitignored)
data/out/            ward_panel.csv, results.json, robustness.json, web_data.json
                     borough_ward_crosswalk.csv - 16 boroughs to 144 wards
```
