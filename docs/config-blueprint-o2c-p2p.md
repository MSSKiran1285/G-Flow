# Configuration Blueprint: New O2C + P2P Environment

**Status: 📋 Blueprint — nothing in this document has been executed.** Per direct
discussion, this is the design to review before any SPRO/config change is made live.
Scope, approach, and depth were explicitly chosen: **build new** (not fix the existing
GP01/1000/1001 setup), **blueprint first** (this document), **minimal viable** (just
enough to prove one full O2C and one full P2P chain, not IDES-parity breadth).

## Why build new instead of fixing GP01/1000/1001

Phase 1 (see `docs/assumptions.md`) found the existing sandbox has several deep,
cross-cutting inconsistencies that took a full investigation session each to diagnose:

- Plant `1000`'s legal-control block is real (its address is a genuine, self-consistent
  UK location) — not fixable without fabricating data.
- Plant `1001` resolves to a valuation-grouping code (`SKY1`) that isn't traceable to
  its own master data (`T001K.BWMOD` is blank) and belongs to a different company code
  (`USAG`) than its own sales org (`GP01`) — an unexplained cross-company assignment.
- Getting one delivery working took root-causing a shipping-point mismatch; getting
  goods issue working took three more sequential fixes; billing is still blocked.

None of that is a framework problem — it's this specific sandbox's accumulated history.
A new, small, self-consistent environment sidesteps all of it by construction rather
than by continuing to discover and patch one gap at a time.

## Design principle: reuse what's already proven, mint only what's new

The biggest cost driver in a real SAP configuration build is inventing new financial
account determination (`OBYC`) — deciding real G/L account numbers is a genuine FI
judgment call, not something to fabricate. This blueprint avoids that entirely by
**reusing the existing chart of accounts (`CANA`) and reusing a valuation-grouping code
that already has complete account determination**, confirmed live (read-only, no
changes made) this session:

| Transaction key | Purpose | Confirmed accounts under `CANA`, grouping `0001` |
|---|---|---|
| `BSX` | Inventory posting | valuation class `3000` → `131000`; class `7920` → `134000` |
| `GBB` | Offsetting entry (goods issue/receipt) | class `3000` → `510040`; class `7920` → `510040` (`ZOB`/general mod.) |
| `WRX` | GR/IR clearing (not valuation-class-dependent) | `211200` |

All three of O2C's goods-issue posting, P2P's goods-receipt posting, and P2P's invoice
verification clearing already have real, working accounts under grouping `0001`. **No
new G/L accounts and no new OBYC entries need to be created.** The only finance-side
config step is making sure the *new* plant's own valuation area resolves to grouping
`0001` instead of whatever produces `SKY1` for the old plant.

Similarly, reuse rather than recreate:
- **Valuation class `7920`** and a copy of **material `103`**'s master data — it's the
  one material proven this session to have a complete MRP/checking-group setup (no
  "missing checking group" incompleteness, unlike material `97`).
- **Distribution channel `G1`**, **division `D1`**, **order type `OR`**, **delivery
  type `LF`**, **billing type `F2`**, **shipping condition `01`**, **loading group
  `0001`** — all already exist and are already proven live; a new sales org/plant only
  needs to be *assigned* to them, not have them recreated.
- **Fiscal year variant `K4`** (calendar year, already used by `GP01`) and **currency
  `USD`**.

What's genuinely new: one company code, one plant, one sales org, one purchasing org,
one shipping point, one storage location, one posting-period variant, one vendor, plus
the assignments wiring them together and extending one customer + one material into
the new structure.

## New objects to create

| Object | Proposed code | Notes |
|---|---|---|
| Company code | `SM01` | Assign chart of accounts `CANA`, currency `USD`, fiscal year variant `K4`. **Verify `SM01` is free before use** (`T001`) — not confirmed free, this is a proposal, not a reservation. |
| Plant | `SM01` | Assign to company code `SM01`. Address can be a placeholder — doesn't feed legal control the way it did for the old plant `1000`, since we're not reusing a real-but-mislabeled address. |
| Storage location | `0001` | Under plant `SM01`. Non-WM-managed (avoid plant `1000`'s `WMS1`-style complexity). |
| Sales organization | `SM01` | Assign to company code `SM01`. |
| Purchasing organization | `SM01` | Assign to company code `SM01`, and to plant `SM01` for plant-specific procurement. |
| Shipping point | `SM01` | Dedicated 1:1 to plant `SM01` — deliberately not shared with any other plant, to structurally rule out the "delivery split" scenario that blocked Phase 1. |
| Posting period variant | `SM01` (or reuse if an already-fully-open one exists — verify during execution) | Assigned only to company code `SM01`. All 12 periods open for the relevant fiscal year(s) — this directly avoids the "period 2026/08 closed" blocker hit in Phase 1. |
| Vendor | one new vendor, e.g. `SM0001` | Created via `XK01`, purchasing org `SM01`, company code `SM01`. |

## Assignments (the actual IMG work)

In dependency order — each step needs the previous one to exist:

1. **Define company code `SM01`** (`OX02`), assign chart of accounts `CANA`, currency
   `USD`, fiscal year variant `K4` (`OB37`-family assignments).
2. **Create posting period variant, assign to `SM01`, open all periods** (`OB29`/`OBBO`
   family) — do this early; it's cheap and prevents rediscovering the fiscal-period
   trap from Phase 1.
3. **Define plant `SM01`** (`OX10`), assign to company code `SM01` (`OX18`).
4. **Define storage location `0001`** under plant `SM01` (`OX09`).
5. **Define valuation area = plant `SM01`**, set its valuation grouping code
   (`T001K.BWMOD`) to **`0001`** explicitly (`OMWD`/`OMWN` — "Group Together Valuation
   Areas" must be active and grouping code set, matching the code already proven to
   have complete `BSX`/`GBB`/`WRX` coverage). **This is the single step that prevents
   recreating the `SKY1` problem.**
6. **Define sales organization `SM01`** (`OVX5`/`enterprise structure`), assign to
   company code `SM01`, assign distribution channel `G1` and division `D1` to it, set
   up the sales area `SM01`/`G1`/`D1`.
7. **Assign plant `SM01` to sales org `SM01` + distribution channel `G1`** (plant/sales
   area assignment — this is what lets `VA01` accept plant `SM01` as a delivering
   plant for orders in this sales area).
8. **Assign order type `OR` as permitted for sales area `SM01`/`G1`/`D1`.**
9. **Create shipping point `SM01`**, assign it to plant `SM01`.
10. **Add one shipping-point-determination entry** (`TVSTZ`/`OVL2`-family): shipping
    condition `01` + loading group `0001` + plant `SM01` → shipping point `SM01`. One
    row, one plant, one shipping point — no ambiguity possible.
11. **Define purchasing organization `SM01`** (`OX08`), assign to company code `SM01`,
    assign to plant `SM01` (plant-specific purchasing).
12. **Assign pricing procedure for the new sales area**: copy the existing
    `Doc.Pricing Proc` + `Cust.Pricing Proc` → `Procedure` entry already used by
    `GP01`/`G1`/`D1` (verify the exact procedure name live — not yet confirmed which
    one `GP01` uses) into a new entry for `SM01`/`G1`/`D1`.
13. **Create vendor `SM0001`** (`XK01`) with purchasing org `SM01`, company code
    `SM01`, reconciliation account matching whatever `CANA` uses for trade payables
    (verify live).
14. **Extend an existing, proven customer** (e.g. customer `2`, shipping condition
    `01`, already used successfully in Phase 1) **to the new sales area**
    `SM01`/`G1`/`D1` (`XD01`/`VD01` "extend to sales area").
15. **Extend material `103`** (or copy it as a new material via `MM01` with reference)
    **to plant `SM01`**: Sales/Plant view (assign storage location `0001`, delivery
    plant), MRP view (verify checking group carries over from the reference), Accounting
    view (valuation class `7920`, standard price or moving average — verify), Purchasing
    view (needed for the P2P side).

## What this deliberately does NOT cover (minimal-viable scope)

- **Tax**: use a zero-rate / no-tax code (e.g. `I0`/`O0`) if one already exists and is
  usable without jurisdiction setup, sidestepping tax-procedure/jurisdiction
  configuration entirely. Flagged explicitly — a real O2C/P2P build would need this,
  but it's out of scope for "prove one chain works."
- **Credit management**: assumed off / not blocking, since nothing in Phase 1 hit a
  credit check. Verify live in the first order-creation attempt; add a credit control
  area only if actually needed.
- **Multiple plants, storage locations, order types, or pricing conditions** — one of
  each, deliberately, to keep the surface area small.
- **Warehouse Management** — storage location `0001` is intentionally not WM-managed,
  avoiding plant `1000`'s `WMS1`-style pick/putaway complexity entirely.

## The two chains this unlocks

**O2C**: `VA01` (order type `OR`, sales org `SM01`, plant `SM01`, customer `2`,
material `103`) → `VL01N` (shipping point `SM01` auto-determines cleanly — one
plant, one shipping point) → Post Goods Issue (storage location `0001` already
assigned, checking group already present from the reference material, posting period
already open) → `VF01` (billing — `BSX`/`GBB` account determination already resolves
under grouping `0001`).

**P2P**: `ME21N` (purchasing org `SM01`, plant `SM01`, vendor `SM0001`, material `103`)
→ `MIGO` (goods receipt — `BSX` resolves under grouping `0001`) → `MIRO` (invoice
verification — `WRX` clears against `211200`).

## Verification checkpoints before executing

A handful of facts this blueprint assumes but hasn't verified live — check these first,
each is cheap (a `read-table`/`SE16N` lookup) and would change a proposed code or value
if wrong:

- `SM01` (and `SM0001`) are actually free/unused company-code, plant, sales-org,
  purchasing-org, and vendor codes.
- The exact pricing procedure `GP01`/`G1`/`D1` currently resolves to (to replicate for
  `SM01`/`G1`/`D1`).
- The reconciliation account `CANA` uses for trade payables (for the new vendor).
- A usable zero-tax code exists and doesn't itself require jurisdiction data.
- Material `103`'s current checking group and item category group, to confirm they
  carry over cleanly when extended to a new plant.

## Rollback / blast-radius notes

Every new object above is either brand new (safe — nothing else references it yet) or
an *extension* of an existing customer/material to a new sales area/plant (additive —
doesn't change that customer's or material's existing GP01/1000/1001 data). The one
touch to shared config is step 5 (valuation area `SM01`'s own grouping code), which is
scoped to the new plant only and doesn't alter any existing plant's grouping. Nothing
in this blueprint modifies `GP01`, `1000`, `1001`, or any existing OBYC entry.
