# -*- coding: utf-8 -*-
# from odoo import http


# class CustomPtms(http.Controller):
#     @http.route('/custom_ptms/custom_ptms/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_ptms/custom_ptms/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_ptms.listing', {
#             'root': '/custom_ptms/custom_ptms',
#             'objects': http.request.env['custom_ptms.custom_ptms'].search([]),
#         })

#     @http.route('/custom_ptms/custom_ptms/objects/<model("custom_ptms.custom_ptms"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_ptms.object', {
#             'object': obj
#         })
