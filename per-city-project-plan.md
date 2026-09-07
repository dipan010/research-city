# Per-City Project Plan — Bengaluru, Mumbai, Kolkata

*Three separate analyses sharing one method. No merged dataset, no forced comparison. Every feasibility claim below was verified by downloading and parsing the actual files.*

---

## Why this framing is better

Dropping the "must exist in all three cities" constraint unlocks the platform's best data. That constraint had forced everything onto nationally-uniform survey instruments (UDISE+, HCES, NSS) and threw away the deepest holdings — BBMP's decade of ward-level work orders, Mumbai's 15 geospatial layers, KMC's amenity registries.

The three cities get **different projects on different data, unified by a common method**: ward-level civic equity. Each answers "what does this city's own data say about how services and money are distributed across its wards?"

**Be upfront about the asymmetry.** Bengaluru is the main event, Mumbai is a solid second chapter, Kolkata is genuinely thin. A project that says "Kolkata's open data supports this much and no further" is more credible than one padded to look symmetric — and that limitation is itself a reportable finding about Indian municipal transparency.

---

# 🏆 Bengaluru — "Do Complaints Follow the Money?"

**The flagship. Deepest data on the platform, and a confirmed gap in OpenCity's own coverage.**

## The confirmed originality claim

I searched all 186 OpenCity articles for ones mentioning **both** grievances/complaints **and** work orders. Exactly one hit — a **July 2023 datajam *announcement***, not an analysis. They have analysed grievances alone ("Decoding Bengaluru's Civic Complaints", 2025-07-03) and work orders alone ("What BBMP's Work Orders Reveal About How Money was Spent", 2023-05-23), **but have never joined them.** That join is your project.

## The data (all verified by download)

**Citizen demand — `BBMP Grievances Data`, 6 CSVs, 2020–2024:**
```
Complaint ID, Category, Sub Category, Grievance Date, Ward Name, Grievance Status, Staff Remarks, Staff Name
```
- **91,620 complaints in 2020 → 207,016 in 2024** — a 2.3× rise in five years. That's a finding before you join anything.
- Top 2024 categories: Electrical (75,155), Solid Waste (57,329), Road Maintenance (24,973), Health (15,324), Forest (11,723)
- `Grievance Status` lets you measure *resolution*, not just volume

**Municipal supply — the work-orders family:**
| Dataset | Resources | Coverage |
|---|---|---|
| `BBMP Work Orders by Ward (2013-2022)` | **198 CSVs** (one per ward) | contractor-level, ward-level |
| `BBMP Work Orders and Bill Payment` | 87 CSVs | 2010-15, by department |
| `BBMP Work Orders Categorised (2018-2023)` | 4 CSVs | ward × category totals |
| `BBMP Work Orders and Payments 2024-25 / 2025-26` | 3 + 4 CSVs | current, incl. 198/225/243-ward files |

Ward-level file schema: `id, wo num, wodetails, contractor, brnumber, amount, nett, deduction` — real contractor names and rupee amounts.

## The numbers I already pulled (your headline results are here)

From `BBMP Ward Wise Work Orders Gross Categorised (2018-2023)`:

- **₹46,481 crore** total work-order spend, 2018–2023
- **₹8,023 crore — 17.3% — is `Untagged Expenses/Multiple Wards`**, attributable to no ward at all
- 198 identifiable wards
- **Top ward Horamavu ₹436 cr vs bottom ward Agaram ₹12 cr — a 35.2× spread**

> **That 17.3% is your strongest single number.** The accountability question cannot be answered for nearly a fifth of the money. Lead with it. It sharpens the "do complaints predict spending?" framing rather than undermining it — you're showing exactly where the public record goes dark.

## The join — verified tractable, with one real task

The categories map onto each other cleanly, which is what makes the join meaningful:

| Grievance category | → | Spend category |
|---|---|---|
| Electrical | → | Streetlighting |
| Solid Waste (Garbage) | → | Waste Management |
| Road Maintenance (Engg) | → | Roads and Drains / Roads and Infrastructure |
| — | | Buildings and Facilities, Drainage, Surveillance, Water and Sanitation, Others |

**The join key needed checking, and it passes:**

1. **No ward-vintage mismatch.** BBMP went 198 → 225 → GBA/243 wards. I confirmed **grievances use the 198-ward regime in both 2020 and 2024**, matching the 198-ward work-order files. The trap is real but you don't fall into it. *(If you extend into 2025-26 data, you must use the crosswalk — see below.)*
2. **A crosswalk exists and is published.** `BBMP Ward Information` (13 resources) includes `Constituencies to Wards Mapping for Old and New Wards` with columns `Old Ward Num, Old Ward Name, New Ward Num, New Ward Name` — 245 rows, 241 of which change number. Plus a `Ward No ↔ Ward Name` master for all 198 wards.
3. **Name matching is 51% exact, but 96% resolvable automatically.** Grievance ward names are spelling variants: `bagalagunte`/`bagalakunte`, `bellandur`/`bellanduru`, `binnipet`/`binni pete`, `chamrajpet`/`chamraja pet`. Of 96 unmatched names, **fuzzy matching at 0.82 cutoff resolves 88 — leaving just 8 for manual mapping** (`hoodi`, `ulsoor`, `rajamahal`, `yadiyuru`, `someshwara`, `hagadooru`, `subedarapalya`, `gali anjaneya swamy temple`).

**Build the crosswalk as a versioned CSV in your repo and publish it.** It's an hour of work, it's the thing that makes the analysis possible, and nobody else has published one.

## What to build

1. Per-ward, per-category: complaints per capita vs rupees spent
2. **The correlation** — do high-complaint wards get more money? Lagged: do 2020-21 complaints predict 2022-23 spend?
3. Resolution rates by ward — where do complaints get closed vs languish?
4. Contractor concentration — how much of a ward's spend goes to how few contractors? (`contractor` field is right there)
5. Map it on `BBMP Ward Information`'s ward KMLs (2015, 2022, 2023 boundaries all provided)

**Optional enrichment, all Bengaluru-only and all CSV:** `BBMP Fix My Street`, `BBMP Property Tax Collections` (does a ward get back what it pays?), `Bengaluru MLA - Local Area Development Funds` (28 res), `BBMP Budget` (22 res), `Bengaluru Urban Slums`.

---

# 🥈 Mumbai — Spatial Equity of Civic Amenities

**The best geospatial set on the platform. A genuine second chapter, lighter than Bengaluru.**

Mumbai has **15 geospatial layers**, and critically includes `Mumbai - Slum Cluster Map` — which turns a mapping exercise into an equity question.

**Base layers:** `Mumbai Wards Map` (KML), `Mumbai - Slum Cluster Map` (KML), `Mumbai Microwatersheds Map` (GeoJSON)

**Amenity layers (all KML):** Public Toilets · City Public Health Centres (+CSV) · Fire Stations · Police Station Locations · Schools Locations · Public Gardens, Parks and Zoos · Funeral and Cremation Sites · BEST Bus Stops and Depots · Parking · Suburban Network 2025

**The question:** overlay slum clusters against amenity locations. Compute per-ward and per-cluster access — distance to nearest public toilet, health centre, school, bus stop. Are the highest-density, lowest-income areas the furthest from public services?

**Supporting tabular data:** `Mumbai - Ward wise Census Data` (denominators for per-capita rates), `Mumbai Water Connections Details`, `Mumbai Traffic Violations Data 2024`, `Mumbai - Crime Data 2023`, `Mumbai Hourly Air Quality Reports` (60 resources), `Mumbai Rainfall Data`, `BMC Budget` 2024-25 through 2026-27.

**Policy overlay:** `Mumbai Development Plan 2034`, `DCPR 2034`, `Mumbai Climate Action Plan`, `Mumbai Comprehensive Mobility Plan` are all PDFs — use them to frame what the city *promised*, against what the layers *show*.

⚠️ Public-toilet access in slum clusters is a sensitive, real-stakes finding. Report rates and distances carefully, don't over-claim causation, and cite the layer vintages — some KMLs are undated.

---

# 🥉 Kolkata — Ward-Level Amenity Access (honestly scoped)

**Thin, and say so. 32 datasets total, 17 from KMC. Only 4 geospatial layers.**

This is a smaller, self-contained piece — not a third of equal weight.

**What's genuinely there:** `Kolkata Wards Information` (KML) as a base, joined to amenity CSVs — `Kolkata Civic Amenities`, `Kolkata Markets`, `Kolkata Health Services`, `Kolkata Public Service Centres`, `Kolkata Schools`, `Kolkata Municipal Corporation Offices`.

**The distinctive asset:** `Kolkata Water Bodies Census Data` (KML) — a census of water bodies, which is genuinely unusual and pairs with `Kolkata Microwatersheds Map` (GeoJSON) for a wetlands/drainage angle. Kolkata's East Kolkata Wetlands context makes this the most interesting thing in the city's holdings.

**Also usable:** `Kolkata Hourly Air Quality Reports` (14 WBPCB station CSVs, 2017-2023), `Kolkata UDISE+` (2021-22, 2023-24, 2024-25), `KMC Budget Statement`, `Kolkata RTO-wise Vehicle Registrations` (2021-2025).

⚠️ **Boundary caveat:** Kolkata *district* is smaller than KMC's actual jurisdiction, which extends into South 24 Parganas. Any district-sourced data (UDISE+, Census, RTO) undercounts the city. Note it; don't silently mix it with KMC-sourced data.

## Verified against the catalogue, 2026-09-07

*The scoping above was written before checking. These were confirmed by API sweep
and by downloading the ward file. Two of them contradict it.*

- **27 Kolkata datasets on the portal**, not 32. Only 3 carry geospatial
  resources: `Kolkata Wards Information` (KML), `Kolkata Water Bodies Census
  Data` (KML), `Kolkata Microwatersheds Map` (GeoJSON).
- **`Kolkata Drainage Maps` has 80 resources.** The scoping above does not
  mention this dataset at all, and it is the largest Kolkata holding by a wide
  margin. Check what is in it before accepting the "Kolkata is thin" framing:
  it may carry the project.
- **The ward KML holds exactly 141 placemarks**, resource named "Kolkata Wards
  Map 2022", single attribute `WARD`. KMC's formal ward count is 144, so three
  are missing or merged. Resolve that before any ward join, and do not assume
  the file matches the corporation.
- `Kolkata Schools`, `Kolkata Markets`, `Kolkata Civic Amenities` (4 res),
  `Kolkata Health Services` (5 res), `Kolkata Public Service Centres` (3 res)
  are the amenity tables. None is geospatial, so any mapping needs a join or
  geocoding, which is a materially harder build than Mumbai's ready-made KMLs.
- `KMC Budget Statement` has 16 resources. Worth checking whether it supports
  anything like the BBMP work-order analysis before concluding it does not.

**The Mumbai method transfers, the Mumbai data does not.** Mumbai had point
layers for ten services and a polygon layer for the thing of interest. Kolkata
has 141 ward polygons and a pile of tables. Expect the shape to be closer to the
Bengaluru project (join tables to wards) than the Mumbai one (spatial overlay),
with the water bodies census as the one genuinely spatial asset.

## Feasibility pass, 2026-09-07 — the four open questions, answered

*Everything below was verified by downloading and parsing the actual files. The
four questions raised by the catalogue sweep above are now closed. Three of the
four answers are negative, and they close off most of the scoping this document
originally proposed.*

### 1. `Kolkata Drainage Maps` (80 resources) — scanned PDFs, not data

All 80 resources are **PDF ward drainage-network maps**, one per ward, 160 KB to
3 MB each. There is no tabular or geospatial resource in the dataset. Coverage is
**80 of 144 wards**, and the gaps are not random: present are wards 7-100 with
holes, plus 115 and 133-141. Absent are wards 1-6, most of 101-132, and 142-144 —
that is, the whole of Boroughs XI, XII, XIII, XIV and XVI barring ward 115.

This dataset does **not** carry the project. Using it at all means georeferencing
and digitising 80 scanned plans, which is a multi-week GIS effort with no
guarantee the line work is machine-traceable, and it would still cover only 55%
of the city. Treat it as context or as a separate digitisation proposal, not as
an analysis input.

### 2. The ward KML is 141 because it is the pre-2015 boundary set

Not three wards "missing or merged" — a stale vintage. Parsed:
`Kolkata Wards Map 2022` holds 141 placemarks, all with geometry, `WARD` values
1-141, **no duplicates**, and exactly wards **142, 143 and 144 absent**.

The election files settle why. `Kolkata KMC Election Results 2010` has exactly
**141 wards**; `Kolkata KMC Election Results 2015` has exactly **144**. KMC
expanded from 141 to 144 wards ahead of the 2015 poll, annexing the Joka area
(Borough XVI now reads `123,124,125,126,142,143 &144`). The file named "2022"
therefore predates 2015. **This is the Bengaluru filename lesson again: count the
features, do not trust the name.**

Consequence, and it is the boundary caveat biting exactly as predicted: the water
bodies census holds **68 records in wards 142-144** that have no polygon to land
in. Any spatial join silently drops them unless handled.

### 3. `KMC Budget Statement` cannot support a BBMP-style analysis. It is flat by construction.

The 16 resources are all PDFs, but they are text-extractable (`pdftotext -layout`
works cleanly), so this was checked rather than assumed. The ERP account code has
`Borough` and `Ward` columns throughout — but they are filled with the aggregate
placeholders `60` and `333` on essentially every line. Every document is the
consolidated `BOROUGH I - XVI` statement. There is no per-borough or per-ward
breakdown of ordinary expenditure.

There is exactly **one** ward-attributed line item in the whole budget:
**Councillors' Elaka Unnayan Prakalpa**, which lists all 144 wards individually.
Its allocation is **identical for every ward**:

| Budget | Per-ward allocation | Wards | Variance |
|---|---|---|---|
| BE 2019-20 | ₹12.50 lakh | 144 | zero |
| BE 2021-22 | ₹12.50 lakh | 144 | zero |
| BE 2025-26 | ₹15.00 lakh | 144 | zero |

It appears under two object codes (400 "Works" and 800 "Supply"), each block
totalling **₹2,160.00 lakh = ₹21.6 crore**. Whether the two blocks sum to ₹30
lakh per ward or restate the same money by object code is **not resolvable from
the PDF** — do not quote a combined total without settling it.

Against KMC's BE 2025-26 total expenditure of **₹5,639.56 crore**, ward-attributed
spending is **₹21.6 crore, or 0.38% of the budget — and it has no variance at
all.**

> **This is the cleaner version of the finding this document was reaching for.**
> BBMP attributes 82.7% of ₹46,481 crore to named wards and shows a 35× spread
> between top and bottom. KMC attributes 0.38%, equally, by design. There is no
> ward-level spending variation in Kolkata's published budget to correlate
> against anything. That is one strong sentence, not a project — and it is the
> honest answer to "is there a KMC equivalent of the work-order archive?" No.

### 4. The amenity tables mostly cannot be joined to wards, and one of them is the wrong file

**Five of the fourteen amenity CSVs carry a ward column**, and their coverage is
too sparse to compute per-ward rates:

| Table | Rows | Wards covered (of 144) |
|---|---|---|
| KMC Immunization centres | 223 | 127 |
| KMC Schools | 258 | 106 |
| KMC Taxi Parking (2018) | 276 | 55 |
| KMC Parks and Gardens | 92 | 53 |
| KMC Dispensaries | 22 | 21 |

The rest carry borough only (Malaria Clinics, Birth Registration), a bare address
(Crematoriums, Chest Clinics, Death Registration), or **nothing but a name** —
`KMC Markets` is 47 rows of market names with no address, no ward and no
coordinates. None of the fourteen is geospatial.

**A borough → ward crosswalk does exist** and is worth publishing as a small
artifact: `KMC Borough Committees Office` lists the ward numbers belonging to
each of the 16 boroughs, covering 1-144 completely. It places the borough-only
tables at borough resolution, not ward.

**`KMC Pay-and-use Toilets (2018)` is not a toilets file.** It is a
**byte-identical duplicate of `KMC Schools`** — same MD5
(`1c0ce93ca1f54407777bcec4ea582c8e`), same 258 rows, same header
(`School Code, School Address, School Type, Classes, No of Students`). The
portal's only Kolkata sanitation resource contains school data. **Kolkata has no
public-toilet data at all**, so the Mumbai chapter's central question cannot be
asked here. This is worth reporting to OpenCity regardless of what gets built.

> **The structural-zero problem is what actually rules out ward amenity access.**
> With 88 of 144 wards absent from the parks table, there is no way to tell "this
> ward has no park" from "this ward is not in the registry." Every per-ward rate
> would rest on an ambiguous denominator, and the ambiguity will not be random —
> it will correlate with whatever is being tested. These tables support a
> **data-quality audit**, not an access analysis.

### The one asset that does hold up: `Kolkata Water Bodies Census Data`

3,051 placemarks, **all points, all with geometry, none dropped**, from the
national Jal Shakti water bodies census. 28 attributes with real variance:

- **Ward is encoded in the `village` field** (`KOLKATA (M CORP.) WARD NO.-0108`),
  so all 3,051 are ward-tagged **and** independently geocoded. That allows the
  Mumbai discipline: assign spatially, keep the attribute, and report how often
  the two disagree.
- Covers **93 of 144 wards**. Of the 51 absent, **37 are wards ≤54** (the dense
  old-city core), **13 sit in the 55-100 band** (60, 61, 65, 68, 70, 73, 74, 77,
  83, 84, 86, 87, 88) and one is ward 134 in Garden Reach. Not a clean block.
- Ownership: **Individual 1,695 · Other private 766 · Group of individuals 315 ·
  Municipal authority 228 (7.5%) · Panchayat 33**.
- **906 of 3,051 (29.7%) are recorded as not in use.** Of the 2,145 in use:
  pisciculture 1,098, domestic/drinking 681, industrial 366.
- Heavily concentrated: **ward 108 alone holds 453**, ward 58 holds 292.

#### The 51 zero-wards look like real absence, not an enumeration gap

This is the same structural-zero problem that rules out amenity access, so it was
tested rather than assumed — it decides the inference unit. If the zeros are an
enumeration gap the usable n is 93 and the sample is biased; if they are real,
the unit is **144 wards with 51 legitimate zeros**.

The discriminating test is whether the small-pond left tail survives in the core.
It does, and more strongly than elsewhere:

| Band | n | min (ha) | p10 | median | share ≤0.03 ha |
|---|---|---|---|---|---|
| Core, wards ≤54 | 134 | 0.02 | 0.04 | 0.11 | **9.0%** |
| Mid, 55-100 | 578 | 0.01 | 0.05 | 0.22 | 2.2% |
| Peripheral, >100 | 2,339 | 0.01 | 0.03 | 0.09 | 13.6% |

Enumerators recorded ponds down to 0.02 ha *in the core*, at a higher small-pond
share than the mid band, so there was no size threshold suppressing small water
bodies there. The per-ward counts in covered core wards also form a gradient
rather than a block — wards 4, 9, 27, 29, 41, 45 and 46 have exactly one record
each, next to wards 1 (36) and 33 (24) — and no borough is wholly absent
(Borough I retains wards 1, 2, 4 and 9). Both patterns fit genuine scarcity.

**Counterweight, and keep it in view:** Ray's NATMO figure is 8,731 ponds against
this census's 3,051. That 3× gap has to live somewhere, and "small ponds in the
dense core" is the obvious candidate. So treat **n=144 with zeros as primary and
n=93 as the sensitivity case**, and report both rather than picking one silently.

**Two dead fields — do not report either as a result.** `waterbody_encroached`
is `No` for all 3,051, and `water_body_nature` is `Man-made` for all 3,051. The
census instrument collects encroachment nationally, so a uniformly negative
column in a city with a litigated pond-filling history is evidence the field was
never populated, not evidence of no encroachment. Reporting "0% encroached", even
hedged, would repeat the Mumbai retraction shape.

### The EKW framing does not survive the data — say so before anyone commits to it

The idea that this is an East Kolkata Wetlands dataset was tested and **fails**:

| | |
|---|---|
| Total water spread area, all 3,051 | **1,175 ha** |
| Median | 0.10 ha |
| 95th percentile | 1.28 ha |
| Largest single body | 38.93 ha |
| Bodies over 10 ha | 13 |
| EKW Ramsar site, for comparison | **~12,500 ha** |
| Easternmost record | 88.458 E |

The file's entire stock is under a tenth of the Ramsar site's area, its largest
water body is 39 ha against EKW's sewage-fed *bheris* of hundreds of hectares,
and the coordinates stop at the KMC jurisdictional boundary — **the bheris are
not in this file.** There is a real eastern concentration (808 records east of
88.40 E, 692 ha, in wards 108, 58 and 109 — the KMC-side fringe), but that is the
fringe, not the wetlands.

**Call it what it is: Kolkata's ward-level pond and tank stock.** Naming it East
Kolkata Wetlands would be a framing the data cannot carry, shipped publicly.

### Prior work — this is an extension, not a discovery

Mohit Ray's CSE deck *Water bodies of Kolkata* is the standing reference. It
tabulates KMC's own pond counts — **1,786 (1997), 3,873 (2006)** — against NATMO's
8,731 and 4,889 counted from satellite imagery, and argues **~44% of Kolkata's
water bodies were filled in two decades.** The loss narrative is published.

What is not published is this census read at ward level. The national count of
**3,051** sits below KMC's own 2006 list of 3,873, which is the natural hook — but
it is a *comparison across incompatible instruments and vintages*, so treat it as
a question, not a finding. No ward-level analysis of the Kolkata Jal Shakti file
was found on OpenCity or in general search.

### Vintage table — every layer is a different year, and two are mislabelled

| Source | Actual vintage | What the portal says |
|---|---|---|
| Ward KML | **pre-2015** (141 wards) | resource named "Kolkata Wards Map 2022" |
| Water bodies census | **enumerated Nov 2020 – Nov 2021** (from `enumeration_date`) | described "2018-19", resource named "2023" |
| Amenity CSVs | 2018 or earlier; none has a record above ward 141 | undated |
| KMC elections | 2010 (141 wards), 2015 (144 wards) | correct |
| KMC budget | 2017-18 to 2026-27 | correct |
| Drainage PDFs | undated | undated |

Both the ward file and the water bodies file are mislabelled on the portal, in
opposite directions. The amenity tables containing no ward above 141 is a useful
cross-check: they are the same pre-expansion vintage as the ward polygons, so
joining those two is at least internally consistent.

### Two assets the original scoping missed entirely

`Kolkata KMC Elections Data` (2010 and 2015) is **ward-level, complete, and
KMC-sourced** — 1,044 and 1,084 candidate rows carrying `Ward_No`,
`Total_Electors`, `Total_Votes`, `Voter_Turnout_Percentage`, party and gender.
`Total_Electors` sums to **3.43 M across 141 wards (2010)** and **3.74 M across
144 wards (2015)**.

That matters more than it looks: it is a **ward-level denominator that is not
district-sourced**, so it sidesteps the boundary caveat that disqualifies census,
UDISE+ and RTO data. It is an electorate, not a population, and it is a decade
old — but it is the only complete per-ward denominator Kolkata publishes.
(The `District` column reads "South 24-Parganas" on every row of both files; that
is a source artifact of the election dataset, not geography.)

**`Kolkata - Economic Census` (6th EC, 2012-13) is establishment-level microdata
with a ward code**, and at 34.7 MB it is the largest tabular Kolkata holding on
the portal. It is **not** the district-aggregate table it looks like from the
catalogue. Schema:

```
State, District, Tehsil, T_V, WC, EB, EBX, C_HOUSE, IN_HH, BACT, NIC3,
HLOOM_ACT, OWN_SHIP_C, SEX, SG, RELIGION, NOP, SOF, M_H, F_H, M_NH, F_NH,
TOTAL_WORKER, SECTOR, DISTRICT
```

`WC` is the ward code and `TOTAL_WORKER`, `M_H`/`F_H`/`M_NH`/`F_NH` give hired
and non-hired employment by sex; `BACT` is a 21-class broad activity code.
Estimated **~558,000 rows** (measured from a 400 KB range request: 6,439 rows in
the first 400 KB). In that sample `WC` runs **0-141** — the pre-2015 regime again,
consistent with a 2012-13 vintage, and consistent with every other Kolkata ward
source on the portal.

Caveats before leaning on it: it is **district-sourced** (`DISTRICT` = 1916,
Kolkata), so the boundary caveat applies and wards 142-144 will be absent; the
bundled metadata CSV describes `WC` as "0-198 ward no.", which is BBMP's ward
count, so **the metadata file is generic across cities and is not authoritative
for Kolkata**; and only the first 6,439 rows were parsed here, so the full ward
distribution is unverified.

It is a candidate ward-level denominator (establishments and workers per ward,
independent of electorate) and arguably a project in its own right. It is also
thirteen years old.

`KMC Drainage Pumping Stations Sewage Treatment Plants` (81 rows: Type, Name,
No of Pumps, Telephone) is the only other drainage-adjacent table. It has **no
ward and no coordinates**, so it can be mapped only by geocoding station names.

### Where this leaves Kolkata

- **Drainage maps: no.** 80 scanned PDFs, 55% ward coverage, digitisation project.
- **Budget: no.** One flat ward line, 0.38% of spend, zero variance. One sentence.
- **Amenity access: no.** Sparse, ambiguous denominators, and the toilets file is
  the schools file.
- **Water bodies: yes, at ward level.** Real attribute variance, a ward key and
  independent coordinates. Primary unit **n=144 with 51 zeros** (rho critical
  value ≈ 0.164 at 5%), sensitivity at **n=93** (≈ 0.204).
- **Economic census: unresolved, and worth resolving.** ~558k establishment rows
  with a ward code, but 2012-13 and district-sourced.

Inference belongs at the **ward**, not the water body: 453 of 3,051 records sit in
ward 108 alone, so treating individual water bodies as independent observations
would repeat the Mumbai 47,450-grid-cell mistake.


~~**The honest framing:** "Kolkata publishes enough to locate its amenities, but not enough to audit its spending — there is no KMC equivalent of BBMP's work-order archive."~~

**Superseded by the feasibility pass.** The second half holds and is now
quantified (0.38% of budget, zero ward variance). The first half does not:
Kolkata does *not* publish enough to locate its amenities — 88 of 144 wards are
absent from the parks table, the markets table has names only, and the
pay-and-use toilets resource is a duplicate of the schools file. The cumulative
three-chapter comparison stands, but Kolkata's side of it is "cannot audit
spending **and** cannot locate amenities", with the water bodies census as the
one exception.

---

## Suggested shape

One repo, three notebooks, a shared `wards`/`rates` utility module, and a short write-up per city. The through-line: **ward-level civic equity, and what each city's data does and doesn't let you ask.**

Order of work: Bengaluru first (it carries the project), Mumbai second, Kolkata last and short.

**Two reusable artifacts worth publishing separately** — both are small and neither exists publicly today:
- The BBMP ward-name crosswalk (198 names ↔ numbers ↔ 225/243 vintages)
- The AQI unpivot function — those hourly files are stored in a wide pivot (`Year,2017` header, rows = months, columns = 24 hours), *consistently* across all three cities, so one function cleans Bengaluru's 27, Mumbai's 60, and Kolkata's 14 station files

---

# Carried forward from the Bengaluru build

*Added after `bbmp-complaints-vs-spending` shipped. These cost real time; they
will recur on Mumbai and Kolkata.*

**The denominator decides the conclusion.** Raw counts, per km², and per resident
gave three *opposite* geographic answers from the same two columns. Mumbai's
wards vary in size and density at least as much as Bengaluru's, so never publish
a ward-level claim without naming its denominator — and check all three before
believing any of them.

**Check for summary rows before summing a government CSV.** A `GranTotal` row in
BBMP's work-order file got summed along with the data and put a headline figure
2× out. Reconcile the parts against the stated total every time.

**Verify boundary regimes match across datasets.** BBMP has 198, 225 and 243-ward
regimes in circulation, the grievance extracts mixed labels from two of them, and
the KML filenames did not match their actual ward counts (the file named "2022"
holds 243 wards; "2023" holds 225). Count the features before trusting a name.

**Look identifiers up; never infer them.** Six ward numbers guessed from name
similarity silently misassigned data into the wrong wards. Exact lookup against
the master, or leave it unresolved and document it.

**Check prior work before claiming novelty.** Two findings that looked original
had already been published by Citizen Matters in 2023. Search their archive and
OpenCity's 186 articles first — it changes the framing from "I discovered" to
"I extended", which is both accurate and more defensible.

**Bound caveats, don't just state them.** Every judgement call got a sensitivity
test in `robustness.py`. "We excluded 1.7% of records" is weak; "excluding them
moves ρ from 0.341 to 0.350" is finished work.

**Small mechanical traps.** Indian digit grouping (`72,63,34,02,610`) makes
`pd.to_numeric` return NaN. KML rings carry a z coordinate, so
`for x, y in ring.coords` raises. A `.gitignore` line excluding a directory
outright stops git descending into it, so any `!negation` beneath it silently
never applies. Standalone HTML needs its own `<meta charset="utf-8">` or every
₹, — and ² breaks when opened from disk.

## Suggested Mumbai scaffold

Copy the shape of `bbmp-complaints-vs-spending/`: `fetch.py` resolving CKAN
resources by title and name, a build step per stage, `robustness.py` alongside
the analysis, and `web/template.html` built into the repo's `docs/`. The
crosswalk step is Bengaluru-specific and Mumbai may not need it — but check
whether BMC ward names are consistent across its datasets before assuming so.

---

# Carried forward from the Mumbai build

*Added after `mumbai-slums-vs-amenities` shipped. Kolkata is next and has 4
geospatial layers and 141 wards — a different shape again, so check which of
these apply before assuming.*

**Match the inference unit to the n you actually have.** Mumbai has 24 wards.
At n=24 a Spearman coefficient needs ~0.41 to clear the 5% level, so the whole
correlation-and-quintile structure that carried the Bengaluru project could not
be reused. Inference moved to the slum cluster (n=2,541) and a 100 m grid cell
(n=47,450); wards were kept for the map and the table only. Kolkata's 141 wards
sit awkwardly between the two — check the critical value before reporting a rho.

**A big nominal n is not a big effective n.** Grid cells 100 m apart are heavily
spatially autocorrelated. Mann–Whitney on 47,450 of them returned p < 1e-140,
which is an artifact of treating neighbours as independent, and reporting it
would have undercut the n=24 discipline in the same document. The defensible
statistic was "closer in 21 of 21 wards".

**Choose the comparison group, or it chooses your answer.** Slum land looked
closer to all ten services than "the rest of Mumbai" — but that baseline held
the national park, mangroves, salt pans and the airport. Against inhabited land
only three of ten survived, and four reversed. The first version of this finding
was wrong in exactly the way the denominator trap is wrong, one level up: it was
the *comparison set*, not the divisor. Define the baseline as deliberately as
the denominator, and score each service against a proxy it does not itself
define or the test is circular.

**Check for a newer edition of your prior-work source, then re-check.** The
Mumbai page shipped publicly claiming a BMC map-vs-RTI toilet discrepancy was
unexplained, having "ruled out" the obvious pooling explanation. It was wrong on
both counts. Praja's **May 2025** report — on the same OpenCity portal already
swept, while only the **May 2024** edition had been read — tabulates public and
community toilets separately and shows the layer plainly pools them. The claim
had to be retracted after publication.

**A negative result from an untested proxy is not evidence.** The "ruled out"
argument was: pooling would leave a male-skewed subset, none was found inside
versus outside slum polygons, therefore no pooling. That test assumes public
toilets sit outside slum polygons and community toilets inside — which is false,
since public toilets serve markets, stations and streets often inside dense slum
areas. The proxy could never have detected what it was asked to detect. Before
trusting a null, ask whether the measurement could have found the thing at all.

**State data vintages as a table, not as scattered caveats.** Mumbai mixed a 2011
census denominator, a 2015 slum footprint, undated ~2023 amenity layers and 2024
reference figures. CKAN's dates were the bulk-upload date and carried no vintage
information at all; the real ages had to be recovered from resource names and
from embedded edit timestamps in the two layers that happened to carry them.
Every headline ratio spans at least two vintages, and one of them (households per
seat) is an upper bound purely because of it.

**Polygon distance, not centroid distance.** Measuring from a cluster's centroid
overstated distance-to-toilet by a median 33 m overall and 54 m for the largest
decile of clusters, and reported 0% of clusters as containing a toilet against
the true 32.8%. The shortcut penalises exactly the biggest settlements.

**Verify positional column indices in a merged-header government sheet.**
Census table HH-14 has a four-row merged header pandas cannot parse into names,
so its columns are addressed by position — with an assertion that the header
text still reads "not having latrine" and "Public latrine" before any number is
taken out of them.

**Normalise labels by lookup across every layer.** The same 24 BMC wards are
spelled `K/E`, `KE`, `K-E` and lowercase across layers. One `norm_ward()` strips
separators and looks the result up against the canonical list, returning None
rather than guessing. Assign the unit spatially and keep the attribute only to
measure how often the two disagree — 3.1% on toilets, 13.9% on health UPHCs,
which is a publishable data-quality finding in itself.

**Count placemarks against geometries.** 16 of 134 police placemarks, and 1 slum
placemark, carry no geometry at all. Report the drop; do not let a layer quietly
shrink.

