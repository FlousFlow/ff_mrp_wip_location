from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ff_wip_location_id = fields.Many2one(
        related='company_id.ff_wip_location_id',
        string='Work in Progress Location',
        readonly=False,
        domain="[('usage', '=', 'internal'), ('active', '=', True)]",
        check_company=True,
    )
