# Roadmap

This document tracks ongoing architectural work so contributors know what's stable, what's in progress, and what pattern to follow depending on the area of the codebase they're touching.

## HTMX migration

We're progressively moving dynamic interactions away from custom `fetch` + manual DOM manipulation, toward server-rendered partials swapped in via HTMX. The goal is to let Django remain the single source of truth for state (totals, cart contents, availability) instead of duplicating that logic in JavaScript.

### Current state

| Feature | Status | Notes |
|---|---|---|
| Remove item from cart | ✅ Done | Returns `_cart_content.html` partial, triggers `cartUpdated` via `HX-Trigger` |
| Cart item count (navbar) | ✅ Done | Listens for `cartUpdated from:body` |
| Clear cart | ✅ Done | Same pattern as remove item |
| Add to cart (from catalog) | 🚧 In progress | Being worked on in `refactor/js` |
| Catalog filtering | ⏳ Not started | Still relies on the legacy approach |

### Pattern to follow for new HTMX work

If you're migrating a feature to HTMX, follow the pattern established for the cart:

1. The view detects `request.headers.get('HX-Request')` and returns a partial template instead of JSON
2. The partial includes everything that needs to update visually (list, totals, empty-state message)
3. If something outside the swapped container also needs updating (e.g. a cart count in the navbar), set an `HX-Trigger` header from the view and have the relevant element listen via `hx-trigger="eventName from:body"`
4. Any JavaScript that attaches event listeners to elements inside a swapped container must be re-run after the swap, via a `htmx:afterSwap` listener scoped to the container's ID — see `initCart()` in `core/script.js` for a reference implementation
5. Avoid recalculating things in JavaScript that the server can compute and render directly (e.g. totals); JS should only handle UI-only state (checkbox toggles, client-side validation feedback)

### Why this matters for contributors

If you're touching `catalog` or `cart` templates/JS and you're unsure which pattern applies to the specific page you're working on, check this table first, or ask in your pull request. We'd rather pause and confirm the approach than have two competing patterns drift further apart.

This roadmap will be trimmed down once the migration is complete and the HTMX pattern can be documented as a stable convention in [CONTRIBUTING.md](CONTRIBUTING.md) instead.

## JavaScript — per-app separation (planned, after HTMX migration)
 
Once the HTMX migration above is complete, JavaScript will be split by ownership instead of living in one or two large files:
 
- `core/script.js` keeps only what's truly global (navbar, language switch, overlay)
- App-specific JS (cart, catalog) moves into its own app, loaded via `{% block extra_js %}` only on the pages that need it
This avoids loading cart-specific JS on pages that have nothing to do with the cart, and keeps each app self-contained.
 
## CSS — approach not yet decided
 
Once JS separation settles, we'll revisit CSS organization. Two directions are being considered, not yet decided:
 
- Mirror the JS approach: split CSS per app instead of one global stylesheet
- Or move to a utility-first approach (e.g. Tailwind) instead
No decision yet — if you have strong opinions, feel free to open an issue to discuss before starting any related work.
 
## SEO
 
- Set up a Google Business Profile (the "fiche établissement" / Google My Business listing) and link it to the site
- Run a full Screaming Frog crawl to catch broken links, missing metadata, duplicate titles/descriptions, etc.

## Dedicated product pages (replacing the modal)
 
Currently, product details are shown in a modal (`catalog/components/_modal.html`) rather than on a dedicated URL. The plan is to replace this with a real page per product.
 
Motivation:
- A modal has no indexable URL, so each product currently contributes nothing to search rankings on its own
- A dedicated page allows for longer, richer descriptions and better keyword coverage than what fits comfortably in a modal
- Each product gets its own shareable link, proper meta tags, and can appear directly in search results
This is a significant change (routing, templates, likely a new `ProductDetailView`) rather than a quick tweak — not started yet. If you want to pick this up, open an issue first to align on URL structure (e.g. `/produits/<category>/<slug>/`) and whether the modal should be fully removed or kept for a quick-view interaction alongside the new page.

## Internationalization
 
- Investigate `django-parler` (or a similar solution) for translating product descriptions, rather than the current approach
## Tests — coverage gaps
 
- `get_product_images` has no test coverage yet
- `legal` app views have no test coverage yet
- 
## Known bugs
 
### Stripe metadata size limit with large carts
 
When a cart contains many items, checkout fails with:
 
```
ERROR Stripe error: Metadata values can have up to 500 characters, 
but you passed in a value that is 1660 characters.
```
 
Stripe metadata values are capped at 500 characters. We're currently passing a JSON-serialized list of items (name + image URL) as a single metadata value, which overflows once the cart has enough items. Needs investigation — likely solutions include splitting the payload across multiple metadata keys, storing only product IDs and reconstructing details server-side after payment, or storing the cart snapshot elsewhere (DB) and referencing it by ID in metadata instead.
 
## Other planned work
 
_Add other in-progress architectural efforts here as they come up (e.g. template restructuring)._