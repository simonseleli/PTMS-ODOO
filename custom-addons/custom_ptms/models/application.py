# -*- coding: utf-8 - *-
from __future__ import division
from odoo import models, fields, api


class PtApplication(models.Model):
    _name = 'pt.application'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "PT Allocation"

    name = fields.Char('PT Allocation', compute='_compute_name')
    user_id = fields.Many2one(
        'res.users', string="User", required=True, default=lambda self: self.env.user.id)
    student_id = fields.Many2one(
        'student.student', string="Student", default=lambda self: self._get_student())
    student_name = fields.Char(related="student_id.name")
    student_gender = fields.Selection(related="student_id.gender")
    registration_no = fields.Char(related="student_id.registration_no")
    department_id = fields.Many2one('hr.department', 'Department',related='student_id.department_id', store=True)
    state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'),
                             ('accepted', 'Accepted'), ('rejected', 'Rejected')], string="Status", readonly=True, default='draft', track_visibility='onchange', tracking=True)
    vacancy_id = fields.Many2one(
        'pt.company.vacancy', string="Company", domain="[('remaining_chances','>',0)]", readonly=True, states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', string="Company", related='vacancy_id.partner_id',
                                 readonly=True, states={'draft': [('readonly', False)]}, store=True)
    region_id = fields.Many2one('res.country.state', 'Region',related='partner_id.state_id', store=True)
    partner_id_self = fields.Many2one('res.partner', string="Company", domain="[('is_company','=',True)]", readonly=True, states={
                                      'draft': [('readonly', False)],'submitted': [('readonly', False)],'accepted': [('readonly', False)]})
    company_id = fields.Many2one(
        'res.company', 'School', default=lambda self: self._get_company())
    academic_year = fields.Many2one(
        'academic.year', string="Academic Year", domain="[('current','=',True)]", default=lambda self: self.env['academic.year'].search([('current', '=', True)]))
    date = fields.Date(string="Application Date",
                       default=lambda self: fields.datetime.today())
    is_self = fields.Boolean(string="Submitted By Student", default=False)
    is_published = fields.Boolean(string="Results Published", default=False)
    confirmation_letter = fields.Binary(
        string="Confirmation Letter", readonly=True, states={'draft': [('readonly', False)],'submitted': [('readonly', False)]},attachment=True)
    division_id = fields.Many2one('standard.division', string="Course", related='student_id.standard_id.division_id', store=True)
    pt_type = fields.Many2one('standard.standard', string="PT Type", related='student_id.standard_id.standard_id', store=True)
    arrival_note = fields.Binary(string='Arrival Note', states={
                                 'accepted': [('readonly', False)]},attachment=True)
    current_year = fields.Boolean(string='Current Academic Year', default=True)

    ########################Supervisor Assignment####################
    is_assigned = fields.Boolean(string="Assigned", default=False)
    assignment_id = fields.Many2one('pt.supervisor.assignment', string="Assignment")
    assignment_user_id = fields.Many2one('res.users', related='assignment_id.teacher_id.employee_id.user_id', store=True, string="Supervisor")

    ########################Vitisting Information####################
    date_visit = fields.Date(string="Visiting Date")
    comments = fields.Text("Workplace Comments")
    remarks = fields.Text("Remarks on Student")
    report_title = fields.Char("Final Report Title")

    ########################Grading Information######################
    officer_marks = fields.Float("Officer Marks")
    logbook_marks = fields.Float("Log Book Marks")
    supervisor_marks = fields.Float("Supervisor Marks")
    report_marks = fields.Float("Final Report Marks")
    total_marks = fields.Float("Total Marks", compute='_compute_total_marks')

    officer_marks_label = fields.Float("Officer Marks",related='student_id.standard_id.officer_marks')
    logbook_marks_label = fields.Float("Log Book Marks",related='student_id.standard_id.logbook_marks')
    supervisor_marks_label = fields.Float("Supervisor Marks",related='student_id.standard_id.supervisor_marks')
    report_marks_label = fields.Float("Final Report Marks",related='student_id.standard_id.report_marks')

    ##########################Final Report############################
    final_report = fields.Binary(string='Final Report', states={
                                 'accepted': [('readonly', False)]},attachment=True)

    @api.model
    def _get_company(self):
        return self._context.get('company_id', self.env.user.company_id.id)

    @api.model
    def _get_current_year(self):
        current_active_year = self.env['academic.year'].search(
            [('current', '=', True)])
        if current_active_year:
            return current_active_year
        return
    
    def _mark_pt_status(self):
        applications = self.search([('current_year','=',True)])
        current_active_year = self.env['academic.year'].search([('current', '=', True)])
        for application in applications:
            if application.academic_year.id != current_active_year.id:
                application.current_year = False

    @api.model
    def _get_student(self):
        student = self.env['student.student'].sudo().search(
            [('user_id', '=', self.env.user.id)], limit=1)
        if student:
            return student.id
        return False

    @api.model
    def _get_active_student(self):
        student = self.env['student.student'].sudo().search(
            [('user_id', '=', self.env.user.id)], limit=1)
        if student:
            return student
        return False

    @api.depends('student_name', 'partner_id')
    def _compute_name(self):
        for record in self:
            record.name = ''
            if record.student_name:
                record.name += record.student_name
            if record.partner_id:
                record.name += '(' + record.partner_id.name + ')'

    @api.depends('officer_marks', 'logbook_marks', 'supervisor_marks', 'report_marks')
    def _compute_total_marks(self):
        for record in self:
            record.total_marks = 0.0
            if record.officer_marks:
                record.total_marks += record.officer_marks
            if record.logbook_marks:
                record.total_marks += record.logbook_marks
            if record.supervisor_marks:
                record.total_marks += record.supervisor_marks
            if record.report_marks:
                record.total_marks += record.report_marks

    def button_submit(self):
        for rec in self:
            rec.state = 'submitted'

    def button_accept(self):
        for rec in self:
            if rec.is_self:
                vacancancies = self.env['pt.company.vacancy'].search([('partner_id', '=', rec.partner_id_self.id),
                                                                 ('academic_year_id', '=', rec.academic_year.id), (
                                                                  'standard_id', '=', rec.student_id.standard_id.id),
                                                                 ('division_id', '=', rec.student_id.standard_id.division_id.id)])
                vacancy = vacancancies
                if len(vacancancies) > 1:
                    vacancy = vacancancies[0]
                if vacancy:
                    vacancy.given_chances += 1
                    vacancy.assigned_chances += 1
                    rec.vacancy_id = vacancy.id
                else:
                    vacancy = self.env['pt.company.vacancy'].sudo().create({'partner_id': rec.partner_id_self.id,
                                                                            'academic_year_id': rec.academic_year.id, 'standard_id': rec.student_id.standard_id.id,
                                                                            'division_id': rec.student_id.standard_id.division_id.id, 'given_chances': 1, 'assigned_chances': 1})
                    rec.vacancy_id = vacancy.id
            rec.state = 'accepted'

    def button_reject(self):
        for rec in self:
            if rec.vacancy_id:
                rec.vacancy_id.assigned_chances -= 1
            rec.state = 'rejected'

    def check_pt_status_system(self):
        current_academic_year = self.env['academic.year'].search(
            [('current', '=', True)], limit=1)
        application = self.search([('user_id', '=', self.env.user.id), ('academic_year', '=',
                                  current_academic_year.id), ('state', 'in', ['draft', 'submitted', 'accepted'])])
        student_id = self._get_student()
        domain = [('remaining_chances', '>', 0)]
        if student_id:
            student = self.env['student.student'].sudo().browse(student_id)
            domain = [('remaining_chances', '>', 0), ('standard_id', '=', student.standard_id.id),
                      ('division_id', '=', student.standard_id.division_id.id),('academic_year_id','=',current_academic_year.id)]
        if application:
            tree_view_id = self.env.ref('custom_ptms.application_student_tree').id
            form_view_id = self.env.ref('custom_ptms.submit_to_confirm_form').id
            return {
                'name': 'Application',
                'view_mode': 'tree,form',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'res_model': 'pt.application',
                'view_id': tree_view_id,
                'type': 'ir.actions.act_window',
                'target': 'main',
            }
        else:
            tree_view_id = self.env.ref(
                'custom_ptms.company_vacancy_application_tree').id
            return {
                'name': 'Company Vacancies',
                'view_mode': 'tree,form',
                'views': [(tree_view_id, 'tree')],
                'res_model': 'pt.company.vacancy',
                'view_id': tree_view_id,
                'type': 'ir.actions.act_window',
                'domain': domain,
                'context': self.env.context,
                'target': 'main',
            }

    def check_pt_status_self(self):
        current_academic_year = self.env['academic.year'].search(
            [('current', '=', True)], limit=1)
        application = self.search([('user_id', '=', self.env.user.id), ('academic_year', '=',
                                  current_academic_year.id), ('state', 'in', ['draft', 'submitted', 'accepted'])])
        if application:
            tree_view_id = self.env.ref(
                'custom_ptms.application_student_tree').id
            form_view_id = self.env.ref(
                'custom_ptms.submit_to_confirm_form').id
            return {
                'name': 'Application',
                'view_mode': 'tree,form',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'res_model': 'pt.application',
                'view_id': tree_view_id,
                'type': 'ir.actions.act_window',
                'target': 'main',
            }
        else:
            form_view_id = self.env.ref(
                'custom_ptms.submit_to_confirm_form').id
            return {
                'name': 'Application',
                'view_mode': 'form',
                'views': [(form_view_id, 'form')],
                'res_model': 'pt.application',
                'view_id': form_view_id,
                'type': 'ir.actions.act_window',
                'context': {'default_is_self': True},
                'target': 'main',
            }
