from odoo import models, fields, api


class Logbook(models.Model):
    _name = 'pt.application.logbook'
    _description = 'Weekly Logbook Entry'

    name = fields.Char(string='Week Number', required=True)
    # date_from = fields.Date(string='From', required=True)
    # date_to = fields.Date(string='To', required=True)
    date_from = fields.Date(string='From', required=True, default=lambda self: fields.Date.today())
    date_to = fields.Date(string='To', required=True, default=lambda self: fields.Date.add(fields.Date.today(), days=6))

    # Daily activities
    monday_activity = fields.Text(string='Monday Activity')
    tuesday_activity = fields.Text(string='Tuesday Activity')
    wednesday_activity = fields.Text(string='Wednesday Activity')
    thursday_activity = fields.Text(string='Thursday Activity')
    friday_activity = fields.Text(string='Friday Activity')

    main_job_details = fields.Text(string='Details of the Main Job of the Week')

    # Computed field for display purposes
    display_name = fields.Char(string='Display Name', compute='_compute_display_name')

    @api.depends('name', 'date_from', 'date_to')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.name} ({record.date_from} to {record.date_to})"



