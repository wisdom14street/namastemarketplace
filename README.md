# namastemarketplace.com

Wholesale-only site for Namaste Bookshop's B2B program (a Wealth Edge Ventures Inc. business). Order builder (static/assets/cart.js) hands off to the namastebookshop.com cart via a cart permalink with storefront=true and attributes[Storefront]=namastemarketplace.com, attributes[Order type]=Wholesale.

- `site/catalog_seed.json`: product handles, per-item minimums and fixed prices copied read-only from the Shopify "Namaste Wholesale" catalog/price list. Re-export it when the catalog changes.
- `scripts/build.py`: builds all pages; pulls retail price, photo and stock daily from the public namastebookshop.com product JSON.
- Apply form posts to namastebookshop.com/contact (the same Shopify contact inbox the existing wholesale page uses).
- Sign in: namastebookshop.com/account/login (Shopify customer accounts). Approved buyers see the wholesale price list automatically.
- GA4 G-Y7R5K9NMW0 with site_brand "Namaste Marketplace"; events in `static/assets/site.js` and the shared `ga.js`.
- `site/pricelist.json`: the Namaste Wholesale price-list rule (50% PERCENTAGE_DECREASE, fixed tarot prices, per-variant minimums) exported from Shopify, plus every variant's verified wholesale price. The daily build applies the rule to live retail prices and fails if any unchanged variant disagrees with the export. Re-export it whenever the price list, fixed prices or minimums change in Shopify (the GitHub Action has no Admin API access).
