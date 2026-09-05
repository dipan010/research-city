# Personal Project Options: Bengaluru × Mumbai × Kolkata on OpenCity Data

*All feasibility claims below were verified by downloading the actual files, not read off dataset titles.*

---

## The finding that picks your project

I checked which dataset families exist in all three cities. The result is sharp:

| Family | BLR | MUM | KOL | Tri-city? |
|---|---|---|---|---|
| UDISE+ schools | 4 | 4 | 4 | ✅ |
| Household Consumption (HCES) | 1 | 1 | 1 | ✅ |
| NSS Multi-Indicator Survey | 1 | 1 | 1 | ✅ |
| Economic Census | 1 | 1 | 1 | ✅ |
| Hourly Air Quality | 4 | 1 | 1 | ✅ |
| RTO vehicle registrations | 2 | 3 | 1 | ✅ |
| Aviation traffic | 1 | 1 | 1 | ✅ |
| Municipal budget | 11 | 3 | 1 | ✅ |
| **Water bodies / lakes** | **27** | **0** | **1** | ❌ |
| **Master / Development Plans** | **10** | **4** | **0** | ❌ |
| **Parks / trees** | **22** | **4** | **0** | ❌ |
| **Parking** | 6 | 1 | **0** | ❌ |
| **Crime data** | 5 | 1 | **0** | ❌ |
| **Bus stops / routes** | 2 | 1 | **0** | ❌ |
| **Police stations** | 2 | 1 | **0** | ❌ |
| **Building bye-laws** | 8 | 1 | **0** | ❌ |

**The rule this gives you: anything tri-city must be built on a *nationally-uniform instrument* — UDISE+, HCES, MIS, Economic Census, RTO, CPCB air quality. City-generated data collapses at Kolkata.**

Kolkata has 32 datasets and 17 of them come from one body (KMC). Bengaluru has 552. That gap is not a data-availability fact about the cities — it's an artifact of OpenCity being Bengaluru-based. Don't fight it; build on the uniform instruments and the asymmetry becomes a *finding you report*, not a problem you hide.

---

## ⚠️ The one design rule you cannot break

UDISE+ (and Census/RTO) data is published by **revenue district, not municipal area**:

- **Bengaluru** = Bengaluru Urban North (2,493 schools) + South (3,646) = **6,139** — but Bengaluru Urban district ≠ BBMP/GBA
- **Mumbai** = Mumbai City (1,750) + Mumbai Suburban (2,343) = **4,093** — closest fit to BMC of the three
- **Kolkata** = **2,344**, single district — but *smaller* than KMC, which spills into South 24 Parganas

So "Bengaluru has 2.6× Kolkata's schools" is a **boundary artifact, not a finding.**

> **Every cross-city number must be a rate or ratio, never a count.** % of schools with functional girls' toilets, pupil–teacher ratio, % of classrooms needing major repair, % with a boundary wall. Those are boundary-invariant. Counts are not.

State this rule prominently in your README. It's the single thing that separates a project that survives scrutiny from one that doesn't.

---

## ⭐ Option 1 — School Infrastructure Equity Index (recommended)

**The strongest option, and I verified it end-to-end.**

### What I confirmed by download

- **Headers are byte-identical across all three cities.** The 2024-25 `Facilities` CSV for Bengaluru, Mumbai, and Kolkata share the same 70-column header, character for character.
- **The schema PDF is byte-identical across the three cities** (same MD5: `56fcf276…`) — one codebook covers all of them.
- **Codebook decoded and confirmed:** `Yes=1, No=2`; `electricity_availability` is 3-state (`1:Yes, 2:No, 3:Yes but not functional`); toilet fields are counts, not flags; furniture is `1-Yes for all, 2-Partial, 3-No Furniture`.
- **It is a genuine panel.** Two schema generations exist — 2021-22 (41 cols) and 2023-24/2024-25 (70 cols) — sharing **36 common columns**. Those 36 give you 3 cities × 3 years of comparable data, with 2025-26 district reports as a fourth wave.
- **~12,600 schools** in one year across the three cities. School-level microdata, keyed on a pseudonymised school ID.

### Two gotchas I hit (mention them in your writeup — they show rigour)

1. **The ID column is misspelled in 2021-22.** It's `psuedocode` in 2021-22 and `pseudocode` from 2023-24 on. A naive `pd.concat` silently produces two half-empty columns.
2. **Water access was re-instrumented between waves.** 2021-22 has `drinking_water_available` / `drinking_water_functional`; 2023-24+ replaces these with `hand_pump_yn`, `pack_water_fun_yn`, `othsrc_fun_yn`, etc. You *cannot* trend water access across the break without an explicit mapping — and honestly documenting that you can't is a better result than a fake trendline.

### What to actually build

A composite index per school, aggregated to district, on boundary-invariant rates:
- Sanitation: functional girls'/boys' toilets per 100 students; CWSN-accessible toilet availability
- Structure: % classrooms in good condition vs needing major repair; boundary wall present
- Services: electricity functional (careful — code 3 is *not* code 1), library, ramps + handrails
- Staffing: pupil–teacher ratio from the `Teachers` + `Enrolment` resources

Then: rank, map, and trend 2021-22 → 2024-25 on the 36-column core.

### Why it works as a portfolio piece

**OpenCity's own two-part UDISE analysis (2024-09-10 and 2024-09-13) used 2021-22 data and did not do the cross-city rate comparison or the multi-year trend.** You'd be doing something additive with their own data, not re-treading it. That framing — "here's what the publisher hasn't done with their own archive" — is what makes it a portfolio piece rather than a tutorial.

---

## Option 2 — "Two Agencies, Two Numbers": the air quality reconciliation

The sharper, more original idea. Smaller scope, bigger payoff if you like a punchy result.

**Mumbai has `Bandra Kurla Complex IITM AQI Data` and `Bandra Kurla Complex MPCB AQI Data` — two agencies measuring the same location.** Bengaluru's 27 stations and Kolkata's 14 (WBPCB) let you extend the check.

This reproduces, at station level, exactly the discrepancy I found in OpenCity's own reporting: their June 2026 article cites **1,75,142** road deaths for 2024 (NCRB ADSI) while their August 2026 article cites **1,77,175** for the same year (MoRTH). Two government arms, same phenomenon, different numbers. Doing that at AQI-station level is the same story told with data you can download and verify yourself.

**Data engineering angle:** the AQI CSVs are stored in a wide pivot — header is `Year,2017`, rows are months, columns are the 24 hours. Ugly, but *consistently* ugly across all three cities, so one reusable unpivot function handles everything. Coverage is 2017–2023 hourly. That's a legitimate "I can wrangle real government data" showcase.

---

## Option 3 — Cost of living, three cities (HCES + MIS)

**Verified:** `HCES 2022-23` exists for all three cities with **identical 17-resource structure** (`HCES Level 01`–`Level 06` CSVs), and `NSS Multi-Indicator Survey 78th Round 2020-21` exists for all three with identical 10-resource structure.

This is NSO household microdata at level-file granularity — the real thing, not summary tables. Combine with `RTO-wise Vehicle Registration Data` (2021–2025, five annual CSVs, all three cities, identical naming) for a consumption-and-mobility picture.

Lower effort than Option 1 because the schemas are already aligned. Higher effort in *interpretation*, because NSO level files need the survey design (weights, multipliers) handled properly or your numbers are wrong. Only pick this if you're comfortable with survey weighting.

---

## Option 4 — A reverse index for OpenCity (small, useful, very fast)

From the research: **articles cite datasets 253 times, but zero dataset records link back to any article.** Someone landing on a dataset page has no way to find the analysis written on it.

You already have the extracted link graph. Building a browsable dataset→article reverse index — and offering it to OpenCity — is a genuinely useful contribution and a *tiny* build. Weaker as a data-analysis showcase, strong as an "I noticed a real gap and shipped a fix" story. Good as a companion piece to Option 1, not as your main project.

---

## Recommendation

**Build Option 1, and fold in Option 2 as a second chapter if you want more range.**

Option 1 is the only one where I verified identical schemas across all three cities *and* a working multi-year panel *and* an unaddressed gap in the publisher's own coverage. Option 2 adds a memorable headline and shows data-engineering chops. Together they read as one coherent project: *what three Indian cities' open data can and cannot tell you, and where the government disagrees with itself.*

Lead your README with the tri-city availability table and the district-boundary rule. That's the part that shows judgement, and it's the part most people building on open data get wrong.
