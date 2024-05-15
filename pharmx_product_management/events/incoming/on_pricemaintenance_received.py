from odoo.addons.component.core import Component # type: ignore
from odoo import api, fields, models, _
from ....pharmx_edi.dataclasses.datasyncmessage import DataSyncMessage
from ...commands.create_price import create_price
import logging
_logger = logging.getLogger(__name__)

class OnPriceMaintenanceReceivedEventListener(Component):
    _name = 'datasync.pricemaintenance.received.listener'
    _inherit = 'base.event.listener'

    def on_Outbound_PriceMaintenance_received(self, record: DataSyncMessage, fields=None):
        _logger.info("%r has been triggered", record)

        price = create_price(self, record.PriceMaintenance)