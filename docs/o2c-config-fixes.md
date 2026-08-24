# O2C config fixes — GP01/1000/1001 (live system)

This is the complete, consolidated record of every real customizing and master-data
change made in the live SAP instance to get the O2C chain (`VA01` → `VL01N` → PGI →
`VF01`) working on the **existing** `GP01`/plant `1000`/`1001` environment, after the
decision to reuse it (see `docs/assumptions.md`, "Why build new instead of fixing
GP01/1000/1001" in `config-blueprint-o2c-p2p.md`) was reversed — see that file's
status note. Every change below was found by reading the live error and the live
config tables, not guessed, and every one is still live in the system today.

**Customizing changes**: three (OBYC account determination, an FBN1 number-range
interval, an FTXP tax code — fixes 1–3 below), plus two earlier ones from the prior
investigation phase that made the O2C prerequisites reachable at all (the FI/MM
period extensions below). **No SAP object was deleted** as part of any of this.

## Why two different company codes are involved

Plant `1001`'s **valuation area** (`T001K.BWKEY = 1001`) belongs to company code
**`USAG`** (chart of accounts `SKY1`), which is why the goods-issue posting (fix 1)
lives under `USAG`/`SKY1`. The delivery's **sales organization** is `GP01`, and a
billing document's company code is derived from the sales org, not the delivery
plant's valuation area — so the billing document (`VBRK-BUKRS`) came out as `GP01`,
and fixes 2–3 are `GP01`-side. This split is a real, pre-existing property of this
sandbox's org structure, not something introduced by these fixes.

## Fix 0a — `OB52`: GP01's FI posting periods extended through 2030

**Symptom**: order/delivery-side postings for company code `GP01` were at risk of
hitting a closed-period error as soon as the system date moved past whatever period
was last open (this sandbox's period configuration wasn't kept current).

**Fix**: extended `GP01`'s posting period variant so periods through fiscal year
**2030** are open (`OB52`). This is a blanket period-management fix, not tied to any
specific document — it removes fiscal-period closure as a recurring blocker for all
future O2C/P2P work in this sandbox, not just the chain proven this session.

## Fix 0b — `MMPV`: USAG's MM posting period advanced to 08/2026

**Symptom**: goods-movement postings for company code `USAG` (the company code behind
plant `1001`'s valuation area — see below) were blocked by MM's own period-control
table, independent of the FI posting-period variant above. MM periods can only be
advanced **one calendar month at a time** — a direct jump throws "Incorrect period in
control rec. of CoCd USAG; no conversion".

**Fix**: ran `MMPV` twice in sequence (06/2026 → 07/2026, then 07/2026 → 08/2026) for
company code `USAG`, using the "Check and close" mode (the correct default) and the
real Execute toolbar button (not `SEND_VKEY F8`, which doesn't reliably trigger this
particular screen — the toolbar button does and produces a confirmable "Period closing
complete" log each time). This is also a blanket fix: it keeps USAG's MM period
current with the system date, independent of any one document.

## Fix 1 — OBYC: `GBB` account determination for `SKY1` (transaction `OBYC`)

**Symptom**: Post Goods Issue on delivery `80001138` failed with `Account
determination for entry SKY1 GBB ____ VAX not possible` (and, before that, the same
message with `KOMOK=ZOB` — the delivery's goods-issue posting evaluates both
modifiers depending on path).

**Root cause**: `T030` had zero entries for `KTOPL=SKY1, KTOSL=GBB` — the rule
(`T030R`) already correctly required `XKOMO` (general modification) + `XBWMO`
(valuation modifier), not `XBKLA` (valuation class), but no account rows existed at
all.

**Account chosen**: `12003`, chart of accounts `SKY1`. Verified live before use:
- Already exists at company-code level for `USAG` (`SKB1`).
- P&L statement account (`SKA1.XBILK` = blank, `GVTYP` = `X`), the correct type for a
  GBB offsetting entry paired with `BSX` (`12007`, the balance-sheet inventory
  account already in use for material `103`'s valuation class `7920`).
- Named "Expense Account" in `SKAT` and was **not** referenced by any other `T030`
  entry (`BSX`→`12007`, `WRX`→`12004`, `PRD`→`12008` were all already taken) — the
  clear, unused slot for exactly this purpose.

**Entries created** (`T030`, both `BWMOD` blank):

| KTOPL | KTOSL | BWMOD | KOMOK | KONTS |
|---|---|---|---|---|
| SKY1 | GBB | (blank) | VAX | 12003 |
| SKY1 | GBB | (blank) | ZOB | 12003 |

Saved to transport `GECK903480`.

## Fix 2 — `FBN1`: missing number-range interval `49` for `USAG`

**Symptom**: after fix 1, PGI failed with `Interval 49 does not exist for object
RF_BELEG USAG FBN1` — the FI document type used for the goods-issue posting needs
number-range group `49`, which simply didn't exist for this company code.

**Existing intervals for `USAG`** (all through fiscal year 2026): `02`, `03`, `15`,
`17`, `19`, `50`, `51`.

**Interval added**:

| Range | Year | From | To |
|---|---|---|---|
| 49 | 2026 | 0000000700 | 0000000799 |

Chosen to sit in the same small-block numbering pattern as the other custom ranges in
this sandbox, non-overlapping with any existing interval. Number-range intervals are
not auto-transported (SAP's own note on save) — transport them manually via
`Interval → Transport` in `FBN1` if this needs to move to another system.

## Fix 3 — `FTXP`: missing tax code `A0` for procedure `USTAX1`

**Symptom**: the billing document (`VF01`, doc `90001003`) saved but with "no
accounting document generated". `Environment → Acct.determ.analysis → Revenue
accounts`, then a manual `Billing document → ReleaseToAccounting`, surfaced the real
message: `Tax code A0 in procedure USTAX1 is invalid`.

**Root cause**: `USTAX1` only had tax codes `E0` (output, `MWART=A`) and `E1` (input,
`MWART=V`) defined (`T007A`) — `A0` didn't exist under this procedure at all, even
though it's what the billing item's pricing/tax determination resolved to.

**Fix**: created tax code `A0`, mirroring `E0`'s existing structure exactly (same tax
type, same account keys, same 0% rate) since `E0` is the system's working zero-rate
output-tax placeholder and `A0` needed to behave identically for this chain:

| Field | Value |
|---|---|
| Country | US |
| Tax code | A0 |
| Description | Output tax A0 0% |
| Tax type (`MWART`) | A (output tax) |
| Rate rows | `U01`/`US01` @ 0,000 · `U02`/`US02` @ 0,000 (same account keys as `E0`) |

No new G/L accounts needed — `U01`/`U02` were already assigned (via `OB40`) from
`E0`'s existing setup.

## End-to-end verification — run 1 (existing order, first proof after the fixes)

| Step | Document | Verification |
|---|---|---|
| Order | (pre-existing) `1979` | — |
| Delivery | `80001138` | `VL02N` → Post Goods Issue succeeded |
| PGI status | — | `VBUK.WBSTK = 'C'`, `KOSTK = 'C'` (both completed) |
| Billing | `90001003` | `VF01`, net value 541,00 USD |
| Accounting release | — | `VBRK.RFBSK` went from blank → `'C'` **after a manual** `ReleaseToAccounting` (this billing doc was created *before* fix 3, so it needed the manual nudge once the tax code existed) |
| FI document | `100000017` / FY2026 / type `RV` | `BKPF`, `AWTYP='VBRK'`, `AWKEY='0090001003'` |

This was the first time this project's O2C chain produced a real FI accounting
document — order through delivery through goods issue through billing through FI
posting, all live, all in the existing `GP01`/`1000`/`1001` environment (no new
company code/plant was needed).

## End-to-end verification — run 2 (fresh order, created entirely after all fixes)

To confirm the fixes are durable and not one-off patches for delivery `80001138`
specifically, a second chain was run from a **brand-new order**, created after every
fix above was already in place:

| Step | Document | Verification |
|---|---|---|
| Order | **`1983`** (new; customer `3`, material `103`) | `VA01`, saved cleanly once plant `1001` was set on the item (see note below) |
| Delivery | **`80001139`** (new) | `VL01N`, shipping point `GP01`, no split |
| PGI status | — | `VBUK.WBSTK = 'C'`, `KOSTK = 'C'` |
| Billing | **`90001004`** (new) | `VF01`, net value 541,00 USD |
| Accounting release | — | `VBRK.RFBSK = 'C'` **automatically on save** — no manual `ReleaseToAccounting` needed this time |
| FI document | **`100000018`** / FY2026 / type `RV` | `BKPF`, `AWTYP='VBRK'`, `AWKEY='0090001004'` |

The automatic (rather than manual) accounting release on this run is the direct
confirmation that fix 3 (`FTXP` tax code `A0`) is a real, general fix, not something
that only worked once via the manual nudge.

**Incidental finding, not a new gap**: order `1983`'s item-level plant (`VBAP-WERKS`)
didn't auto-default from the customer/material master data this time, unlike orders
`1979`/`1980` — setting it explicitly (`1001`) resolved a cascading incompleteness
(shipping point, route, and all schedule-line dates went blank without it). This is
an intermittent default-resolution behavior in this sandbox's master data, not
something introduced by any fix above.

## Inert leftovers in the system (deliberately not cleaned up)

- **Order `1982`**: an earlier attempt in run 2's session, created with customer `2`
  instead of `3` and abandoned incomplete (same missing-plant symptom as above,
  found before switching to the known-good customer `3` combination). It sits
  incomplete and undelivered — harmless, no downstream document references it.
- **A partial `MBT1` plant rebuild** (via Copy-As from `PM01`, done during the
  earlier "build new environment" attempt before that plan was reversed — see
  `docs/config-blueprint-o2c-p2p.md`'s status note): the plant object exists but
  nothing was ever wired to it (no company code assignment, no sales org, no
  downstream config), so it's inert.

Neither of these was deleted — removing customizing/master-data objects safely needs
the same care as creating them, and neither is in the way of anything.
