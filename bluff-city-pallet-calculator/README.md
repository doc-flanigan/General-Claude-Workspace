# Bluff City Pallet — Quote Calculator (Demo)

An interactive, single-file pallet pricing demo built to show the partners of
**Bluff City Pallet** (Memphis, TN). No build step, no dependencies — just open
`index.html` in any browser.

## What it does

**Order Quote tab**
- Pick pallet size (48×40 GMA standard, 48×48, 42×42, 36×36)
- Pick grade: New / Grade A recycled / Grade B recycled
- Enter quantity — volume discounts kick in automatically at 500 / 1,000 / 2,500
- Add-ons: heat treatment (ISPM-15 export stamp) and block-style 4-way
- Delivery distance from Memphis (free inside 30 miles)
- Live total, per-pallet delivered cost, and **savings vs. all-new**
- "Email this quote" button drafts a ready-to-send message

**Truckload Estimator tab**
- Estimates how many pallets fit per truckload by footprint, stack height,
  and trailer size (53′ / 48′ / 28′)

## Showing it to the partners

Just double-click `index.html`. Everything runs locally in the browser, so it
works on a laptop with no internet at a meeting.

## Making the numbers real

All pricing lives in one place — the `PRICING`, `ADDONS`, `BREAKS`,
`FREE_MILES`, and `PER_MILE` constants at the top of the `<script>` block in
`index.html`. Drop in Bluff City's actual rate card and the whole calculator
updates. The sample numbers shipped here are illustrative only.

> This is a sales/marketing demo, not a binding quote tool.
