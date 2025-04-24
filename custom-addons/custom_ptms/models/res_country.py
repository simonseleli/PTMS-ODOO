# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
import logging
from odoo import api, fields, models
from odoo.osv import expression
from psycopg2 import IntegrityError
from odoo.tools.translate import _
_logger = logging.getLogger(__name__)


class CountryDistrict(models.Model):
    _description = "District"
    _name = 'res.country.district'
    _order = 'name'

    state_id = fields.Many2one('res.country.state', string='Region', required=True)
    name = fields.Char(string='District Name', required=True,)
    code = fields.Char(string='District Code', required=True, unique=True)

class DistrictWard(models.Model):
    _description = "Ward"
    _name = 'res.country.ward'
    _order = 'name'

    district_id = fields.Many2one('res.country.district', string='District', required=True)
    name = fields.Char(string='Ward Name', required=True,)
    code = fields.Char(string='Ward Code', required=True, unique=True)