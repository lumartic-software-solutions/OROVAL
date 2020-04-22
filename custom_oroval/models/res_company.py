from odoo import models, fields, api, tools


class ResCompany(models.Model):
    _inherit = "res.company"

    custom_header = fields.Boolean('Custom Header')
    header_text = fields.Text('Header Text')
    footer_text = fields.Text('Footer Text')
    image_footer = fields.Binary('Add Image Footer')
    footer_selection = fields.Selection([('footer_text', 'Footer Text'), ('image_footer', 'Footer Image')], 'Footer Selection')

