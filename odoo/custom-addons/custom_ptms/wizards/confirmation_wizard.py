from odoo import models, fields, api

class ConfirmationWizard(models.TransientModel):
    _name = 'pt.confirmation.wizard'

    yes_no = fields.Char(default='Do you wish to proceed?')
    vacancy_id = fields.Many2one('pt.company.vacancy', string='Vacancy')

    def yes(self):
        if self.vacancy_id:
            return self.env['pt.company.vacancy'].button_reserve(self.vacancy_id.id)