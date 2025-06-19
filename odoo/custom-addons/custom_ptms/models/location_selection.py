# -*- coding: utf-8 - *-

from odoo import models, fields, api

class PtLocationSelection(models.Model):
    _name = 'pt.location.selection'

    
    name = fields.Char(string='PT Location',compute='_compute_name')
    company_id = fields.Many2one('res.company', 'School',
                                 default=lambda self: self._get_company())
    user_id = fields.Many2one(
        'res.users', string="User", required=True, default=lambda self: self.env.user.id)
    student_id = fields.Many2one('student.student', string="Student", default=lambda self: self._get_student())
    department_id = fields.Many2one('hr.department', 'Department',related='student_id.department_id', store=True)
    academic_year_id = fields.Many2one('academic.year', string='Academic Year', domain="[('current','=',True)]" ,
            default=lambda self: self.env['academic.year'].search([('current','=',True)]),required=True)
    standard_id = fields.Many2one('school.standard', string='Year of Study',related='student_id.standard_id',store=True)
    division_id = fields.Many2one('standard.division', string='Course',related='student_id.standard_id.division_id',store=True)
    region_id = fields.Many2one('res.country.state', string='Region', required=True)
    district_id = fields.Many2one('res.country.district', string='District',domain="[('state_id', '=?', region_id)]")
    ward_id = fields.Many2one('res.country.ward', string='Ward',domain="[('district_id', '=?', district_id)]")
    is_editable = fields.Boolean(string='Location Editable', compute='_compute_active_academic_yr')


    @api.model
    def _get_company(self):
        return self._context.get('company_id', self.env.user.company_id.id)

    @api.model
    def _get_student(self):
        student = self.env['student.student'].sudo().search([('user_id','=',self.env.user.id)], limit=1)
        if student:
            return student.id
        return False

    @api.depends('academic_year_id')
    def _compute_active_academic_yr(self):
        for record in self:
            record.is_editable = False
            if not record.academic_year_id:
                record.is_editable = True
            if record.academic_year_id.current:
                record.is_editable = True

    @api.depends('academic_year_id','region_id')
    def _compute_name(self):
        for record in self:
            record.name = ''
            if record.academic_year_id:
                record.name += record.academic_year_id.name
            if record.region_id:
                record.name += '-' + record.region_id.name

    def check_location_status(self):
        current_academic_year = self.env['academic.year'].search([('current','=',True)], limit=1)
        preference = self.search([('user_id','=',self.env.user.id),('academic_year_id','=',current_academic_year.id)])
        form_view_id = self.env.ref('custom_ptms.location_selection_form').id
        if preference:
            tree_view_id = self.env.ref('custom_ptms.location_selection_tree_active').id
        else:
            tree_view_id = self.env.ref('custom_ptms.location_selection_tree').id

        return {
            'name':'PT Location Preference',
            'view_mode':'tree,form',
            'views' : [(tree_view_id,'tree'),(form_view_id,'form')],
            'res_model':'pt.location.selection',
            'view_id':tree_view_id,
            'type':'ir.actions.act_window',
            'context':self.env.context,
            'target':'main',
        }
