from odoo import models, fields
import base64


URL_BASE = '/gslab_backend_theme/static/src/css/'
URL_SCSS_GEN_TEMPLATE = URL_BASE + 'colors.gen.scss'
DEFAULT_PRIMARY = '#7E4861'
DEFAULT_SECONDARY = '#01A29D'


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    SCSS_TEMPLATE = """
        $o-community-color: %(o_community_color)s;
        $o-community-primary-color: %(o_community_primary_color)s;
    """
    theme_color_brand = fields.Char(
        string="Brand", default=DEFAULT_PRIMARY, help='Default brand color: #7E4861')
    theme_color_primary = fields.Char(
        string="Primary", default=DEFAULT_SECONDARY, help='Default primary color: #01A29D')

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        colors = self._get_colors()
        if colors['$o-community-color'] != self.theme_color_brand or colors['$o-community-primary-color'] != self.theme_color_primary:
            self.create_or_update_scss_attachment()

        return res

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        colors = self._get_colors()
        res.update({
            'theme_color_brand': colors['$o-community-color'] or DEFAULT_PRIMARY,
            'theme_color_primary': colors['$o-community-primary-color'] or DEFAULT_SECONDARY
        })
        return res

    def _get_colors(self):
        colors = {}
        if self._get_content():
            colors = dict(
                x.strip().replace(';', '').split(': ', 1) for x in self._get_content().split('\n')
                if x.find(':') != -1
            )
        return colors

    def create_or_update_scss_attachment(self):
        ir_attachment_obj = self.env['ir.attachment']
        for record in self:
            custom_url = URL_SCSS_GEN_TEMPLATE
            datas = base64.b64encode(
                record._generate_scss().encode('utf-8'))
            custom_attachment = ir_attachment_obj.search([
                ('url', 'like', '%s%%' % custom_url)
            ])
            values = {
                'datas': datas,
                'url': custom_url,
                'name': custom_url,
                # 'datas_fname': custom_url.split("/")[-1],
            }
            if custom_attachment:
                custom_attachment.write(values)
            else:
                values.update({
                    'type': 'binary',
                    'mimetype': 'text/scss',
                })
                ir_attachment_obj.create(values)

        self.env['ir.qweb'].sudo().clear_caches()

    def _get_css_attachment(self, url):
        return self.env["ir.attachment"].with_context(
            bin_size=False, bin_size_datas=False
        ).search([("url", '=', url)])

    def _get_content(self):
        custom_attachment = self._get_css_attachment(URL_SCSS_GEN_TEMPLATE)
        if custom_attachment.exists():
            return base64.b64decode(custom_attachment.datas).decode('utf-8')

        return False

    def _generate_scss(self):
        return self.SCSS_TEMPLATE % {
            'o_community_color': self.theme_color_brand or DEFAULT_PRIMARY,
            'o_community_primary_color': self.theme_color_primary or DEFAULT_SECONDARY
        }
