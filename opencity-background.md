# OpenCity: Data Registry ↔ Data Stories — Background & Correlation

*Compiled 2026-09-05 from `data.opencity.in` (CKAN API) and `opencity.in/articles` (WordPress REST API). All figures are counts computed from full API dumps, not page samples.*

---

## 1. What OpenCity is

OpenCity is a programme of **Oorvani Foundation**, the same nonprofit behind the civic news platform *Citizen Matters*. It runs two coupled halves:

| Half | Location | Size |
|---|---|---|
| **The registry** — a CKAN instance holding urban datasets scraped, RTI'd, or contributed from Indian government sources | `data.opencity.in` | **1,098 datasets / 8,375 resource files** |
| **The editorial layer** — analyses, explainers, event write-ups built on that data | `opencity.in/articles` | **186 articles** |

The articles page is client-side paginated, so `/page/2/` serves the same first 15 items — the WordPress REST API (`/wp-json/wp/v2/posts`) is the only way to see the full 186.

Licensing is loose and mostly nominal: 740 datasets are "Other (Public Domain)", 49 CC-NC, 34 unspecified, and ~250 carry no license field at all.

---

## 2. The registry in detail

**By city group** (8 groups; 132 datasets belong to none):

| City | Datasets | Share |
|---|---|---|
| Bengaluru | 552 | 50.3% |
| Chennai | 136 | 12.4% |
| Mumbai | 68 | 6.2% |
| Hyderabad | 58 | 5.3% |
| Pune | 57 | 5.2% |
| Delhi | 48 | 4.4% |
| Kolkata | 32 | 2.9% |
| Others | 22 | 2.0% |

Bengaluru is half the registry. This is a home-city artifact — Oorvani is Bengaluru-based — not a statement about data availability elsewhere.

**By publisher** (71 organizations). Concentrated at the top: BBMP 151, Government of Karnataka 125, Government of India 68, Greater Chennai Corporation 52, "Academic/Research Institution" 52, Election Commission of India 44, Pune Municipal Corporation 40, BMC/MCGM 30, Greater Bengaluru Authority 29, NGO 28, Government of Tamil Nadu 28. A long tail follows — courts (Supreme Court 6, Karnataka HC 4, NGT 2, Madras HC 1), utilities (BWSSB 17, BESCOM 10, CMWSSB 12, HMWSSB 4), and one stray `test-org`.

**By theme.** The tag vocabulary is curated, not free-form — only **12 tags exist**, and 157 datasets carry none. So shares below are of the 941 tagged datasets:

Governance 286 · Environment 167 · Mobility 124 · City Services 106 · Urban Planning 69 · Economy 59 · Health 42 · Education 38 · Finance 37 · Infrastructure 29 (plus two near-empty tags, KAOMA and Tender Documents, at 1 each).

**By format — the single most consequential fact about this registry:**

| Format | Files |
|---|---|
| PDF | 640 |
| CSV | 400 |
| KML | 203 |
| XLSX / XLS | 41 |
| ZIP / RAR | 27 |
| GeoJSON | 18 |
| KMZ | 15 |
| DOCX / TXT | 13 |
| images | 5 |

**PDF outnumbers CSV.** This reflects how Indian municipal bodies actually publish — budget books, work orders, tender documents, court orders — and it shapes the entire editorial output (see §5).

**Growth:** 357 datasets added in 2022, 206 in 2023, 226 in 2024, 164 in 2025, 145 so far in 2026. The 2024 year-end article states 825 datasets at that point, versus 1,098 today — consistent, steady accretion of ~150–200/year.

⚠️ **Freshness caveat:** 886 datasets show `metadata_modified` in 2025, but **868 of those fall in November 2025 alone** — that is a bulk migration or re-index, not real updating. Do not read it as data freshness.

---

## 3. The editorial layer in detail

186 articles across six categories:

| Category | Count | What it is |
|---|---|---|
| **Analysis** | 107 | The core output — a dataset interrogated for a finding |
| **Explainers** | 39 | How to read a dataset, or how to use a file format |
| **Jams** | 25 | Datajam / design-jam event write-ups |
| **Showcase** | 11 | Things other people built with OpenCity data |
| **Surveys** | 4 | OpenCity's own crowd-sourced primary collection |
| **Events** | 1 | |

**Publication history is sharply bimodal.** A handful of legacy posts (2008–2021: ~20 items, e.g. "Bangalore Metro Phase 1 Tracker" 2008, "BMTC Bus Routes" 2010) predate the programme in its current form. The real run begins **October 2022** and is sustained: 12 (2022, from Oct) · 37 (2023) · 41 (2024) · 47 (2025) · 29 (2026 through August). That start date matters — the registry's earliest `metadata_created` is also 2022. **Registry and editorial layer were stood up together.**

The 2022 restart is anchored by a specific event: *"Bangalore Floods – A Call for Open Data"* (2022-10-27).

---

## 4. The correlation — hard link evidence

I parsed every `data.opencity.in/dataset/...` URL out of all 186 article bodies.

| Measure | Value |
|---|---|
| Articles linking to ≥1 dataset | **112 / 186 (60%)** |
| …restricted to 2022+, when the registry existed | **111 / 166 (67%)** |
| Total dataset citations | 253 |
| **Distinct datasets ever cited** | **192 (17.5%)** |
| **Datasets never cited by any article** | **911 (83%)** |

**Citation rate by category** — this is the most revealing cut:

| Category | Linked / Total | Rate |
|---|---|---|
| Explainers | 25 / 39 | **64%** |
| Analysis | 69 / 107 | 64% |
| Showcase | 6 / 11 | 55% |
| Jams | 11 / 25 | 44% |
| Surveys | 1 / 4 | 25% |

Explainers and Analysis are the load-bearing tie between the two halves. Jams score low because they are event reportage; Surveys score low because they *generate* data rather than consume it.

**The correlation is strictly one-way.** I grepped all 1,098 dataset records (notes + resource descriptions) for links back to articles: **zero**. A visitor arriving at a dataset page has no path to the analysis written on it. This is the clearest structural gap between the two properties.

**Most-cited datasets** — elections and civic boundaries dominate:

Karnataka Assembly Elections 2023 (5×) · Karnataka & Bengaluru Assembly Constituency Maps (4×) · BMTC Bus Stops and Routes Map by Ward (4×) · NFHS-5, Bengaluru Tree Census, National Time Use Survey 2024, Bengaluru Traffic Violations, BBMP Ward Information, Parliamentary Elections 2024 Voter Rolls, Chennai Climate Action Plan, Bengaluru Urban Public Health Centres (3× each).

**Most data-dense articles:** "Explainer: Bengaluru Elevated Corridors – 2026" (10 datasets), "Resources – Karnataka Elections 2023" (9), "Analysing DGCA Passenger Data" (8), "Resources – General Elections 2024" (8), "BBMP RTI documents" (8), "Bengaluru Constituency Datajam Tables" (8).

**Link rot:** 5 cited slugs now 404 — `Mumbai-udise-2021-22`, `delhi-election-boundaries`, `delhi-slums-data`, `delhi-bus-stops-and-routes`, `economic-survey-of-karnataka` (all verified by HTTP status, not inferred). Small in absolute terms, but there is no redirect layer catching them.

### Where citation over- and under-shoots the registry

Comparing the 187 resolvable cited datasets against registry-wide shares:

| Tag | Registry share | Cited share | |
|---|---|---|---|
| Economy | 5.4% | **15.0%** | ▲ heavily over-cited |
| Finance | 3.4% | 6.4% | ▲ |
| Infrastructure | 2.6% | 5.3% | ▲ |
| Health | 3.8% | 5.9% | ▲ |
| Governance | 26.0% | 22.5% | ≈ |
| Mobility | 11.3% | 10.7% | ≈ |
| Environment | 15.2% | 11.2% | ▼ |
| **City Services** | 9.7% | **3.7%** | ▼▼ most neglected |

Economy/Finance datasets are cited ~3× and ~2× their weight — budgets, HCES, economic censuses are cheap to turn into a story. **City Services (106 datasets) is the largest under-used block**, alongside Environment.

Geographically, citation tracks supply closely for Bengaluru (50.3% → 52.9%) but drops off for the secondary cities: Chennai 12.4% → 7.5%, Hyderabad 5.3% → 1.6%, Pune 5.2% → 2.7%, "Others" 2.0% → **0%**. Data has been collected for these cities faster than stories have been written about them.

---

## 5. Three structural findings

### (a) The PDF-first registry explains the Explainers category

Because supply is 640 PDFs and 203 KMLs rather than clean CSV, a large share of the editorial output is *format tooling*, not analysis:

*"How to extract maps from pdfs"* · *"Explainer: How to view and interact with KML files"* · *"How to Access Government GIS Data for Indian Cities/States"* · *"How to Download Maps from GIS websites"* · *"Georeferencing Image Maps on to a GIS Map"* · *"Scraping Daily Weather Data From Ogimet"* · *"How to check if a CSV file is valid"*

The shape of the supply directly produced the shape of the output. OpenCity had to teach its audience to open its own files.

### (b) The flywheel: Jams → Showcase → third-party tools

The datajams are the mechanism by which datasets become artifacts. The 2024-12-30 post *"Projects in 2024 That Used OpenCity.in Data"* documents this directly:

- **whoismyneta.com** — from a 2024 General Elections virtual datajam; per-constituency MP track records
- **Lakes and Streams of Bengaluru** — interactive map by geospatial scientist Ellen Brock, built after the 7 Dec 2024 Lakes datajam, using WELL Labs' contributed lakes/streams layer; code open-sourced
- **cityofficials.bengawalk.com** — third-party, not from a jam, but built on OpenCity data
- **Chennai flooding analysis** — an Instagram post correlating OpenCity historic inundation zones against Oct 2024 news reports

The Showcase category (11 posts) is the formalization of this: "Bengaluru Metro: Ridership Data For Revenue Optimization", "Masterplan Viewer for Indian Cities", "A Calculator to Measure Chennai's Traffic", "Meet The Trees of Bengaluru", "Visualising Bengaluru's Budget & Where GBA's Money Flows".

### (c) The registry is the evidence base for a data-governance critique

OpenCity's most pointed articles are about the *data itself* being broken. The clearest case, and it is worth stating precisely:

> **Two OpenCity articles report two different national road-death totals for the same year, 2024.**
> - *"Indian Roads Continue to be Deadly with Pedestrians Paying the Price"* (2026-06-15) — **1,75,142** deaths, sourced to **NCRB's Accidental Deaths & Suicides in India (ADSI)**
> - *"Every Fifth Road Death in India is a Pedestrian"* (2026-08-13) — **1,77,175** deaths, sourced to **MoRTH's Road Accidents in India**

Both are correct as reported. Two arms of the Union government count the same deaths and get answers ~2,000 apart. Because OpenCity holds both source reports in one registry and writes from both, the discrepancy surfaces — which is precisely the argument made in *"State of Data Governance in India"* (2025-04-09) and *"Lack of Samples Undermining NSO's CMS Surveys"* (2025-09-11).

Related recurring critiques: *"Explainer: NFHS-6 Data Sheets and the Missing Indicators"*, *"PLFS 2025 – The Missing Half of the Workforce in Indian Cities"*, *"Bangalore Floods – A Call for Open Data"*.

---

## 6. Recurring beats — the same dataset, tracked annually

The strongest pattern in the article set is longitudinal series built on annually-refreshed national datasets. Each is a dataset family in the registry plus a yearly article:

| Beat | Source data | Articles |
|---|---|---|
| **Road crashes / pedestrian deaths** | MoRTH RAI + NCRB ADSI | 2022 → 2023 → Bengaluru 2023 → Mumbai 2023 → KA vs TN → 2024 (×2), 2026 |
| **Crime in cities** | NCRB Crime in India | 2022, 2023 (×2) |
| **Suicides** | NCRB ADSI | 2023, 2024 |
| **Groundwater** | Central Ground Water Board annual | 2022, 2023, 2024, Bengaluru 2024, + data-centre draw 2026 |
| **Municipal budgets** | BBMP / GBA / BMC / GCC budget PDFs | BBMP 2025-26, Brand Bengaluru, GBA 2026-27, GCC 2026-27, BMC 2026-27 |
| **BBMP work orders** | BBMP work-order dumps | 2023 (×2), 2024-25 restoration analysis |
| **Household consumption** | HCES / MoSPI | HCES 2022 explainer + metros analysis; HCES 2023-24 |
| **Elections** | ECI + state EC rolls & maps | KA 2023, GE 2024, MH 2024, Chennai constituencies 2026 |
| **Urban heat** | satellite / ward-level | Bengaluru, Chennai, Mumbai, Hyderabad (Bholakpur, Kondapur), Bellandur |
| **Water tankers** | own survey | Feb 2024, 2025 |

This is why the registry keeps growing without diversifying much: each year's refresh of MoRTH, NCRB, CGWB, MoSPI and the municipal budget books lands as new datasets feeding an established beat.

---

## 7. Summary of the relationship

1. **Built together, October 2022.** Both halves start the same year; the registry has no pre-2022 datasets and the sustained article run begins Oct 2022.
2. **Two-thirds of post-2022 articles cite the registry directly** (111/166) — a genuinely tight coupling for a civic-media/data-portal pair.
3. **But only 17% of the registry has ever been cited.** 911 datasets are archival — collected because they were obtainable, not because a story needed them. That's a deliberate commons strategy, not a failure, but it's the dominant fact of the relationship.
4. **The link graph runs one way.** Articles → datasets, never back. The obvious highest-value fix.
5. **Bengaluru dominates both halves**, and the secondary cities (Hyderabad, Pune, "Others") have data collected far ahead of stories written.
6. **Supply format dictates editorial form** — a PDF/KML-heavy registry produced a whole sub-genre of file-handling explainers.
7. **The jams are the conversion mechanism** turning inert datasets into third-party tools, and Showcase is where that gets recorded.
