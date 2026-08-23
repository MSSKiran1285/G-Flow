# O2C config fixes — GP01/1000/1001 (live system)

This documents the exact customizing changes made to unblock the O2C chain
(`VA01` → `VL01N` → PGI → `VF01`) on the **existing** `GP01`/plant `1000`/`1001`
environment, after the decision to reuse it (see `docs/assumptions.md`, "Why build
new instead of fixing GP01/1000/1001" in `config-blueprint-o2c-p2p.md`) was reversed —
see that file's status note. All three fixes below are real customizing changes, each
found by reading the live error and the live config tables, not guessed.

## Why two different company codes are involved

Plant `1001`'s **valuation area** (`T001K.BWKEY = 1001`) belongs to company code
**`USAG`** (chart of accounts `SKY1`), which is why the goods-issue posting (fix 1)
lives under `USAG`/`SKY1`. The delivery's **sales organization** is `GP01`, and a
billing document's company code is derived from the sales org, not the delivery
plant's valuation area — so the billing document (`VBRK-BUKRS`) came out as `GP01`,
and fixes 2–3 are `GP01`-side. This split is a real, pre-existing property of this
sandbox's org structure, not something introduced by these fixes.

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

## End-to-end verification (live, this session)

| Step | Document | Verification |
|---|---|---|
| Order | (pre-existing) `1979` | — |
| Delivery | `80001138` | `VL02N` → Post Goods Issue succeeded |
| PGI status | — | `VBUK.WBSTK = 'C'`, `KOSTK = 'C'` (both completed) |
| Billing | `90001003` | `VF01`, net value 541,00 USD |
| Accounting release | — | `VBRK.RFBSK` went from blank → `'C'` after `ReleaseToAccounting` |
| FI document | `100000017` / FY2026 / type `RV` | `BKPF`, `AWTYP='VBRK'`, `AWKEY='0090001003'` |

This is the first time this project's O2C chain has produced a real FI accounting
document — order through delivery through goods issue through billing through FI
posting, all live, all in the existing `GP01`/`1000`/`1001` environment (no new
company code/plant was needed).
