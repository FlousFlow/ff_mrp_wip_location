# Odoo 20 Engineering Log

## Architecture decision

The addon inherits `mrp.production._compute_location_dest_id` and keeps the
native picking type destination as the default. Only a product template marked
`ff_under_processing` can replace it, and only with a valid company-compatible
internal location.

## Safety boundaries

- No Odoo core files are changed.
- No routes are globally replaced.
- By-products remain on their native destination.
- Accounting and stock valuation methods are not overridden.
- Missing or invalid configuration is rejected at confirmation and completion.

## Verification

The addon was installed on a clean Odoo 20 Community database and upgraded on
the local demo database. The module test tag completed with 0 failed and 0
errors across 9 module tests. The demo database also contains unrelated legacy
`flousflow_accounting` model warnings; they are outside this addon.
