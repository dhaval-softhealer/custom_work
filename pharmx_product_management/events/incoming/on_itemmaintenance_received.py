from odoo.addons.component.core import Component # type: ignore
from odoo import api, fields, models, _
from ....pharmx_edi.dataclasses.datasyncmessage  import AlternativeID, DataSyncMessage, Item
import logging
from decimal import Decimal
from odoo import fields, models
from datetime import datetime
from typing import List
from dateutil import parser
_logger = logging.getLogger(__name__)
from ...commands.create_product import create_product
from ...commands.create_item import create_item

class OnItemMaintenanceReceivedEventListener(Component):
    _name = 'datasync.itemmaintenance.received.listener'
    _inherit = 'base.event.listener'

    def on_Outbound_ItemMaintenance_received(self, record: DataSyncMessage, fields=None):
        _logger.info("%r has been triggered", record)
        
        product = create_product(self, record.ItemMaintenance.Product)
        create_item(self, record.ItemMaintenance, product)
