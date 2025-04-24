# Copyright 2019 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

from odoo import SUPERUSER_ID, api

URL_BASE = '/gslab_backend_theme/static/src/css/'
URL_SCSS_GEN_TEMPLATE = URL_BASE + 'colors.gen.scss'


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["ir.attachment"].search([('url', 'like', '%s%%' % URL_BASE)]).unlink()


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    res_config = env['res.config.settings']
    custom_url = URL_SCSS_GEN_TEMPLATE
    datas = base64.b64encode(res_config._generate_scss().encode('utf-8'))
    custom_attachment = env['ir.attachment'].search([
        ('url', 'like', '%s%%' % custom_url)
    ])
    values = {
        'datas': datas,
        'url': custom_url,
        'name': custom_url,
    }
    if custom_attachment:
        custom_attachment.write(values)
    else:
        values.update({
            'type': 'binary',
            'mimetype': 'text/scss',
        })
        env['ir.attachment'].create(values)

    env['ir.qweb'].sudo().clear_caches()
