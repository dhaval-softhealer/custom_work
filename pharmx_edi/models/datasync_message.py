import datetime
from email.mime import message
from odoo import models,fields,api
import logging
from types import SimpleNamespace
import json
from ..dataclasses.datasyncmessage import DataSyncMessage
import dateutil.parser
_logger = logging.getLogger(__name__)

class PersistedDataSyncMessage(models.Model):
    _name = 'datasync.message'

    MessageId = fields.Char(string="MessageId", required=True, index=True)
    MessageDateTime = fields.Datetime(string="MessageDateTime", required=True, index=True)
    MessageType = fields.Char(string="MessageType", required=True, index=True)
    MessageDirection = fields.Selection(selection=[('Inbound', 'Inbound'), ('Outbound','Outbound') ], required=True)
    OriginatingBusinessUnitID = fields.Char(string="OriginatingBusinessUnitID", required=True)
    OriginatingBusinessUnitServiceID = fields.Char(string="OriginatingBusinessUnitServiceID")
    InitiatingBusinessUnitID = fields.Char(string="InitiatingBusinessUnitID", required=True)
    InitiatingBusinessUnitServiceID = fields.Char(string="InitiatingBusinessUnitServiceID")
    
    RequestID = fields.Char(string="RequestID")
    ResponseID = fields.Char(string="ResponseID")
    ResponseError = fields.Char(string="ResponseError")
    Message = fields.Text(string="Message")
    
    # Telemetry Fields
    QueueTime = fields.Float(string="Time on Queue (ms)", size=15, digits=(15, 0))
    ValidationTime = fields.Float(string="Time Validating (ms)", size=15, digits=(15, 0))
    RoutingTime = fields.Float(string="Time Routing (ms)", size=15, digits=(15, 0))
    PersistenceTime = fields.Float(string="Time Persisting (ms)", size=15, digits=(15, 0))

    FromQueue = fields.Datetime(string="Pulled From Queue", required=False)
    ToQueue = fields.Datetime(string="Pushed To Queue", required=False)
    ValidationComplete = fields.Datetime(string="Validation Complete", required=False)
    RoutingComplete = fields.Datetime(string="Routing Complete", required=False)
    PersistenceComplete = fields.Datetime(string="Persistance Complete", required=False)

    @api.model
    def retrigger(self):
        for message in self:
            vals = super(PersistedDataSyncMessage, self).fields_get()
            self.env['datasync.message'].with_delay().process(message)
    
    @api.model
    def replay(self):
        #self.env['pharmx.backend'].with_delay().sendBatch(self)
        for message in self:
            vals = super(PersistedDataSyncMessage, self).fields_get()
            self.env['pharmx.backend'].with_delay().send(message)

    @api.model
    def process(self, message):
        datasyncMessage : DataSyncMessage = json.loads(message['Message'], object_hook=lambda d: SimpleNamespace(**d))
        event = "on_{}_{}_received".format(message.MessageDirection, message.MessageType)
        self._event(event).notify(datasyncMessage)
    
    @api.model
    def receive(self, message):
        newMessage = {
                'MessageId': message['MessageId'],
                'MessageDateTime': dateutil.parser.isoparse(message['MessageDateTime']).replace(tzinfo=None),
                'MessageType': message['MessageType'],
                'MessageDirection': message['MessageDirection'],
                'OriginatingBusinessUnitID': message['OriginatingBusinessUnit']['SiteID'],
                'OriginatingBusinessUnitServiceID': message['OriginatingBusinessUnit']['ServiceID'] if 'ServiceID' in message['OriginatingBusinessUnit'] else None,
                'InitiatingBusinessUnitID': message['InitiatingBusinessUnit']['SiteID'],
                'InitiatingBusinessUnitServiceID': message['InitiatingBusinessUnit']['ServiceID'] if 'ServiceID' in message['InitiatingBusinessUnit'] else None,
                'RequestID': message['Request']['RequestID'] if 'Request' in message else None,
                'ResponseID': message['Response']['RequestID'] if 'Response' in message else None,
                'ResponseError': message['Response']['BusinessError']['Description'] if 'Response' in message and 'BusinessError' in message['Response'] else None,
                'Message': json.dumps(message, indent = 4),
                'FromQueue' :dateutil.parser.isoparse(message['Telemetry']['FromQueue']).replace(tzinfo=None),
                'ToQueue' : dateutil.parser.isoparse(message['Telemetry']['ToQueue']).replace(tzinfo=None),
                'ValidationComplete' : dateutil.parser.isoparse(message['Telemetry']['ValidationComplete']).replace(tzinfo=None),
                'RoutingComplete' : dateutil.parser.isoparse(message['Telemetry']['RoutingComplete']).replace(tzinfo=None),
                'PersistenceComplete' :datetime.datetime.utcnow(),
                'QueueTime': self.msbetween(self.tryparse(message['Telemetry']['FromQueue']), self.tryparse(message['Telemetry']['ToQueue'])) if 'FromQueue' in message['Telemetry'] and 'ToQueue' in message['Telemetry'] else None,
                'ValidationTime': self.msbetween(self.tryparse(message['Telemetry']['ValidationComplete']), self.tryparse(message['Telemetry']['FromQueue'])) if 'ValidationComplete' in message['Telemetry'] and 'FromQueue' in message['Telemetry'] else None,
                'RoutingTime': self.msbetween(self.tryparse(message['Telemetry']['RoutingComplete']), self.tryparse(message['Telemetry']['ValidationComplete'])) if 'RoutingComplete' in message['Telemetry'] and 'ValidationComplete' in message['Telemetry'] else None,
                'PersistenceTime': self.msbetween(datetime.datetime.utcnow(), self.tryparse(message['Telemetry']['RoutingComplete'])) if 'RoutingComplete' in message['Telemetry'] else None
        }
        return self.env['datasync.message'].create(newMessage)
    
    @api.model
    def receiveBatch(self, messages):
        newMessages = []
        for message in messages:
            newMessage = {
                    'MessageId': message['MessageId'],
                    'MessageDateTime': dateutil.parser.isoparse(message['MessageDateTime']).replace(tzinfo=None),
                    'MessageType': message['MessageType'],
                    'MessageDirection': message['MessageDirection'],
                    'OriginatingBusinessUnitID': message['OriginatingBusinessUnit']['SiteID'],
                    'OriginatingBusinessUnitServiceID': message['OriginatingBusinessUnit']['ServiceID'] if 'ServiceID' in message['OriginatingBusinessUnit'] else None,
                    'InitiatingBusinessUnitID': message['InitiatingBusinessUnit']['SiteID'],
                    'InitiatingBusinessUnitServiceID': message['InitiatingBusinessUnit']['ServiceID'] if 'ServiceID' in message['InitiatingBusinessUnit'] else None,
                    'RequestID': message['Request']['RequestID'] if 'Request' in message else None,
                    'ResponseID': message['Response']['RequestID'] if 'Response' in message else None,
                    'ResponseError': message['Response']['BusinessError']['Description'] if 'Response' in message and 'BusinessError' in message['Response'] else None,
                    'Message': json.dumps(message, indent = 4),
                    'FromQueue' :dateutil.parser.isoparse(message['Telemetry']['FromQueue']).replace(tzinfo=None),
                    'ToQueue' : dateutil.parser.isoparse(message['Telemetry']['ToQueue']).replace(tzinfo=None),
                    'ValidationComplete' : dateutil.parser.isoparse(message['Telemetry']['ValidationComplete']).replace(tzinfo=None),
                    'RoutingComplete' : dateutil.parser.isoparse(message['Telemetry']['RoutingComplete']).replace(tzinfo=None),
                    'PersistenceComplete' :datetime.datetime.utcnow(),
                    'QueueTime': self.msbetween(self.tryparse(message['Telemetry']['FromQueue']), self.tryparse(message['Telemetry']['ToQueue'])) if 'FromQueue' in message['Telemetry'] and 'ToQueue' in message['Telemetry'] else None,
                    'ValidationTime': self.msbetween(self.tryparse(message['Telemetry']['ValidationComplete']), self.tryparse(message['Telemetry']['FromQueue'])) if 'ValidationComplete' in message['Telemetry'] and 'FromQueue' in message['Telemetry'] else None,
                    'RoutingTime': self.msbetween(self.tryparse(message['Telemetry']['RoutingComplete']), self.tryparse(message['Telemetry']['ValidationComplete'])) if 'RoutingComplete' in message['Telemetry'] and 'ValidationComplete' in message['Telemetry'] else None,
                    'PersistenceTime': self.msbetween(datetime.datetime.utcnow(), self.tryparse(message['Telemetry']['RoutingComplete'])) if 'RoutingComplete' in message['Telemetry'] else None
            }
            newMessages.append(newMessage)
        self.env['datasync.message'].create(newMessages)
    
    def tryparse(self, datetime):
        try:
            return dateutil.parser.parse(datetime)
        except:
            return False
    
    def msbetween(self, endTime: datetime.datetime, startTime: datetime.datetime):
        if endTime == False or startTime == False:
            return False
        range = (endTime.replace(tzinfo=None)-startTime.replace(tzinfo=None))
        return round(range.total_seconds() * 1000)