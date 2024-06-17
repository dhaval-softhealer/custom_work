# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.


from odoo import models


class PosSessionInherit(models.Model):
    _inherit = "pos.session"

    def _loader_params_pos_category(self):
        result = super(PosSessionInherit,self)._loader_params_pos_category()
        result['search_params']['fields'].append('sh_age')
        return result
    
    def _loader_params_res_partner(self):
        result = super(PosSessionInherit,self)._loader_params_res_partner()
        result['search_params']['fields'].append('Sh_birthdate')
        return result