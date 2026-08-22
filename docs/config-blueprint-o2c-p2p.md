# Configuration Blueprint: New O2C + P2P Environment

**Status: ✅ Finalized — verification checkpoints confirmed live, execution in
progress.** Scope, approach, and depth were explicitly chosen: **build new** (not fix
the existing GP01/1000/1001 setup), **blueprint first** (this document, reviewed before
execution), **minimal viable** (just enough to prove one full O2C and one full P2P
chain, not IDES-parity breadth).

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

## Verification checkpoints — confirmed live, read-only, before executing anything

- **`SM01` is already taken as a company code** ("SM01 Private Limited") — the
  originally proposed code had to change. **`MBT1`** (Model-Based Testing 1) is
  confirmed free as a company code (`T001`), sales org (`TVKO`), plant (`T001W`), and
  purchasing org (`T024E`).
- **`GP01`'s own FI profile** (`T001`): country `US`, currency `USD`, fiscal year
  variant `K4`, chart of accounts `CANA`.
- **Tax procedure for country `US`** (`T005`): `USTAX1`. Only two tax codes exist under
  it (`T007A`): `E1` ("US01 Input tax 10%") and **`E0`** (blank description — the
  zero-rate placeholder to use for the minimal build). Whether `E0` is valid for both
  sales (output) and purchasing (input) contexts will be confirmed live the first time
  each transaction's own F4 help is checked, rather than assumed.
- **Vendor reconciliation account**: existing vendors under `GP01` (`LFB1`) mostly use
  `211000` — that's the account the new vendor will use.
- **Material `103`**'s checking group (`MARC.MTVFP`) is `02`, loading group `LADGR` is
  `0001` (consistent with everything else this session), and MRP type `DISMM` is `ND`
  (not planned — pure sales test material, no MRP run needed). Item category group
  (`MVKE.MTPOS`) is `NORM` (standard) — nothing exotic to carry over.
- **Pricing procedure determination**: not resolved from `T683V` as originally assumed
  — that table turned out to hold SD costing-sheet fields (`KALVG`/`KALKS`/`KALNB`),
  not the pricing-procedure-determination table. Deferred to a live checkpoint during
  O2C execution (`VA01` on the new sales area) rather than guessed from the wrong table.

## New objects to create

| Object | Code | Notes |
|---|---|---|
| Company code | `MBT1` | Chart of accounts `CANA`, currency `USD`, fiscal year variant `K4`. |
| Plant | `MBT1` | Assigned to company code `MBT1`. Address is a placeholder — doesn't feed legal control the way it did for the old plant `1000`, since we're not reusing a real-but-mislabeled address. |
| Storage location | `0001` | Under plant `MBT1`. Non-WM-managed (avoid plant `1000`'s `WMS1`-style complexity). |
| Sales organization | `MBT1` | Assigned to company code `MBT1`. |
| Purchasing organization | `MBT1` | Assigned to company code `MBT1`, and to plant `MBT1` for plant-specific procurement. |
| Shipping point | `MBT1` | Dedicated 1:1 to plant `MBT1` — deliberately not shared with any other plant, to structurally rule out the "delivery split" scenario that blocked Phase 1. |
| Posting period variant | `MBT1` | Assigned only to company code `MBT1`. All 12 periods open for 2026 (and a buffer year either side) — this directly avoids the "period 2026/08 closed" blocker hit in Phase 1. |
| Vendor | new, SAP-assigned or `MBT001` if external numbering is required | `XK01`, purchasing org `MBT1`, company code `MBT1`, reconciliation account `211000`. |

## Assignments (the actual IMG work) — execution order

1. **Define company code `MBT1`** (`OX02`), assign chart of accounts `CANA`, currency
   `USD`, fiscal year variant `K4`.
2. **Create posting period variant `MBT1`, assign to company code `MBT1`, open all
   periods** — done early; it's cheap and prevents rediscovering the fiscal-period trap.
3. **Define plant `MBT1`** (`OX10`), assign to company code `MBT1` (`OX18`).
4. **Define storage location `0001`** under plant `MBT1` (`OX09`).
5. **Define valuation area = plant `MBT1`**, set its valuation grouping code
   (`T001K.BWMOD`) to **`0001`** explicitly — the single step that prevents recreating
   the `SKY1` problem.
6. **Define sales organization `MBT1`**, assign to company code `MBT1`, assign
   distribution channel `G1` and division `D1` to it, set up sales area
   `MBT1`/`G1`/`D1`.
7. **Assign plant `MBT1` to sales org `MBT1` + distribution channel `G1`.**
8. **Assign order type `OR` as permitted for sales area `MBT1`/`G1`/`D1`.**
9. **Create shipping point `MBT1`**, assign it to plant `MBT1`.
10. **Add one shipping-point-determination entry**: shipping condition `01` + loading
    group `0001` + plant `MBT1` → shipping point `MBT1`. One row, one plant, one
    shipping point — no ambiguity possible.
11. **Define purchasing organization `MBT1`** (`OX08`), assign to company code `MBT1`,
    assign to plant `MBT1`.
12. **Resolve and assign the pricing procedure for sales area `MBT1`/`G1`/`D1`** —
    live checkpoint (see above), not yet a known value.
13. **Create vendor** (`XK01`) with purchasing org `MBT1`, company code `MBT1`,
    reconciliation account `211000`.
14. **Extend customer `2`** (shipping condition `01`, already proven in Phase 1) **to
    sales area `MBT1`/`G1`/`D1`.**
15. **Extend material `103` to plant `MBT1`**: Sales/Plant view (storage location
    `0001`), MRP view (checking group `02` should carry over), Accounting view
    (valuation class `7920`), Purchasing view (needed for P2P).

## What this deliberately does NOT cover (minimal-viable scope)

- **Tax**: use zero-rate code `E0`, sidestepping tax-procedure/jurisdiction
  configuration entirely. A real O2C/P2P build would need more than this, but it's out
  of scope for "prove one chain works."
- **Credit management**: assumed off / not blocking, since nothing in Phase 1 hit a
  credit check. Verify live in the first order-creation attempt; add a credit control
  area only if actually needed.
- **Multiple plants, storage locations, order types, or pricing conditions** — one of
  each, deliberately, to keep the surface area small.
- **Warehouse Management** — storage location `0001` is intentionally not WM-managed,
  avoiding plant `1000`'s `WMS1`-style pick/putaway complexity entirely.

## The two chains this unlocks

**O2C**: `VA01` (order type `OR`, sales org `MBT1`, plant `MBT1`, customer `2`,
material `103`) → `VL01N` (shipping point `MBT1` auto-determines cleanly — one
plant, one shipping point) → Post Goods Issue (storage location `0001` already
assigned, checking group already present from the reference material, posting period
already open) → `VF01` (billing — `BSX`/`GBB` account determination already resolves
under grouping `0001`).

**P2P**: `ME21N` (purchasing org `MBT1`, plant `MBT1`, the new vendor, material `103`)
→ `MIGO` (goods receipt — `BSX` resolves under grouping `0001`) → `MIRO` (invoice
verification — `WRX` clears against `211200`).

## Rollback / blast-radius notes

Every new object above is either brand new (safe — nothing else references it yet) or
an *extension* of an existing customer/material to a new sales area/plant (additive —
doesn't change that customer's or material's existing GP01/1000/1001 data). The one
touch to shared config is step 5 (valuation area `MBT1`'s own grouping code), which is
scoped to the new plant only and doesn't alter any existing plant's grouping. Nothing
in this blueprint modifies `GP01`, `1000`, `1001`, or any existing OBYC entry.

## Execution log

Filled in as each step is actually done live — see `docs/assumptions.md` for the
detailed narrative (tcodes used, exact screens, any deviation from this plan).
