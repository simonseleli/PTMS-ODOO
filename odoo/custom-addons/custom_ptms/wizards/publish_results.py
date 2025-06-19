from odoo import models, fields, api

class PublishWizard(models.TransientModel):
    _name = 'pt.publish.wizard'

  
    company_id = fields.Many2one('res.company', 'School',
                                 default=lambda self: self._get_company())
    academic_year = fields.Many2one('academic.year', string="Academic Year" ,default=lambda self: self.env['academic.year'].search([('current','=',True)]),required=True)
    is_publish = fields.Selection([('pub', 'Publish'), ('unp', 'Unpublish')], string="Publish/Unpublish",required=True)

    @api.model
    def _get_company(self):
        return self._context.get('company_id', self.env.user.company_id.id)

    def publish_unpublish(self):
        status = False
        if self.is_publish == 'pub':
            status = True
            applications = self.env['pt.place.application'].search([('academic_year','=',self.academic_year.id)])
            for application in applications:
                application.is_published = status
            return