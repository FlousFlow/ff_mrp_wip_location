from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestMrpWipLocation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.picking_type = cls.warehouse.manu_type_id
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.wip_location = cls.env['stock.location'].create({
            'name': 'WIP Test',
            'usage': 'internal',
            'location_id': cls.warehouse.view_location_id.id,
            'company_id': cls.company.id,
        })
        cls.product, cls.component = cls.env['product.product'].create([
            {'name': 'WIP Finished', 'type': 'consu', 'is_storable': True},
            {'name': 'WIP Component', 'type': 'consu', 'is_storable': True},
        ])
        cls.bom = cls.env['mrp.bom'].create({
            'product_id': cls.product.id,
            'product_tmpl_id': cls.product.product_tmpl_id.id,
            'product_qty': 1.0,
            'uom_id': cls.product.uom_id.id,
            'bom_line_ids': [Command.create({
                'product_id': cls.component.id,
                'product_qty': 1.0,
            })],
        })

    def _new_mo(self):
        form = Form(self.env['mrp.production'])
        form.product_id = self.product
        form.bom_id = self.bom
        form.product_qty = 1.0
        return form.save()

    def test_standard_destination_when_disabled(self):
        self.company.ff_wip_location_id = self.wip_location
        self.product.product_tmpl_id.ff_under_processing = False
        mo = self._new_mo()
        self.assertEqual(mo.location_dest_id, self.picking_type.default_location_dest_id)

    def test_wip_destination_and_missing_configuration(self):
        self.product.product_tmpl_id.ff_under_processing = True
        self.company.ff_wip_location_id = False
        mo = self._new_mo()
        with self.assertRaises(UserError):
            mo.action_confirm()

        self.company.ff_wip_location_id = self.wip_location
        mo = self._new_mo()
        self.assertEqual(mo.location_dest_id, self.wip_location)
        mo.action_confirm()
        self.assertEqual(mo.move_finished_ids.filtered(
            lambda move: move.product_id == self.product and not move.byproduct_id
        ).location_dest_id, self.wip_location)
        self.company.ff_wip_location_id = False
        with self.assertRaises(UserError):
            mo.button_mark_done()

    def test_archived_location_is_rejected(self):
        self.product.product_tmpl_id.ff_under_processing = True
        self.company.ff_wip_location_id = self.wip_location
        self.wip_location.active = False
        mo = self._new_mo()
        with self.assertRaises(UserError):
            mo.action_confirm()

    def test_draft_product_change_recomputes_destination(self):
        self.company.ff_wip_location_id = self.wip_location
        self.product.product_tmpl_id.ff_under_processing = False
        mo = self._new_mo()
        self.assertNotEqual(mo.location_dest_id, self.wip_location)
        self.product.product_tmpl_id.ff_under_processing = True
        mo.invalidate_recordset()
        self.assertEqual(mo.location_dest_id, self.wip_location)

    def test_completed_finished_move_uses_wip_location(self):
        self.company.ff_wip_location_id = self.wip_location
        self.product.product_tmpl_id.ff_under_processing = True
        self.env['stock.quant']._update_available_quantity(
            self.component, self.stock_location, 1.0)
        mo = self._new_mo()
        mo.action_confirm()
        mo.action_assign()
        mo.button_mark_done()
        main_move = mo.move_finished_ids.filtered(
            lambda move: move.product_id == self.product and not move.byproduct_id)
        self.assertEqual(mo.state, 'done')
        self.assertEqual(main_move.state, 'done')
        self.assertEqual(main_move.move_line_ids.location_dest_id, self.wip_location)

    def test_byproduct_keeps_standard_destination(self):
        byproduct = self.env['product.product'].create({
            'name': 'WIP Byproduct',
            'type': 'consu',
            'is_storable': True,
        })
        self.bom.write({
            'byproduct_ids': [Command.create({
                'product_id': byproduct.id,
                'product_qty': 1.0,
                'uom_id': byproduct.uom_id.id,
            })],
        })
        self.company.ff_wip_location_id = self.wip_location
        self.product.product_tmpl_id.ff_under_processing = True
        self.env['stock.quant']._update_available_quantity(
            self.component, self.stock_location, 1.0)
        mo = self._new_mo()
        mo.action_confirm()
        mo.action_assign()
        mo.button_mark_done()
        main_move = mo.move_finished_ids.filtered(
            lambda move: move.product_id == self.product and not move.byproduct_id)
        byproduct_move = mo.move_finished_ids.filtered(
            lambda move: move.product_id == byproduct and move.byproduct_id)
        self.assertEqual(main_move.move_line_ids.location_dest_id, self.wip_location)
        self.assertEqual(
            byproduct_move.move_line_ids.location_dest_id,
            self.picking_type.default_location_dest_id,
        )

    def test_shared_location_is_accepted(self):
        shared_parent = self.env['stock.location'].search([
            ('usage', '=', 'view'),
            ('company_id', '=', False),
        ], limit=1)
        shared_location = self.env['stock.location'].create({
            'name': 'Shared WIP Test',
            'usage': 'internal',
            'location_id': shared_parent.id,
            'company_id': False,
        })
        self.company.ff_wip_location_id = shared_location
        self.product.product_tmpl_id.ff_under_processing = True
        mo = self._new_mo()
        self.assertEqual(mo.location_dest_id, shared_location)

    def test_wrong_company_location_is_rejected(self):
        other_company = self.env['res.company'].create({'name': 'Other WIP Company'})
        shared_parent = self.env['stock.location'].search([
            ('usage', '=', 'view'),
            ('company_id', '=', False),
        ], limit=1)
        foreign_location = self.env['stock.location'].create({
            'name': 'Foreign WIP Test',
            'usage': 'internal',
            'location_id': shared_parent.id,
            'company_id': other_company.id,
        })
        with self.assertRaises(UserError):
            self.company.ff_wip_location_id = foreign_location

    def test_partial_production_preserves_wip_destination(self):
        self.company.ff_wip_location_id = self.wip_location
        self.product.product_tmpl_id.ff_under_processing = True
        self.env['stock.quant']._update_available_quantity(
            self.component, self.stock_location, 2.0)
        mo_form = Form(self.env['mrp.production'])
        mo_form.product_id = self.product
        mo_form.bom_id = self.bom
        mo_form.product_qty = 2.0
        mo = mo_form.save()
        mo.action_confirm()
        mo.action_assign()
        mo_form = Form(mo)
        mo_form.qty_producing = 1.0
        mo = mo_form.save()
        action = mo.button_mark_done()
        self.assertIsInstance(action, dict)
        backorder = self.env[action['res_model']].with_context(action['context']).create({})
        backorder.action_backorder()
        self.assertEqual(mo.state, 'done')
        self.assertEqual(mo.move_finished_ids.location_dest_id, self.wip_location)
        backorder_mo = mo.production_group_id.production_ids - mo
        self.assertTrue(backorder_mo)
        self.assertEqual(backorder_mo.location_dest_id, self.wip_location)
