from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SchoolClass(models.Model):
    _inherit = 'school.standard'

    department_id = fields.Many2one('hr.department', 'Department',required=True)
    officer_marks = fields.Float("Officer Marks", default='10.0')
    logbook_marks = fields.Float("Log Book Marks",default='20.0')
    supervisor_marks = fields.Float("Supervisor Marks",default='10.0')
    report_marks = fields.Float("Final Report Marks",default='60.0')