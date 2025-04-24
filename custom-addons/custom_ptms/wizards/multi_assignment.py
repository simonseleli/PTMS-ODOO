from odoo import models, fields, api

class ConfirmationWizard(models.TransientModel):
    _name = 'pt.multiassignment.wizard'

    vacancy_id = fields.Many2one(
        'pt.company.vacancy', string="Company", domain="[('remaining_chances','>',0)]",requied=True)
    company_id = fields.Many2one('res.company', 'School',
                                 default=lambda self: self._get_company())
    academic_year = fields.Many2one(
        'academic.year', string="Academic Year", domain="[('current','=',True)]" ,default=lambda self: self.env['academic.year'].search([('current','=',True)]))
    student_ids = fields.Many2many(
        'student.student', string="Students", requied=True)
    date = fields.Datetime(string="Application Date", default=lambda self: fields.datetime.now())

    @api.model
    def _get_company(self):
        return self._context.get('company_id', self.env.user.company_id.id)

    def save_assignment(self):
        if self.student_ids and self.vacancy_id:
            for student in self.student_ids:
                application = self.env['pt.application'].search([('user_id','=',student.user_id.id),('academic_year','=',self.academic_year.id),('state','in',['draft','submitted','accepted'])])
                if not application:
                    values = {
                        'vacancy_id': self.vacancy_id.id,
                        'company_id': self.company_id.id,
                        'student_id': student.id,
                        'user_id': student.user_id.id,
                        'date': self.date,
                        'academic_year': self.academic_year.id,
                        'state': 'accepted',
                    }
                    self.vacancy_id.assigned_chances += 1
                    res = self.env['pt.application'].sudo().create(values)
            return