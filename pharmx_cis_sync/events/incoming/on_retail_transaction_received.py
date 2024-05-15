from odoo.addons.component.core import Component # type: ignore
from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)

class OnRetailTransactionreceivedEventListener(Component):
    _name = 'datasync.retailtransaction.received.listener'
    _inherit = 'base.event.listener'

    def on_retail_transaction_received(self, record, fields=None):
        _logger.info("%r has been created", record)
        self.env['pharmx.backend'].with_delay().import_sale_from_pharmx(record)

class PharmXRetailTransactionExporter(models.Model):
    _inherit = 'pharmx.backend'

    def import_sale_from_pharmx(self, a, k=None):
       _logger.info('importing retail transaction from pharmx: %s and k: %s', a, k)

       # Create the Retail Transaction
       