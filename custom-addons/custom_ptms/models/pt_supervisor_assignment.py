# -*- coding: utf-8 - *-
from odoo import models, fields, api


class PtSupervisorAssignment(models.Model):
    _name = 'pt.supervisor.assignment'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "Supervisor Assignment"

    name = fields.Char('Supervisor', compute='_compute_name')
    company_id = fields.Many2one('res.company', 'School',default=lambda self: self._get_company())
    date = fields.Datetime(string="Date Visited", default=lambda self: fields.datetime.now())
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done'),
                             ], string="Status", readonly=True, default='draft',track_visibility='onchange',tracking=True)
    academic_year_id = fields.Many2one(
        'academic.year', string="Academic Year", domain="[('current','=',True)]" ,default=lambda self: self.env['academic.year'].search([('current','=',True)]))
    application_ids = fields.One2many('pt.application', 'assignment_id', string='Student Application', required=True)
    teacher_id = fields.Many2one('school.teacher', string='Supervisor',required=True)
    teacher_user_id = fields.Many2one('res.users', related='teacher_id.employee_id.user_id')
    current_year = fields.Boolean(string='Current Academic Year', default=True)


    def write(self,vals):
        app_ids =  self.application_ids
        for ap_id in app_ids:
            ap_id.is_assigned = False
        res = super(PtSupervisorAssignment, self).write(vals)
        if res:
            for new_id in self.application_ids:
                new_id.is_assigned = True
        return res
    
    def _mark_assignment_status(self):
        assignments = self.search([('current_year','=',True)], limit=100)
        current_active_year = self.env['academic.year'].search([('current', '=', True)])
        for assignment in assignments:
            if assignment.academic_year_id.id != current_active_year.id:
                assignment.current_year = False

    @api.model
    def _get_company(self):
        return self._context.get('company_id', self.env.user.company_id.id)

    @api.depends('teacher_id')
    def _compute_name(self):
        for record in self:
            record.name = ''
            if record.teacher_id:
                record.name += record.teacher_id.name

    def button_done(self):
        for rec in self:
            if rec.application_ids:
                for application in rec.application_ids:
                    application.is_assigned = True
            rec.state = 'done'

    def rectify_assignment(self):
        assignments = self.search([('state','=','done')])
        for assignment in assignments:
            if assignment.application_ids:
                for application in assignment.application_ids:
                    application.is_assigned =  True

class PtSummary(models.Model):
    _name = 'pt.summary'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "Summary"

    name = fields.Char('Supervisor', compute='_compute_name')
    company_id = fields.Many2one('res.company', 'School',default=lambda self: self._get_company())
    date = fields.Datetime(string="Date Visited", default=lambda self: fields.datetime.now())
    academic_year_id = fields.Many2one('academic.year', string="Academic Year", domain="[('current','=',True)]" ,default=lambda self: self.env['academic.year'].search([('current','=',True)]))
    application_ids = fields.Many2many('pt.application', 'assignment_id', string='Student Application', required=True)
    teacher_ids = fields.Many2many('school.teacher', string='Supervisor',required=True)
