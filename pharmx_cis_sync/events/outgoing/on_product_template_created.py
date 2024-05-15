# from ....pharmx_edi.dataclasses.datasyncmessage import DataSyncMessage, DestinationBusinessUnit
# from ....pharmx_edi.services.pharmxservice import PharmXService
# from odoo.addons.component.core import Component, AbstractComponent # type: ignore
# from odoo import api, fields, models, _
# import uuid
# from datetime import date, datetime
# import logging
# _logger = logging.getLogger(__name__)

# class ProductTemplate(models.AbstractModel):
#     _inherit = 'product.template'

#     @api.model
#     def create(self, vals):
#         record = super(ProductTemplate, self).create(vals)
#         self._event('on_product_template_created').notify(record, fields=vals.keys())
#         return record

# class ProductCreatedEventListener(Component):
#     _name = 'datasync.producttemplate.created.event.listener'
#     _inherit = 'base.event.listener'

#     def on_product_template_created(self, record, fields=None):
#         _logger.info("%r has been created", record)
#         self.env['pharmx.backend'].with_delay().export_product_record_to_pharmx(record)

# class PharmXExporter(models.Model):
#     _inherit = 'pharmx.backend'

#     def export_product_record_to_pharmx(self, a, k=None):
#         _logger.info('exporting record to pharmx: %s and k: %s', a, k)
#         message = DataSyncMessage(
#             MessageId = uuid.uuid4(),
#             MessageDateTime = datetime.today().isoformat(),
#             MessageType = "CatalogMaintenance",
#             MessageDirection = "Inbound",
#             OriginatingBusinessUnit = DestinationBusinessUnit(SiteID = "3", SiteName = ""),
#             InitiatingBusinessUnit = DestinationBusinessUnit(SiteID = "301", SiteName = ""),
#             NotifiedBusinessUnits = None,
#             Telemetry = None,
#             RetailTransaction = None
#         )
#         _logger.info('creating catalog' + str(message))
#         # Commented out, not needed for now.
#         # PharmXService.send(self, message)
