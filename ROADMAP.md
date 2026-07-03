# Roadmap

This document tracks ongoing architectural work so contributors know what's stable, what's in progress, and what pattern to follow depending on the area of the codebase they're touching.

---

## Current focus — SEO

The site has undergone significant structural work (HTMX migration, dedicated product pages, i18n with `django-modeltranslation`). The current priority is getting the French content indexed properly by Google, then progressively rolling out English.

### Phase 1 — Static content (in progress)

Updating all translatable static strings (H1s, page titles, meta-descriptions) with keyword-optimized copy based on keyword research. This covers the homepage, category pages (leather, macramé, hybrid) and custom-creation page.

- Run `makemessages` and `compilemessages` once all static strings are finalized
- Deploy → Google indexes updated static pages

### Phase 2 — French product content (next)

Rewrite `name_fr`, `meta_description_fr` and `description_fr` for each product with SEO-optimized copy. Roll out by category, in this order:

| Category | Content ready | In sitemap | Indexed |
|---|---|---|---|
| Leather (Maroquinerie) | ⏳ | ⏳ | ⏳ |
| Macramé | ⏳ | ⏳ | ⏳ |
| Hybrid (Hybride) | ⏳ | ⏳ | ⏳ |

For each category:
1. Rewrite product names, meta description and descriptions in French with keyword-optimized copy
2. Switch product detail pages from `noindex` to `index` for that category
3. Add those URLs to the sitemap
4. Submit sitemap to Google Search Console

### Phase 3 — English product content (later)

Once keyword research for English is complete, fill in `name_en`, `meta_description_en` and `description_en` for each product. Same rollout order as Phase 2 (leather → macramé → hybrid).

**Do not start Phase 3 before keyword research is done** — translating now without keyword intent would mean rewriting everything again later, and could generate URLs that need redirecting if slugs change.

### Phase 4 — Google Business Profile

Set up the Google Business Profile ("fiche établissement") and link it to the site once the French product content is indexed.

---

## HTMX migration

We're progressively moving dynamic interactions away from custom `fetch` + manual DOM manipulation, toward server-rendered partials swapped in via HTMX. The goal is to let Django remain the single source of truth for state (totals, cart contents, availability) instead of duplicating that logic in JavaScript.

### Current state

| Feature | Status | Notes |
|---|---|---|
| Remove item from cart | ✅ Done | Returns `_cart_content.html` partial, triggers `cartUpdated` via `HX-Trigger` |
| Cart item count (navbar) | ✅ Done | Listens for `cartUpdated from:body` |
| Clear cart | ✅ Done | Same pattern as remove item |
| Add to cart (from catalog) | ✅ Done | Returns `_product_card.html` partial, triggers `cartUpdated`; product modal's button removed |
| Catalog filtering | ⏳ Not started | Still relies on the legacy approach |

### Pattern to follow for new HTMX work

If you're migrating a feature to HTMX, follow the pattern established for the cart:

1. The view detects `request.headers.get('HX-Request')` and returns a partial template instead of JSON
2. The partial includes everything that needs to update visually (list, totals, empty-state message)
3. If something outside the swapped container also needs updating (e.g. a cart count in the navbar), set an `HX-Trigger` header from the view and have the relevant element listen via `hx-trigger="eventName from:body"`
4. Any JavaScript that attaches event listeners to elements inside a swapped container must be re-run after the swap, via a `htmx:afterSwap` listener scoped to the container's ID — see `initCart()` in `core/script.js` for a reference implementation
5. Avoid recalculating things in JavaScript that the server can compute and render directly (e.g. totals); JS should only handle UI-only state (checkbox toggles, client-side validation feedback)

This roadmap will be trimmed down once the migration is complete and the HTMX pattern can be documented as a stable convention in [CONTRIBUTING.md](CONTRIBUTING.md) instead.

---

## JavaScript — per-app separation (planned, after HTMX migration)

Once the HTMX migration above is complete, JavaScript will be split by ownership instead of living in one or two large files:

- `core/script.js` keeps only what's truly global (navbar, language switch, overlay)
- App-specific JS (cart, catalog) moves into its own app, loaded via `{% block extra_js %}` only on the pages that need it

This avoids loading cart-specific JS on pages that have nothing to do with the cart, and keeps each app self-contained.

---

## CSS — approach not yet decided

Once JS separation settles, we'll revisit CSS organization. Two directions are being considered, not yet decided:

- Mirror the JS approach: split CSS per app instead of one global stylesheet
- Or move to a utility-first approach (e.g. Tailwind) instead

No decision yet — if you have strong opinions, feel free to open an issue to discuss before starting any related work.

---

## Product detail pages

Dedicated product pages (`catalog/product_detail.html`) have replaced the modal. Each product now has its own indexable URL with slug + product ID.

Current state:
- ✅ FR pages built and deployed
- ✅ URL structure: `/produits/<category>/<slug>-<product_id>/`
- ✅ Slug computed on the fly via `slugify(product.name)` — no extra DB field
- ✅ `hreflang` FR/EN correctly set per product page
- ⏳ FR pages currently `noindex` — will be switched to `index` progressively (see SEO phases above)
- ⏳ EN pages pending keyword research and content

### AI-assisted translation (planned)

To help the client fill in `name_en`/`description_en`, we plan to integrate an LLM-based translation tool directly in the Django admin. Rather than plain translation, the prompt will incorporate SEO keyword targets so the output is keyword-aware, not just a literal translation. The client would review and approve before publishing. Not started yet — open an issue to discuss scope before picking this up.

---

## Internationalization

- ✅ Static strings (UI labels, buttons) — Django `.po`/`.mo` files, managed by the developer
- ✅ Product content (`name`, `description`) — `django-modeltranslation`, managed by the client via Django admin
- ⏳ English product content — pending keyword research (see SEO Phase 3 above)

---

## Tests — coverage gaps

- `get_product_images` has no test coverage yet
- `legal` app views have no test coverage yet

---

## Known bugs

### Stripe metadata size limit with large carts

When a cart contains many items, checkout fails with:

```
ERROR Stripe error: Metadata values can have up to 500 characters,
but you passed in a value that is 1660 characters.
```

Stripe metadata values are capped at 500 characters. We're currently passing a JSON-serialized list of items (name + image URL) as a single metadata value, which overflows once the cart has enough items. Needs investigation — likely solutions include splitting the payload across multiple metadata keys, storing only product IDs and reconstructing details server-side after payment, or storing the cart snapshot elsewhere (DB) and referencing it by ID in metadata instead.

---

## Developer onboarding — Docker

Setting up the project locally currently requires several manual steps (venv, dependencies, `.env`, migrations, fixtures). A `docker-compose` setup could collapse this into a single `docker-compose up`, with a consistent environment across all contributors regardless of their OS or local Python version.

Not started yet. If you want to pick this up, open an issue first to discuss scope — e.g. whether to containerize just the app + SQLite, or also add a Postgres service to better mirror considerations for a future production database change.

This wouldn't replace the pre-commit hook or CI checks — Docker would simplify *running* the app, but linting/testing still happen the same way either way.

---

## Other planned work

_Add other in-progress architectural efforts here as they come up._