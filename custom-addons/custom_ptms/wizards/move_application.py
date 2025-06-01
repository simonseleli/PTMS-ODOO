# See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class MoveApplications(models.TransientModel):
    """Defining TransientModel to move applications."""

    _name = 'move.applications'
    _description = "Move Applications"

    academic_year_id = fields.Many2one('academic.year', 'Academic Year',
                                       required=True)

    def move_start(self):
        application_obj = self.env['pt.place.application']
        for app in application_obj.search([('current_year', '=', True)]):
            app.current_year =  False   
        return True
