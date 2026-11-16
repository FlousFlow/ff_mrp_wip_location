# Flous Flow — Manufacturing WIP Location

Odoo 20 Community addon that routes the **main finished product** of selected
manufacturing orders to a company-level Work in Progress (WIP) location.

## Configuration

1. Open **Manufacturing → Configuration → Settings**.
2. Set **Work in Progress Location** to an active internal location for the
   current company (or a shared location).
3. Open a product template and enable **Under Processing**.

The setting is opt-in. Products without the flag retain the standard Odoo
finished-product destination. By-products are not rerouted.

## Validation and accounting

The module blocks confirmation and completion when a flagged product has no
valid WIP location. It changes only the stock destination; it does not create
or alter accounting/valuation logic.

## Compatibility

The implementation extends Odoo's native manufacturing destination computation
and confirmation/completion hooks. Standard one-step, two-step, and three-step
warehouse configurations continue to use Odoo's native route logic; the main
finished move is directed to the configured internal WIP location.

By-products are explicitly restored to the native operation destination, while
the selected main finished product is the only move routed to WIP. The addon
does not create journals, valuation adjustments, transfers, or custom routes.

## Development

Run the addon tests with the Odoo 20 Python environment:

```bash
./odoo-bin -d <database> -i ff_mrp_wip_location --test-enable \
  --test-tags /ff_mrp_wip_location --stop-after-init
```

The automated suite covers standard routing, missing/archived configuration,
draft product changes, completed production, partial production/backorders,
by-products, shared locations, and cross-company protection. The exact
warehouse route variants and lot/serial UI flows remain dependent on the
warehouse configuration used by the target database and should be smoke-tested
there before production rollout.
