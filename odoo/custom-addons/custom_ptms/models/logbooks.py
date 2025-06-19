from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class Logbook(models.Model):
    _name = 'pt.application.logbook'
    _description = 'Weekly Logbook Entry'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Week Number', required=True)
    date_from = fields.Date(string='From', required=True)
    date_to = fields.Date(string='To', required=True)
    application_id = fields.Many2one('pt.place.application', string='Application', required=True, ondelete='cascade')
    student_id = fields.Many2one('student.student', string='Student', related='application_id.student_id', store=True)

    # Daily activities
    monday_activity = fields.Text(string='Monday Activity')
    tuesday_activity = fields.Text(string='Tuesday Activity')
    wednesday_activity = fields.Text(string='Wednesday Activity')
    thursday_activity = fields.Text(string='Thursday Activity')
    friday_activity = fields.Text(string='Friday Activity')

    main_job_details = fields.Text(string='Details of the Main Job of the Week')

    # Attachment fields
    attachment = fields.Binary(string='Attachment', attachment=True)
    attachment_filename = fields.Char(string='Attachment Filename')

    # Computed field for display purposes
    display_name = fields.Char(string='Display Name', compute='_compute_display_name')

    # Computed field for editability
    is_editable = fields.Boolean(
        string='Is Editable',
        compute='_compute_is_editable',
        store=False,
        help="Indicates if the logbook entry is editable based on the current date and user permissions."
    )

    @api.depends('date_from', 'date_to')
    def _compute_is_editable(self):
        today = fields.Date.context_today(self)
        for record in self:
            # Coordinators/admins can always edit
            if self.env.user.has_group('school.group_school_administration') or \
               self.env.user.has_group('custom_ptms.department_coordinator'):
                record.is_editable = True
            else:
                # Students can edit only if date_from <= today <= date_to
                record.is_editable = record.date_from and record.date_to and \
                                     record.date_from <= today <= record.date_to

    @api.depends('name', 'date_from', 'date_to')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.name} ({record.date_from} to {record.date_to})"

    @api.constrains('date_from', 'date_to')
    def _check_date_range(self):
        for record in self:
            if record.date_from and record.date_to:
                delta = (record.date_to - record.date_from).days
                if delta != 6:
                    raise ValidationError("The date range for a logbook entry must be exactly 7 days (from Monday to Sunday).")

    def write(self, vals):
        for record in self:
            # Skip deadline check for coordinators/admins
            if not (self.env.user.has_group('school.group_school_administration') or
                    self.env.user.has_group('custom_ptms.department_coordinator')):
                today = fields.Date.context_today(self)
                if record.date_to and record.date_to < today:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Editing Not Allowed',
                            'message': f"This logbook entry ('{record.display_name}') cannot be edited because the week ended on {record.date_to}.",
                            'type': 'warning',
                            'sticky': True,
                        }
                    }
                if record.date_from and record.date_from > today:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Editing Not Allowed',
                            'message': f"This logbook entry ('{record.display_name}') cannot be edited because the week has not yet started (starts on {record.date_from}).",
                            'type': 'warning',
                            'sticky': True,
                        }
                    }
        return super().write(vals)

    @api.model
    def create(self, vals):
        # Allow creation only by system (e.g., via pt.place.application) or coordinators/admins
        if not (self.env.user.has_group('school.group_school_administration') or
                self.env.user.has_group('custom_ptms.department_coordinator')):
            raise ValidationError("Students cannot manually create logbook entries.")
        return super().create(vals)