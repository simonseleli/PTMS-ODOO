from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    district_id = fields.Many2one("res.country.district", string='District', ondelete='restrict',
                               domain="[('state_id', '=?', state_id)]")
    ward_id = fields.Many2one("res.country.ward", string='Ward', ondelete='restrict',
                               domain="[('district_id', '=?',district_id)]")
    vacancy_lines = fields.One2many('pt.company.vacancy', 'partner_id', string='Vacancy',ondelete='restrict')

    company_id = fields.Many2one('res.company', 'School/College', index=True,default=lambda self: self._get_company())


    @api.model
    def _get_company(self):
        return self._context.get('company_id', self.env.user.company_id.id)