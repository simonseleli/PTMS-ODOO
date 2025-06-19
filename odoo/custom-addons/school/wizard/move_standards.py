# See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class MoveStandards(models.TransientModel):
    """Defining TransientModel to move standard."""

    _name = 'move.standards'
    _description = "Move Standards"

    academic_year_id = fields.Many2one('academic.year', 'Academic Year',
                                       required=True)
    standard_id = fields.Many2one('school.standard', 'Class',required=True)

    def move_start(self):
        '''Code for moving student to next standard'''
        school_stand_obj = self.env['school.standard']
        standard_obj = self.env["standard.standard"]
        student_obj = self.env['student.student']
        application_obj = self.env['student.student']
        standard_seq = self.standard_id.standard_id.sequence
        next_class_id = standard_obj.next_standard(standard_seq)

        if next_class_id:
            for stud in student_obj.search([('state', '=', 'done'),('standard_id', '=', self.standard_id.id)]):
                academic_year = self.academic_year_id
                division = (stud.standard_id.division_id.id or False)
                next_stand = school_stand_obj.\
                    search([('standard_id', '=', next_class_id),
                            ('division_id', '=', division),
                            ('school_id', '=', stud.school_id.id),
                            ('medium_id', '=', stud.medium_id.id)])
                if next_stand:
                    std_vals = {'year': academic_year.id,
                                'standard_id': next_stand.id}
                    # Move student to next standard
                    stud.write(std_vals)
                else:
                    stud.state = 'alumni'
                    stud.active = False 
        else:
            for stud in student_obj.search([('state', '=', 'done'),('standard_id', '=', self.standard_id.id)]):
                stud.state = 'alumni'
                stud.active = False
        return True
