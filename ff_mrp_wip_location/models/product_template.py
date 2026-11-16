from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    ff_under_processing = fields.Boolean(
        string='Under Processing',
        default=False,
        help='When enabled, the main finished product of a manufacturing order '
             'is stored in the company Work in Progress location.',
    )
