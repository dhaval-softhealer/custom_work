from odoo import models, api, fields, exceptions

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Set Australia as default country
    @api.model
    def default_get(self, fields):
        rec = super(ResPartner, self).default_get(fields)
        domain = [('code', '=', 'AU'),('name','=','Australia')]
        find_country = self.env['res.country'].search(domain)
        if find_country:
            rec['country_id'] = find_country.id
        return rec
    
    # Set selected company as Signup Company
    signup_company_id = fields.Many2one(
        'res.company', 
        string='Signup Company',
        default=lambda self: self.env.company
    )

    # Set constraint for duplicate email addresses
    # @api.constrains('email')
    # def _check_duplicate_email(self):
    #     for partner in self:
    #         if partner.email:
    #             duplicate_partners = self.env['res.partner'].search([('email', '=', partner.email), ('id', '!=', partner.id)])
    #             if duplicate_partners:
    #                 raise exceptions.ValidationError("A contact with this email address already exists.")