import json
import math
from ....pharmx_edi.dataclasses.datasyncmessage import Address, ContactInformation, DataSyncMessage, BusinessUnit, Eligibility, Item, AlternativeID, Display, Description, Attribute, OrganizationType, PartnerMaintenance, Partner, SocialMedia, Telephone, ThresholdQuantity
from ....pharmx_edi.services.pharmxservice import PharmXService
from odoo.addons.component.core import Component, AbstractComponent # type: ignore
from odoo import api, fields, models, _
import uuid
from datetime import date, datetime
import ast
import dateutil.parser
import logging
_logger = logging.getLogger(__name__)

class PartnerItem(models.AbstractModel):
    _inherit = 'res.partner'

    def on_partner_updated(self, record, fields=None):
        _logger.info("%r has been created", record)

        partner = PartnerMaintenance(
            PartnerID = str(record.pharmx_site_id),
            BusinessUnit = BusinessUnit(
                SiteID = record.pharmx_site_id,
                SiteName = record.name
            ),
            DoesBusinessAs = record.trding_as or record.name,
            OrganizationTypes=[
                OrganizationType(
                    Code=type.name.replace(" ","")
                )
                for type
                in record.sh_pharmx_type
            ],
            AlternativeBusinessIDs = 
            [
                AlternativeID(
                    Type = id.type,
                    ID = id.value
                )
                for id
                in record.identifier_ids
            ],
            ContactInformation= ContactInformation(
                Address=Address(
                    Street= record.street or "",
                    PostalCode= record.zip or None,
                    Locality= record.city  or "", 
                    Region= record.state_id.name  or "",
                    Country= record.country_id.name if record.country_id else None,
                ),
                Telephone=Telephone(
                    LocalNumber= "0" + record.phone[4:] if record.phone[0] == "+" else record.phone,
                    ITUCountryCallingCode=int(record.phone[1:4].replace(" ", "")) if record.phone[0] == "+" else 0
                ) if record.phone else None,
                Email= record.email or None,
                SocialMedia=
                [
                    id
                    for id
                    in [
                        SocialMedia(
                            Type= "Facebook",
                            Value= record.pharmx_facebook or "",
                            Url= None
                        ),
                        SocialMedia(
                            Type= "Twitter",
                            Value=  record.pharmx_twitter or "",
                            Url= None
                        ),
                        SocialMedia(
                            Type= "Linkedin",
                            Value=  record.pharmx_linkedin or "",
                            Url= None
                        ),
                        # SocialMedia(
                        #     Type= "Instagram",
                        #     Value= "",
                        #     Url=""
                        # ),
                        # SocialMedia(
                        #     Type= "Youtube",
                        #     Value= "",
                        #     Url=""
                        # )
                    ]
                    if  len(id.Value) > 0
                ],
            ),
            ParentCompany=BusinessUnit(
                SiteID=record.sh_parent_company.pharmx_site_id,
                SiteName=record.sh_parent_company.name
            ) if record.sh_parent_company else None
        )
    
        json = partner.to_json(indent=4)

        # Only send out messages if the product has actually changed.
        if record.cached_partner != json:
            
            record.write({ 'cached_partner': json })

            subscriptions = self.env['product.subscription'].search([])

            endpoints = []

            for subscription in subscriptions:
                if subscription.rule_partners_domain:
                    domain = ast.literal_eval(subscription.rule_partners_domain)
                    domain.append(('id', '=', record.id))
                    item = self.env["res.partner"].search(domain, limit=1)
                    if item.id == record.id:
                        endpoints.append(subscription.serviceendpoint)

            if len(endpoints) > 0:

                message = DataSyncMessage(
                    MessageId = uuid.uuid4(),
                    MessageDateTime= datetime.utcnow(),
                    MessageType = "PartnerMaintenance",
                    MessageDirection = "Inbound",
                    OriginatingBusinessUnit = BusinessUnit(SiteID = "15", SiteName = "PharmX", ServiceID="6", ServiceName="Portal"),
                    InitiatingBusinessUnit = BusinessUnit(SiteID = "15", SiteName = "PharmX", ServiceID="6", ServiceName="Portal"),
                    NotifiedBusinessUnits = [BusinessUnit(SiteID= endpoint.partner_id.pharmx_site_id, SiteName = endpoint.partner_id.name, ServiceID= endpoint.service_id, ServiceName= endpoint.name) for endpoint in endpoints],
                    PartnerMaintenance = partner
                )

                _logger.info('creating catalog' + str(message))

                PharmXService.sendMessage(self, message)
