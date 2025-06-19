from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class PTSkill(models.Model):
    _name = 'pt.skill'
    _description = 'Practical Training Skill'

    name = fields.Char(string="Skill Name", required=True)
    description = fields.Text(string="Description")
    active = fields.Boolean(string="Active", default=True)

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'Skill name must be unique!')
    ]