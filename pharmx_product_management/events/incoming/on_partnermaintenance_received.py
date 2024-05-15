from odoo.addons.component.core import Component # type: ignore
from odoo import api, fields, models, _
from ....pharmx_edi.dataclasses.datasyncmessage  import DataSyncMessage, Partner
import logging
from decimal import Decimal
from odoo import fields, models
from datetime import datetime
from typing import List
from dateutil import parser
_logger = logging.getLogger(__name__)
from ...commands.create_partner import create_partner

class OnPartnerMaintenanceReceivedEventListener(Component):
    _name = 'datasync.partnermaintenance.received.listener'
    _inherit = 'base.event.listener'

    def on_Outbound_PartnerMaintenance_received(self, record: DataSyncMessage, fields=None):
        _logger.info("%r has been triggered", record)
        
        create_partner(self, record.PartnerMaintenance)
