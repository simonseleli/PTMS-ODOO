# -*- coding: utf-8 - *-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class PtCompanyVacancy(models.Model):
    _name = 'pt.company.vacancy'

    name = fields.Char('PT Allocation', compute='_compute_name')
    company_id = fields.Many2one('res.company', 'School',
                                 default=lambda self: self._get_company())
    partner_id = fields.Many2one('res.partner', string='Company')
    state_id = fields.Many2one('res.country.state',string='Region',related='partner_id.state_id')
    academic_year_id = fields.Many2one('academic.year', string='Academic Year')
    standard_id = fields.Many2one('school.standard', string='Year of Study & Course')
    department_id = fields.Many2one('hr.department', 'Department',related='standard_id.department_id', store=True)
    standard_standard_id = fields.Many2one('standard.standard', string='Year of Study & Course',related='standard_id.standard_id',store=True)
    division_id = fields.Many2one('standard.division', string='Course',related='standard_id.division_id',store=True)
    given_chances = fields.Integer(string='Given Chances', required=True)
    assigned_chances = fields.Integer(string='Assigned Chances')
    remaining_chances = fields.Integer(string='Remaining Chances', compute='_compute_remaining_chances', store=True)
    is_editable = fields.Boolean(string='Line Editable', compute='_compute_active_academic_yr')
    current_year = fields.Boolean(string='Current Academic Year', default=True)

    @api.model
    def _get_company(self):
        return self._context.get('company_id', self.env.user.company_id.id)
    
    def _mark_vacancy_status(self):
        vacancies = self.search([('current_year','=',True)])
        current_active_year = self.env['academic.year'].search([('current', '=', True)])
        for vacancy in vacancies:
            if vacancy.academic_year_id.id != current_active_year.id:
                vacancy.current_year = False

    @api.depends('standard_id', 'partner_id', 'division_id')
    def _compute_name(self):
        for record in self:
            record.name = ''
            if record.partner_id:
                record.name += record.partner_id.name
            if record.standard_id or record.division_id:
                record.name += '(' + record.standard_id.name + ')'

    @api.depends('given_chances', 'assigned_chances')
    def _compute_remaining_chances(self):
        for record in self:
            record.remaining_chances = 0
            if record.given_chances:
                record.remaining_chances = record.given_chances - record.assigned_chances

    @api.depends('academic_year_id')
    def _compute_active_academic_yr(self):
        for record in self:
            record.is_editable = False
            if not record.academic_year_id:
                record.is_editable = True
            if record.academic_year_id.current:
                record.is_editable = True

    def button_confirm(self):
        view_id = self.env.ref('custom_ptms.confirm_wizard_form').id
        return {
            'name': 'Confirmation Dialog',
                    'view_mode': 'form',
                    'views': [(view_id, 'form')],
                    'res_model': 'pt.confirmation.wizard',
                    'view_id': view_id,
                    'type': 'ir.actions.act_window',
                    'context': {'default_vacancy_id': self.id},
                    'target': 'new',
        }

    def button_reserve(self, vacancy_id):
        if vacancy_id:
            vacancy = self.env['pt.company.vacancy'].browse(vacancy_id)
            if vacancy.remaining_chances > 0:
                vacancy.sudo().assigned_chances += 1
                values = {
                    'user_id': self.env.user.id,
                    'partner_id': vacancy.partner_id.id,
                    'academic_year': vacancy.academic_year_id.id,
                    'state': 'submitted',
                    'pt_type': vacancy.standard_standard_id.id
                }
                self.env['pt.application'].sudo().create(values)
                view_id = self.env.ref('custom_ptms.application_student_tree').id
                return {
                    'name': 'Application',
                    'view_mode': 'tree,form',
                    'views': [(view_id, 'tree')],
                    'res_model': 'pt.application',
                    'view_id': view_id,
                    'type': 'ir.actions.act_window',
                    'target': 'main',
                }
            else:
                raise ValidationError(_('Chances for %s are full'
                                        ) % vacancy.partner_id.name)

