from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    ff_wip_location_id = fields.Many2one(
        'stock.location',
        string='Work in Progress Location',
        domain="[('usage', '=', 'internal'), ('active', '=', True)]",
        check_company=True,
        help='Internal location used for the main finished product of products '
             'marked Under Processing. Leave empty to keep standard Odoo routing.',
    )

    @api.constrains('ff_wip_location_id')
    def _check_ff_wip_location(self):
        for company in self:
            location = company.ff_wip_location_id
            if not location:
                continue
            if location.usage != 'internal' or not location.active:
                raise ValidationError(_(
                    'The Work in Progress Location must be an active internal '
                    'location.'
                ))
            if location.company_id and location.company_id != company:
                raise ValidationError(_(
                    'The Work in Progress Location must belong to the current '
                    'company or be shared.'
                ))
