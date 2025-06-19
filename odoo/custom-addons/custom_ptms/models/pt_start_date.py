from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime

class PTStartDate(models.Model):
    _name = 'pt.start.date'
    _description = 'PT Logbook Start Date'
    _inherit = ['mail.thread']

    logbook_start_date = fields.Date(
        string='Logbook Start Date',
        required=True,
        tracking=True,
        help="The start date for PT logbook entries (must be a Monday)."
    )

    @api.constrains('logbook_start_date')
    def _check_monday(self):
        for record in self:
            if record.logbook_start_date:
                if record.logbook_start_date.weekday() != 0:  # 0 = Monday
                    raise ValidationError("The logbook start date must be a Monday.")

    @api.model
    def create(self, vals):
        # Ensure only one record exists
        existing = self.search([])
        if existing:
            raise ValidationError("Only one PT start date record can exist. Please edit the existing record.")
        return super().create(vals)

    def write(self, vals):
        # Update existing logbook entries when start date changes
        res = super().write(vals)
        if 'logbook_start_date' in vals:
            self.env['pt.place.application'].update_logbook_dates()
        return res