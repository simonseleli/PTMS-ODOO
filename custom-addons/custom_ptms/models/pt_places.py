from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PTPlace(models.Model):
    _name = 'pt.place'
    _description = 'Practical Training Place'
    _order = 'name'

    name = fields.Char(string="Company Name", required=True)
    region = fields.Char(string="Region", required=True)
    district = fields.Char(string="District", required=True)
    total_chances = fields.Integer(string="Total Chances", default=1, required=True)

    application_ids = fields.One2many('pt.place.application', 'place_id', string="Applications")

    available_chances = fields.Integer(
        string="Available Chances",
        compute='_compute_available_chances',
        store=True
    )
    active_applications = fields.Integer(
        compute='_compute_active_applications',
        string="Active Applications"
    )

    def action_apply_pt_place(self):
        self.ensure_one()
        student = self.env['student.student'].search([('user_id', '=', self.env.uid)], limit=1)

        # Check if student has any active application (anywhere)
        existing = self.env['pt.place.application'].search_count([
            ('student_id', '=', student.id),
            ('state', 'in', ['submitted', 'approved'])
        ])

        if existing > 0:
            raise ValidationError(
                "You already have an active PT application. "
                "You can only apply to one place at a time."
            )

        if not student:
            raise ValidationError("Student record not found!")

        return {
            'name': 'Apply for PT Place',
            'type': 'ir.actions.act_window',
            'res_model': 'pt.place.application',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_student_id': student.id,
                'default_place_id': self.id,
            }
        }

    @api.depends('application_ids.state')
    def _compute_active_applications(self):
        for place in self:
            place.active_applications = len(place.application_ids.filtered(
                lambda a: a.state in ['submitted', 'approved']
            ))

    @api.depends('total_chances', 'active_applications')
    def _compute_available_chances(self):
        for place in self:
            place.available_chances = place.total_chances - place.active_applications

    @api.constrains('total_chances')
    def _check_total_chances(self):
        for record in self:
            if record.total_chances < 1:
                raise ValidationError("Total chances must be at least 1.")
            if record.available_chances < 0:
                raise ValidationError("Cannot reduce total chances below current active applications.")

    @api.onchange('total_chances')
    def _onchange_total_chances(self):
        if self.available_chances < 0:
            return {
                'warning': {
                    'title': "Chance Reduction Warning",
                    'message': f"Current active applications: {self.active_applications}. Reducing chances below this will reject pending applications."
                }
            }