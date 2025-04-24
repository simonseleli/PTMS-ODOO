from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SchooDivision(models.Model):
    _inherit = 'standard.division'

    company_id = fields.Many2one(
        'res.company', 'School/College', default=lambda self: self._get_company(),required=True)
    

    @api.model
    def _get_company(self):
        return self._context.get('company_id', self.env.user.company_id.id)