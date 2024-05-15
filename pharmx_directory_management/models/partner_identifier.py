from odoo import api, fields, models, _
import ast

class PartnerIdentifier(models.Model):
    _name = 'res.partner.identifier'
    
    partner_id = fields.Many2one('res.partner', 'Partner')
     
    type = fields.Selection([
        ('USI', 'Universal Supplier Identifier'),
        ('ABN', 'Australian Business Number'),
        ('ASX', 'Australian Stock Exchange Code'),
        ('ApprovalNumber', 'Approval Number'),
    ], required=True, index=True)
    value = fields.Char(string="Value", index=True)
    
    @api.model
    def _name_search(self,
                     name,
                     args=None,
                     operator='ilike',
                     limit=100,
                     name_get_uid=None):
        res = super(PartnerIdentifier, self)._name_search(name=name,
                                                  args=args,
                                                  operator=operator,
                                                  limit=limit,
                                                  name_get_uid=name_get_uid)
        identifier_search = list(
            self._search([('value', '=', name)] + args,
                         limit=limit,
                         access_rights_uid=name_get_uid))
        if identifier_search:
            return res + identifier_search
        return res
