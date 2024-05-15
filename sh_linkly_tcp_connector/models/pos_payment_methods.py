# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import models


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    def _get_payment_terminal_selection(self):
        return super()._get_payment_terminal_selection() + [('linkly', 'Linkly')]

