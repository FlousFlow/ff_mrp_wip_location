from odoo import _, api, models
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.depends(
        'picking_type_id',
        'product_id.ff_under_processing',
        'company_id.ff_wip_location_id',
    )
    def _compute_location_dest_id(self):
        super()._compute_location_dest_id()
        for production in self:
            if not production.product_id.product_tmpl_id.ff_under_processing:
                continue
            location = production.company_id.ff_wip_location_id
            if production._ff_is_valid_wip_location(location):
                production.location_dest_id = location

    def _ff_is_valid_wip_location(self, location):
        self.ensure_one()
        return bool(
            location
            and location.active
            and location.usage == 'internal'
            and (not location.company_id or location.company_id == self.company_id)
        )

    def _ff_get_standard_finished_destination(self):
        """Return the destination Odoo would use before the WIP override."""
        self.ensure_one()
        location = self.picking_type_id.default_location_dest_id
        if not location:
            company = self.company_id if self.company_id in self.env.companies else self.env.company
            location = self.env['stock.warehouse'].search(
                [('company_id', '=', company.id)], limit=1
            ).lot_stock_id
        return location

    def _ff_get_wip_location_or_raise(self):
        self.ensure_one()
        location = self.company_id.ff_wip_location_id
        if not self._ff_is_valid_wip_location(location):
            raise UserError(_(
                'Please configure the Work in Progress Location in Manufacturing '
                'Settings before confirming this manufacturing order.'
            ))
        return location

    def _ff_validate_wip_configuration(self):
        for production in self:
            if production.product_id.product_tmpl_id.ff_under_processing:
                production._ff_get_wip_location_or_raise()

    def _ff_sync_pending_finished_move_destination(self):
        """Re-check the company setting before posting stock.

        A setting may be changed after an MO was confirmed. For a pending main
        finished move, keep the stored destination aligned with the current
        valid company WIP location. By-products are deliberately untouched.
        """
        for production in self:
            if not production.product_id.product_tmpl_id.ff_under_processing:
                continue
            location = production._ff_get_wip_location_or_raise()
            if production.location_dest_id != location:
                production.location_dest_id = location
            main_moves = production.move_finished_ids.filtered(
                lambda move: move.product_id == production.product_id
                and not move.byproduct_id
                and move.state not in ('done', 'cancel')
            )
            if main_moves:
                main_moves.write({
                    'location_dest_id': location.id,
                    'warehouse_id': location.warehouse_id.id,
                })
            byproduct_moves = production.move_finished_ids.filtered(
                lambda move: move.byproduct_id
                and move.state not in ('done', 'cancel')
            )
            standard_destination = production._ff_get_standard_finished_destination()
            if byproduct_moves and standard_destination:
                byproduct_moves.write({
                    'location_dest_id': standard_destination.id,
                    'warehouse_id': standard_destination.warehouse_id.id,
                })

    def _get_move_finished_values(
        self, product_id, product_uom_qty, product_uom, operation_id=False,
        byproduct_id=False, cost_share=0,
    ):
        values = super()._get_move_finished_values(
            product_id,
            product_uom_qty,
            product_uom,
            operation_id=operation_id,
            byproduct_id=byproduct_id,
            cost_share=cost_share,
        )
        if byproduct_id and self.product_id.product_tmpl_id.ff_under_processing:
            destination = self._ff_get_standard_finished_destination()
            values.update({
                'location_dest_id': destination.id,
                'warehouse_id': destination.warehouse_id.id,
            })
        return values

    def action_confirm(self):
        self._ff_validate_wip_configuration()
        result = super().action_confirm()
        self._ff_sync_pending_finished_move_destination()
        return result

    def button_mark_done(self):
        self._ff_sync_pending_finished_move_destination()
        return super().button_mark_done()
