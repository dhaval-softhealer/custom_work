from odoo.addons.component.core import Component # type: ignore
from odoo import api, fields, models, _
from ....pharmx_edi.dataclasses.datasyncmessage import DataSyncMessage
import logging
_logger = logging.getLogger(__name__)

class OnInventoryTransactionReceivedEventListener(Component):
    _name = 'datasync.inventorytransaction.received.listener'
    _inherit = 'base.event.listener'

    def on_Outbound_InventoryControlTransaction_received(self, record: DataSyncMessage, fields=None):
        _logger.info("%r has been triggered", record)

        print(record.MessageType, record.MessageDateTime)
        print(record.MessageType, record.MessageDateTime)
