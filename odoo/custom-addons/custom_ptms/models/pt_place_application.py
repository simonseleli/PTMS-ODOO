# from odoo import models, fields, api
# from odoo.exceptions import ValidationError
#
#
# class PTApplication(models.Model):
#     _name = 'pt.place.application'
#     _description = 'PT Application'
#     _order = 'create_date desc'
#
#     name = fields.Char(string="Application Reference", readonly=True, default=lambda self: self._default_reference())
#     student_id = fields.Many2one(
#         'student.student',
#         string="Student",
#     )
#
#     place_id = fields.Many2one('pt.place', string="PT Place", required=True)
#
#     application_date = fields.Datetime(default=fields.Datetime.now)
#     state = fields.Selection([
#         ('draft', 'Draft'),
#         ('submitted', 'Submitted'),
#         ('approved', 'Approved'),
#         ('rejected', 'Rejected'),
#     ], default='draft', string="Status")
#     rejection_reason = fields.Text(string="Rejection Reason")
#
#
#     @api.model
#     def _default_reference(self):
#         return self.env['ir.sequence'].next_by_code('pt.application') or 'New'
#
#     @api.model
#     def create(self, vals):
#         if vals.get('name', 'New') == 'New':
#             vals['name'] = self._default_reference()
#         return super().create(vals)
#
#     def action_submit(self):
#         for application in self:
#             if application.state != 'draft':
#                 raise ValidationError("Only draft applications can be submitted.")
#
#             if application.place_id.available_chances < 1:
#                 raise ValidationError(
#                     f"No available chances at {application.place_id.name}. Only {application.place_id.available_chances} chance(s) remaining."
#                 )
#
#             application.state = 'submitted'
#
#     def action_approve(self):
#         for application in self:
#             if application.state != 'submitted':
#                 raise ValidationError("Only submitted applications can be approved.")
#
#             if application.place_id.available_chances < 1:
#                 raise ValidationError(
#                     f"Cannot approve - no available chances at {application.place_id.name}."
#                 )
#
#             application.state = 'approved'
#
#     def action_reject(self):
#         for application in self:
#             if application.state not in ['submitted', 'draft']:
#                 raise ValidationError("Only submitted or draft applications can be rejected.")
#
#             return {
#                 'name': "Rejection Reason",
#                 'type': 'ir.actions.act_window',
#                 'res_model': 'pt.application.reject.wizard',
#                 'view_mode': 'form',
#                 'target': 'new',
#                 'context': {'default_application_id': application.id}
#             }
#
#     def action_draft(self):
#         self.filtered(lambda app: app.state == 'rejected').write({'state': 'draft'})
#
#     @api.constrains('student_id')
#     def _check_duplicate_application(self):
#         for application in self:
#             if application.state in ['submitted', 'approved']:
#                 existing = self.search_count([
#                     ('student_id', '=', application.student_id.id),
#                     ('state', 'in', ['submitted', 'approved']),
#                     ('id', '!=', application.id)
#                 ])
#                 if existing > 0:
#                     raise ValidationError(
#                         "You can only have one active PT application at a time. "
#                         "Cancel your existing application before applying to a new place."
#                     )
#
#     @api.onchange('place_id')
#     def _onchange_place(self):
#         if self.place_id:
#             return {
#                 'warning': {
#                     'title': "Availability Information",
#                     'message': f"Available chances: {self.place_id.available_chances}/{self.place_id.total_chances}"
#                 }
#             }
#
#
#     def action_view_application(self):
#         self.ensure_one()
#         return {
#             'name': 'My Application',
#             'type': 'ir.actions.act_window',
#             'res_model': 'pt.place.application',
#             'view_mode': 'form',
#             'res_id': self.id,
#             'target': 'current',
#         }