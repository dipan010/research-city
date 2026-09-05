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

**The honest framing:** "Kolkata publishes enough to locate its amenities, but not enough to audit its spending — there is no KMC equivalent of BBMP's work-order archive." That comparison across your three chapters *is* the cumulative finding, without needing a merged dataset.

---

## Suggested shape

One repo, three notebooks, a shared `wards`/`rates` utility module, and a short write-up per city. The through-line: **ward-level civic equity, and what each city's data does and doesn't let you ask.**

Order of work: Bengaluru first (it carries the project), Mumbai second, Kolkata last and short.

**Two reusable artifacts worth publishing separately** — both are small and neither exists publicly today:
- The BBMP ward-name crosswalk (198 names ↔ numbers ↔ 225/243 vintages)
- The AQI unpivot function — those hourly files are stored in a wide pivot (`Year,2017` header, rows = months, columns = 24 hours), *consistently* across all three cities, so one function cleans Bengaluru's 27, Mumbai's 60, and Kolkata's 14 station files
