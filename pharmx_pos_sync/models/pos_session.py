from odoo import api, fields, models, _
from odoo.tools import formatLang, float_is_zero
from odoo.exceptions import ValidationError, UserError

class PosSessionInherit(models.Model):
    _inherit = 'pos.session'
    
    config_id = fields.Many2one(
        'pos.config', string='Point of Sale',
        help="The physical point of sale you will use.",
        required=False,
        index=True)
    
class PosOrderInherit(models.Model):
    _inherit = 'pos.order'
    
    session_id = fields.Many2one(
        'pos.session', string='Session', required=False, index=True,
        domain="[('state', '=', 'opened')]", states={'draft': [('readonly', False)]},
        readonly=True)
    
    currency_id = fields.Many2one(
        "res.currency", string="Currency",
        related='company_id.currency_id', readonly=True)
    
class PosPaymentInherit(models.Model):
    _inherit = 'pos.payment'
    
    @api.constrains('payment_method_id')
    def _check_payment_method_id(self):
        return
    
class PurchaseOrderLineInherit(models.Model):
    _inherit = 'purchase.order.line'
    
    @api.ondelete(at_uninstall=False)
    def _unlink_except_purchase_or_done(self):
        posSync = self._context.get('pos_sync')
        if posSync: 
            return # AS Overriding, the you cannot delete a purchase order line, if the pos has done it, we must too.
        for line in self:
            if line.order_id.state in ['purchase', 'done']:
                state_description = {state_desc[0]: state_desc[1] for state_desc in self._fields['state']._description_selection(self.env)}
                raise UserError(_('Cannot delete a purchase order line which is in state \'%s\'.') % (state_description.get(line.state),))
