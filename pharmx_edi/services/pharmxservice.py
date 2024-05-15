from ast import List, Raise
from odoo import models,fields,api
import datetime
import logging
import json
import requests
import dateutil.parser
_logger = logging.getLogger(__name__)
from types import SimpleNamespace
from ..dataclasses.datasyncmessage import DataSyncMessage

class PharmXService(models.Model):
    _name = 'pharmx.backend'
    _description = 'PharmX Backend'
    
    inbound_shared_access_key = fields.Char(string='InboundboundSharedAccessKey')
    inbound_shared_access_key_name = fields.Char(string='InboundboundSharedAccessKeyName')
    outbound_shared_access_key = fields.Char(string='OutboundSharedAccessKey')
    outbound_shared_access_key_name = fields.Char(string='OutboundSharedAccessKeyName')
    site_id = fields.Char(string='SiteID')
    service_id = fields.Char(string='ServiceID')         
    rest_api_address = fields.Char(string='Rest API Address')

    def receive(self, limitCount = 1000, limitTime = 30, sessionEnabled = "True"):
        config = self.env['pharmx.backend'].search([])
        parameters = {
            'limitCount': limitCount,
            'limitTime': limitTime
        }
        headers = {
            "OutboundSharedAccessKey": config.outbound_shared_access_key,
            "OutboundSharedAccessKeyName": config.outbound_shared_access_key_name,
            "SiteID": config.site_id,
            "ServiceID": config.service_id if config.service_id else None,
            "SessionEnabled": sessionEnabled
        }

        response = requests.get(config.rest_api_address.format(limitCount, limitTime), headers = headers, params = parameters)
        messages = response.json()

        for message in messages:
            newMessage = {
                'MessageId': message['MessageId'],
                'MessageDateTime': dateutil.parser.isoparse(message['MessageDateTime']).replace(tzinfo=None),
                'MessageType': message['MessageType'],
                'MessageDirection': message['MessageDirection'],
                'OriginatingBusinessUnitID': message['OriginatingBusinessUnit']['SiteID'],
                'InitiatingBusinessUnitID': message['InitiatingBusinessUnit']['SiteID'],
                'RequestID': message['Request']['RequestID'] if message['Request'] else None,
                'ResponseID': message['Response']['RequestID'] if message['Response'] else None,
                'ResponseError': message['Response']['BusinessError']['Description'] if message['Response'] and message['Response']['BusinessError'] else None,
                'Message': json.dumps(message, indent = 4)
            }
            created_message = self.env['datasync.message'].create(newMessage)
            self.env['datasync.message'].with_delay().process(created_message)
            

    def send(self, message):
        config = self.env['pharmx.backend'].search([])
        datasyncMessage : DataSyncMessage = json.loads(message['Message'], object_hook=lambda d: SimpleNamespace(**d))
        headers = {
            "InboundSharedAccessKey": config.inbound_shared_access_key,
            "InboundSharedAccessKeyName": config.inbound_shared_access_key_name,
            "SiteID": str(datasyncMessage.OriginatingBusinessUnit.SiteID),
            "ServiceID": str(datasyncMessage.OriginatingBusinessUnit.ServiceID) if hasattr(datasyncMessage.OriginatingBusinessUnit, 'ServiceID') else None,
            'Content-Type': 'application/json'
        }
        
        requests.put(config.rest_api_address, data=message['Message'], headers = headers)

    def log_message(self, message : DataSyncMessage):

        log = {
            'MessageId': message.MessageId,
            'MessageDateTime': message.MessageDateTime,
            'MessageType': message.MessageType,
            'MessageDirection': message.MessageDirection,
            'OriginatingBusinessUnitID': message.OriginatingBusinessUnit.SiteID,
            'InitiatingBusinessUnitID': message.InitiatingBusinessUnit.SiteID,
            'RequestID': message.Request.RequestID if message.Request else None,
            'ResponseID': message.Response.RequestID if message.Response else None,
            'ResponseError': message.Response.BusinessError.Description if message.Response and message.Response.BusinessError else None,
            'Message': message.to_json() # json.dumps(message, indent = 4)
        }
        
        self.env['datasync.message'].create(log)
    
    def sendMessage(self, message : DataSyncMessage):
        config = self.env['pharmx.backend'].search([])
        
        headers = {
            "InboundSharedAccessKey": config.inbound_shared_access_key,
            "InboundSharedAccessKeyName": config.inbound_shared_access_key_name,
            "OutboundSharedAccessKey": config.outbound_shared_access_key,
            "OutboundSharedAccessKeyName": config.site_id + "." + config.service_id if config.service_id else config.site_id,
            "SiteID": str(message.OriginatingBusinessUnit.SiteID),
            "ServiceID": str(message.OriginatingBusinessUnit.ServiceID) if hasattr(message.OriginatingBusinessUnit, 'ServiceID') else None,
            'Content-Type': 'application/json'
        }
        
        json = message.to_json()
        
        response = requests.put(config.rest_api_address, data=json, headers = headers)

        if response.status_code != 200:
            raise Exception("Failed to send outbound message: " + str(message.MessageId) + "." + response.text)

    def sendRequest(self, message : DataSyncMessage):
        config = self.env['pharmx.backend'].search([])
        
        headers = {
            "InboundSharedAccessKey": config.inbound_shared_access_key,
            "InboundSharedAccessKeyName": config.inbound_shared_access_key_name,
            "OutboundSharedAccessKey": config.outbound_shared_access_key,
            "OutboundSharedAccessKeyName": config.site_id + "." + config.service_id if config.service_id else config.site_id,
            "SiteID": str(message.OriginatingBusinessUnit.SiteID),
            "ServiceID": str(message.OriginatingBusinessUnit.ServiceID) if hasattr(message.OriginatingBusinessUnit, 'ServiceID') else None,
            'Content-Type': 'application/json'
        }
        
        json = message.to_json()
        
        response = requests.patch(config.rest_api_address, data=json, headers = headers)
        
        return response.json()

    def sendBatch(self, messages, sendingSiteID: str, sendingServiceID: str):
        config = self.env['pharmx.backend'].search([])
        jsonStrings = [message.to_json() for message in messages]
        jsonString =  '[' + ','.join(jsonStrings) + ']' 
        headers = {
            "InboundSharedAccessKey": config.inbound_shared_access_key,
            "InboundSharedAccessKeyName": config.inbound_shared_access_key_name,
            "OutboundSharedAccessKey": config.outbound_shared_access_key,
            "OutboundSharedAccessKeyName": config.site_id + "." + config.service_id if config.service_id else config.site_id,
            "SiteID": sendingSiteID,
            "ServiceID": sendingServiceID,
            'Content-Type': 'application/json'
        }
        
        response = requests.post(config.rest_api_address, data=jsonString, headers = headers)

        if response.status_code != 200:
            raise Exception("Failed to send outbound batch messages" + "." + response.text)

    # This could be done, but it would need to be split by origin, also not sure how large of a batch size the rest api can handle.
    # Might be easier to just do thousands of small sends on the queue.
    # def sendBatch(self, messages):
    #     config = self.env['pharmx.backend'].search([])
    #     headers = {
    #         "InboundSharedAccessKey": config.inbound_shared_access_key,
    #         "InboundSharedAccessKeyName": config.inbound_shared_access_key_name,
    #         "SiteID": str(siteid),
    #         "ServiceID": str(serviceid) if serviceid else None,
    #         'Content-Type': 'application/json'
    #     }
    #     # I think need to go through and array of messages it, then json dumps out array.
    #     jsonString =  '[' & ','.join(messages) & ']' 
    #     requests.post('https://dev-datasync-restapi.azurewebsites.net/REST', json=jsonString, headers = headers)
