from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.school.models import school


class StudentStudent(models.Model):
    _inherit = 'student.student'

    company_id = fields.Many2one('res.company', 'Company', related='school_id.company_id')
    stu_name = fields.Char('Student Name', readonly=True,compute='_compute_student_name')
    display_name = fields.Char('Student Name', compute='_compute_student_name')
    middle = fields.Char('Middle Name', states={'done': [('readonly', True)]})
    registration_no = fields.Char('Registration No', states={'done': [('readonly', True)]})
    department_id = fields.Many2one('hr.department', 'Department',related='standard_id.department_id', store=True)

    @api.model
    def _get_company(self):
        return self._context.get('company_id', self.env.user.company_id.id)

    def admission_done(self):
        res = super(StudentStudent, self).admission_done()
        if res:
            for rec in self:
                rec.user_id.write(
                    {'login': rec.registration_no, 'password': rec.registration_no})
        return True

    @api.depends('name', 'middle', 'last')
    def _compute_student_name(self):
        for record in self:
            record.display_name = ''
            if record.name:
                record.display_name += record.name
            if record.middle:
                record.display_name += ' ' + record.middle + ' '
            if record.last:
                record.display_name += ' ' + record.last + ' '

    def _rectify_name(self):
        students = self.search([('state','=','done')])
        for student in students:
            firstname = student.user_id.name.split()[0]
            middlename = student.middle
            lastname =  student.last
            if firstname:
                student.user_id.name = firstname
            if middlename:
                student.user_id.name += ' ' + middlename
            if lastname:
                student.user_id.name += ' ' + lastname

    def _rectify_draft_name(self):
        students = self.search([('state','=','draft')])
        for student in students:
            firstname = student.user_id.name.split()[0]
            middlename = student.middle
            lastname =  student.last
            if firstname:
                student.user_id.name = firstname
            if middlename:
                student.user_id.name += ' ' + middlename
            if lastname:
                student.user_id.name += ' ' + lastname