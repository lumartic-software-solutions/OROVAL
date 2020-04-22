from odoo import api, fields, models, _


# login popup
class LoginPopup(models.TransientModel):
    _name = 'login.popup'
    
    @api.multi
    def login_popup(self):
        return True