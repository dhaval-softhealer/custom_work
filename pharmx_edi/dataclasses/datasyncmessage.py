from ast import Str
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID
from dataclasses_json import dataclass_json, LetterCase, config
from marshmallow import fields

from odoo.tools.misc import str2bool

class str(Enum):
    string = "string"

metadata = {}

def exclude(x) -> bool:
    """if x is None, do not present in to_json() and to_dict() """
    return x is None

dataclass_json_config = config(
    encoder=datetime.isoformat,
    decoder=datetime.fromisoformat,
    mm_field=fields.DateTime(format='iso'),
    exclude=exclude
)

metadata.update(dataclass_json_config)

@dataclass
class SessionSettle:
    TransactionCount: Optional[int] = None
    TotalNetSalesAmount: Optional[int] = None
    TotalNetReturnAmount: Optional[int] = None
    TotalTaxAmount: Optional[int] = None


@dataclass
class BusinessEOD:
    StartDateTimestamp: Optional[datetime] = None
    EndDateTimestamp: Optional[datetime] = None
    TillID: Optional[str] = None
    Openstr: Optional[str] = None
    Closestr: Optional[str] = None
    SessionSettle: Optional[SessionSettle] = None
    LastransactionSequenceNumber: Optional[str] = None


@dataclass
class Operator:
    Name: Optional[str] = None
    ID: Optional[str] = None
    Email: Optional[str] = None


@dataclass
class ControlTransaction:
    TransactionID: Optional[str] = None
    DateTime: Optional[datetime] = None
    WorkstationID: Optional[str] = None
    SequenceID: Optional[int] = None
    str: Optional[str] = None
    Operator: Optional[Operator] = None
    VoidFlag: Optional[bool] = None
    CurrencyCode: Optional[str] = None
    BusinessEOD: Optional[BusinessEOD] = None


@dataclass
class BusinessUnit:
    SiteName: Optional[str] = None
    SiteID: Optional[int] = None
    ServiceName: Optional[str] = None
    ServiceID: Optional[int] = None


@dataclass
class AlternativeID:
    Type: Optional[int] = None
    ID: Optional[str] = None


@dataclass
class InventoryLoss:
    ItemID: Optional[str] = None
    State: Optional[int] = None
    AlternativeItemIDs: Optional[List[AlternativeID]] = None
    Quantity: Optional[int] = None
    TypeCode: Optional[int] = None


@dataclass
class InventoryPosition:
    Items: Optional[List[InventoryLoss]] = None


@dataclass
class InventoryAction:
    InventoryPosition: Optional[InventoryPosition] = None


@dataclass
class Tax:
    Amount: Optional[int] = None
    TaxType: Optional[int] = None


@dataclass
class OrderLineItem:
    Status: Optional[str] = None
    SupplierItemID: Optional[str] = None
    TypeCode: Optional[str] = None
    ItemID: Optional[str] = None
    AlternativeItemIDs: Optional[List[AlternativeID]] = None
    ItemDescription: Optional[str] = None
    UnitCount: Optional[int] = None
    UnitBaseCostAmount: Optional[int] = None
    UnitsShippedCount: Optional[int] = None
    UnitsDeliveredCount: Optional[int] = None
    UnitsReceivedCount: Optional[int] = None
    UnitsInvoicedCount: Optional[int] = None
    Tax: Optional[Tax] = None
    TaxIncludedInPriceFlag: Optional[bool] = None


@dataclass
class Order:
    SupplierID: Optional[str] = None
    Supplier: Optional[BusinessUnit] = None
    AlternativeSupplierIDs: Optional[List[AlternativeID]] = None
    DocumentID: Optional[str] = None
    AlternativeDocumentIDs: Optional[List[AlternativeID]] = None
    LineItem: Optional[List[OrderLineItem]] = None


@dataclass
class ReceiveInventory:
    DocumentID: Optional[str] = None
    ActualDeliveryDate: Optional[datetime] = None
    ItemID: Optional[str] = None
    AlternativeItemIDs: Optional[List[AlternativeID]] = None
    Quantity: Optional[int] = None


@dataclass
class ReturnToVendor:
    LineItems: Optional[List[InventoryLoss]] = None


@dataclass
class Transfer:
    SourceBusinessUnit: Optional[BusinessUnit] = None
    DestinationBusinessUnit: Optional[BusinessUnit] = None
    LineItems: Optional[List[InventoryLoss]] = None


@dataclass
class InventoryControlTransaction:
    TransactionID: Optional[str] = None
    DateTime: Optional[datetime] = None
    WorkstationID: Optional[str] = None
    SequenceID: Optional[int] = None
    str: Optional[str] = None
    Operator: Optional[Operator] = None
    VoidFlag: Optional[bool] = None
    CurrencyCode: Optional[str] = None
    InventoryLoss: Optional[InventoryLoss] = None
    ReturnToVendor: Optional[ReturnToVendor] = None
    ReceiveInventory: Optional[ReceiveInventory] = None
    Transfer: Optional[Transfer] = None
    Order: Optional[Order] = None


@dataclass
class Description:
    Text: Optional[str] = None


@dataclass
class Display:
    Description: Optional[Description] = None
    ShelfLabel: Optional[Description] = None


@dataclass
class Attribute:
    AttributeName: Optional[str] = None
    AttributeValue: Optional[str] = None


@dataclass
class ThresholdQuantity:
    Units: Optional[int] = None
    UnitOfMeasureCode: Optional[int] = None


@dataclass
class Eligibility:
    ThresholdQuantity: Optional[ThresholdQuantity] = None


@dataclass
class Price:
    Currency: Optional[str] = None
    ValueTypeCode: Optional[int] = None
    Amount: Optional[int] = None
    Eligibility: Optional[Eligibility] = None
    EffectiveDateTimestamp: Optional[datetime] = field(default=None,metadata=metadata)
    ExpirationDateTimestamp: Optional[datetime] = field(default=None, metadata=metadata)


@dataclass
class ManufacturerInformation:
    Manufacturer: Optional[BusinessUnit] = None
    AlternativeManufacturerIDs: Optional[List[AlternativeID]] = None


@dataclass
class MerchandiseHierarchy:
    Level: Optional[str] = None
    Value: Optional[str] = None
    ParentValue: Optional[str] = None


@dataclass
class SupplierInformation:
    SupplierID: Optional[str] = None
    Supplier: Optional[BusinessUnit] = None
    AlternativeSupplierIDs: Optional[List[AlternativeID]] = None
    Description: Optional[str] = None
    StoreOrderAllowedFlag: Optional[bool] = None
    SupplierItemID: Optional[str] = None
    SalesUnitPerPackUnitQuantity: Optional[int] = None
    AlternativeSupplierItemIDs: Optional[List[AlternativeID]] = None
    Attributes: Optional[List[Attribute]] = None
    MerchandiseHierarchy: Optional[List[MerchandiseHierarchy]] = None

@dataclass
class TaxInformation:
    TaxType: Optional[str] = None
    TaxGroupID: Optional[str] = None
    TaxPercent: Optional[str] = None

@dataclass
class Availability:
    StatusCode: Optional[str] = None
    WarehouseID: Optional[str] = None
    Region: Optional[str] = None
    Country: Optional[str] = None

@dataclass_json(letter_case=LetterCase.PASCAL, )
@dataclass
class Product:
    ProductID: Optional[str] = None
    StatusCode: Optional[str] = None
    AlternativeProductIDs: Optional[List[AlternativeID]] = None
    ProductAttributes: Optional[List[Attribute]] = None
    MerchandiseHierarchy: Optional[List[MerchandiseHierarchy]] = None
    ProductPrice: Optional[List[Price]] = None
    ManufacturerInformation: Optional[ManufacturerInformation] = None
    TaxInformation: Optional[List[TaxInformation]] = None
    Display: Optional[Display] = None

@dataclass_json(letter_case=LetterCase.PASCAL, )
@dataclass
class Item:
    ItemID: Optional[str] = None
    SupplierID: Optional[str] = None
    Supplier: Optional[BusinessUnit] = None
    AlternativeSupplierIDs: Optional[List[AlternativeID]] = None
    StatusCode: Optional[int] = None
    AlternativeItemIDs: Optional[List[AlternativeID]] = None
    ItemAttributes: Optional[List[Attribute]] = None
    MerchandiseHierarchy: Optional[List[MerchandiseHierarchy]] = None
    ItemPrice: Optional[List[Price]] = None
    SupplierInformation: Optional[List[SupplierInformation]] = None
    ManufacturerInformation: Optional[ManufacturerInformation] = None
    TaxInformation: Optional[List[TaxInformation]] = None
    Availability: Optional[List[Availability]] = None
    Display: Optional[Display] = None
    SalesUnitPerPackUnitQuantity: Optional[int] = None
    ItemQuantityPerSalesUnit: Optional[int] = None
    OrderQuantityMinimum: Optional[int] = None
    OrderQuantityMaximum: Optional[int] = None
    OrderQuantityMultiple: Optional[int] = None
    Product: Optional[Product] = None

@dataclass_json(letter_case=LetterCase.PASCAL, )
@dataclass
class PriceMaintenance:
    PriceID: Optional[str] = None
    ItemID: Optional[str] = None
    RequestType: Optional[int] = None
    SupplierID: Optional[str] = None
    Supplier: Optional[BusinessUnit] = None
    AlternativeSupplierIDs: Optional[List[AlternativeID]] = None
    AlternativeItemIDs: Optional[List[AlternativeID]] = None
    ItemPrice: Optional[Price] = None

@dataclass
class Request:
    DestinationBusinessUnit: Optional[BusinessUnit] = None
    RequestID: Optional[UUID] = None


@dataclass
class ValidationFailure:
    PropertyName: Optional[str] = None
    ErrorMessage: Optional[str] = None


@dataclass
class BusinessError:
    Severity: Optional[int] = None
    ErrorID: Optional[str] = None
    Code: Optional[int] = None
    Description: Optional[str] = None
    ValidationFailures: Optional[List[ValidationFailure]] = None


@dataclass
class Response:
    RequestID: Optional[UUID] = None
    BusinessError: Optional[BusinessError] = None


@dataclass
class Disposal:
    Method: Optional[int] = None


@dataclass
class TransactionLink:
    ReasonCode: Optional[int] = None
    BusinessUnit: Optional[BusinessUnit] = None
    WorkstationID: Optional[str] = None
    str: Optional[str] = None
    SequenceNumber: Optional[str] = None


@dataclass
class Return:
    ItemType: Optional[int] = None
    ItemID: Optional[str] = None
    AlternativeItemIDs: Optional[List[AlternativeID]] = None
    MerchandiseHierarchy: Optional[List[MerchandiseHierarchy]] = None
    ItemNotOnFileFlag: Optional[bool] = None
    Description: Optional[str] = None
    TaxIncludedInPriceFlag: Optional[bool] = None
    UnitCostPrice: Optional[int] = None
    UnitListPrice: Optional[int] = None
    RegularSalesUnitPrice: Optional[int] = None
    InventoryValuePrice: Optional[int] = None
    ActualSalesUnitPrice: Optional[int] = None
    ExtendedAmount: Optional[int] = None
    DiscountAmount: Optional[int] = None
    ExtendedDiscountAmount: Optional[int] = None
    Quantity: Optional[int] = None
    Tax: Optional[Tax] = None
    TransactionLink: Optional[TransactionLink] = None
    Disposal: Optional[Disposal] = None


@dataclass
class CreditDebit:
    CardType: Optional[int] = None


@dataclass
class Rounding:
    RoundingDirection: Optional[int] = None
    Amount: Optional[int] = None


@dataclass
class Total:
    Amount: Optional[int] = None


@dataclass
class Tender:
    TenderType: Optional[str] = None
    CoPayType: Optional[str] = None
    Amount: Optional[int] = None
    Cashback: Optional[int] = None
    Rounding: Optional[Rounding] = None
    TenderChange: Optional[Total] = None
    CreditDebit: Optional[CreditDebit] = None


@dataclass
class RetailTransactionLineItem:
    VoidFlag: Optional[bool] = None
    SequenceNumber: Optional[str] = None
    BeginDateTime: Optional[datetime] = None
    EndDateTime: Optional[datetime] = None
    Sale: Optional[Return] = None
    Return: Optional[Return] = None
    Tender: Optional[Tender] = None
    TransactionLink: Optional[str] = None


@dataclass
class RetailTransaction:
    TransactionID: Optional[str] = None
    DateTime: Optional[datetime] = None
    WorkstationID: Optional[str] = None
    SequenceID: Optional[int] = None
    BusinessDayDate: Optional[str] = None
    Operator: Optional[Operator] = None
    VoidFlag: Optional[bool] = None
    CurrencyCode: Optional[str] = None
    ManagerApproval: Optional[bool] = None
    ReceiptDateTime: Optional[datetime] = None
    LineItems: Optional[List[RetailTransactionLineItem]] = None
    Total: Optional[Total] = None
    TransactionLink: Optional[TransactionLink] = None


@dataclass
class SaleSoftware:
    ProviderIdentification: Optional[str] = None
    ApplicationName: Optional[str] = None
    SoftwareVersion: Optional[str] = None
    CertificationCode: Optional[str] = None


@dataclass
class SaleTerminalData:
    TerminalEnvironment: Optional[str] = None
    SaleCapabilities: Optional[List[str]] = None
    TotalGroupID: Optional[str] = None


@dataclass
class LoginRequest:
    DateTime: Optional[str] = None
    SaleSoftware: Optional[SaleSoftware] = None
    SaleTerminalData: Optional[SaleTerminalData] = None
    OperatorLanguage: Optional[str] = None
    OperatorID: Optional[str] = None
    ShiftNumber: Optional[str] = None
    POISerialNumber: Optional[str] = None


@dataclass
class LogoutRequest:
    MaintenanceAllowed: Optional[bool] = None


@dataclass
class MessageHeader:
    ProtocolVersion: Optional[str] = None
    MessageClass: Optional[str] = None
    MessageCategory: Optional[str] = None
    MessageType: Optional[str] = None
    ServiceID: Optional[str] = None
    SaleID: Optional[str] = None
    POIID: Optional[str] = None


@dataclass
class PaymentData:
    PaymentType: Optional[str] = None


@dataclass
class AmountsReq:
    Currency: Optional[str] = None
    RequestAmount: Optional[int] = None


@dataclass
class PaymentTransaction:
    AmountsReq: Optional[AmountsReq] = None


@dataclass
class SaleItem:
    ItemID: Optional[int] = None
    Brand: Optional[str] = None
    EanUpc: Optional[str] = None
    ParentItemId: Optional[int] = None
    ProductCode: Optional[str] = None
    ProductLabel: Optional[str] = None
    AdditionalProductInfo: Optional[str] = None
    QuantityInStock: Optional[int] = None
    SaleChannel: Optional[str] = None
    Category: Optional[str] = None
    SubCategory: Optional[str] = None
    Tags: Optional[List[str]] = None
    TaxCode: Optional[str] = None
    UnitOfMeasure: Optional[str] = None
    Quantity: Optional[int] = None
    ItemAmount: Optional[int] = None
    UnitPrice: Optional[int] = None
    CostBase: Optional[int] = None
    Discount: Optional[int] = None


@dataclass
class SaleTransactionID:
    TimeStamp: Optional[str] = None
    TransactionID: Optional[str] = None


@dataclass
class SaleData:
    SaleTransactionID: Optional[SaleTransactionID] = None
    SaleToAcquirerData: Optional[str] = None
    SaleItems: Optional[List[SaleItem]] = None


@dataclass
class PaymentRequest:
    PaymentTransaction: Optional[PaymentTransaction] = None
    SaleData: Optional[SaleData] = None
    PaymentData: Optional[PaymentData] = None


@dataclass
class MessageReference:
    MessageCategory: Optional[str] = None
    SaleID: Optional[str] = None
    ServiceID: Optional[str] = None


@dataclass
class TransactionStatusRequest:
    ReceiptReprintFlag: Optional[bool] = None
    DocumentQualifier: Optional[List[str]] = None
    MessageReference: Optional[MessageReference] = None


@dataclass
class SaleToPOIRequest:
    MessageHeader: Optional[MessageHeader] = None
    LoginRequest: Optional[LoginRequest] = None
    LogoutRequest: Optional[LogoutRequest] = None
    PaymentRequest: Optional[PaymentRequest] = None
    TransactionStatusRequest: Optional[TransactionStatusRequest] = None


@dataclass
class SaleToPOIResponse:
    Result: Optional[str] = None
    AdditionalResponse: Optional[str] = None
    ErrorCondition: Optional[str] = None


@dataclass
class DateFilter:
    DateType: Optional[int] = None
    BeginDate: Optional[datetime] = None
    EndDate: Optional[datetime] = None


@dataclass
class RequestMessage:
    MessageType: Optional[int] = None
    DateFilter: Optional[DateFilter] = None


@dataclass
class SynchronizationRequest:
    RequestMessages: Optional[List[RequestMessage]] = None


@dataclass
class TelemetryItem:
    Type: Optional[int] = None
    StartTime: Optional[datetime] = None
    EndTime: Optional[datetime] = None


@dataclass
class Telemetry:
    ToQueue: Optional[datetime] = None
    FromQueue: Optional[datetime] = None
    ValidationComplete: Optional[datetime] = None
    RoutingComplete: Optional[datetime] = None
    PersistenceComplete: Optional[datetime] = None
    TelemetryItems: Optional[List[TelemetryItem]] = None

@dataclass
class AdditionalField:
    Field: Optional[int] = None
    Value: Optional[str] = None

@dataclass
class AlternateReferenceID:
    Scheme: Optional[str] = None
    ID: Optional[str] = None

@dataclass 
class Line:
    LineReference: Optional[str] = None
    SupplierItemID: Optional[str] = None
    TypeCode: Optional[int] = None
    ItemID: Optional[str] = None
    AlternativeItemIDs: Optional[List[AlternativeID]] = None
    Description: Optional[str] = None
    QuantityOrdered: Optional[int] = None
    UnitOfMeasureCode: Optional[int] = None
    UnitBaseCostAmount: Optional[int] = None
    Tax: Optional[List[Tax]] = None
    TaxIncludedInPriceFlag: Optional[bool] = None

@dataclass
class PurchaseOrderRequest:
    Reference: Optional[str] = None
    AlternateReferenceIDs: Optional[List[AlternateReferenceID]] = None
    Supplier: Optional[BusinessUnit] = None
    AlternativeSupplierIDs: Optional[List[AlternativeID]] = None
    BillToAccountNumber: Optional[str] = None
    DeliveryAccountNumber: Optional[str] = None
    Purchaser: Optional[str] = None
    PurchaserSignature: Optional[str] = None
    DeliverNoEarlierThan: Optional[datetime] = None
    DeliverNoLaterThan: Optional[datetime] = None
    AdditionalFields: Optional[List[AdditionalField]] = None
    LineCount: Optional[int] = None
    Freight: Optional[int] = None
    Lines: Optional[List[Line]] = None

@dataclass
class PurchaseOrderResponse:
    Reference: Optional[str] = None
    AlternateReferenceIDs: Optional[List[AlternateReferenceID]] = None
    Supplier: Optional[BusinessUnit] = None
    AlternativeSupplierIDs: Optional[List[AlternativeID]] = None
    BillToAccountNumber: Optional[str] = None
    DeliveryAccountNumber: Optional[str] = None
    Purchaser: Optional[str] = None
    PurchaserSignature: Optional[str] = None
    DeliverNoEarlierThan: Optional[datetime] = None
    DeliverNoLaterThan: Optional[datetime] = None
    AdditionalFields: Optional[List[AdditionalField]] = None
    LineCount: Optional[int] = None
    Freight: Optional[int] = None
    Lines: Optional[List[Line]] = None
    Id: Optional[str] = None
    AcknowledgedBySupplier: Optional[bool] = None
    ReceivedBySupplier: Optional[datetime] = None
    Status: Optional[int] = None
    SupplierResponse: Optional[str] = None
    Created: Optional[datetime] = None
    Sent: Optional[datetime] = None
    

@dataclass
class OrganizationType:
    Code: Optional[str] = None

@dataclass
class BusinessID:
    ID: Optional[str] = None
    Type: Optional[str] = None

@dataclass
class Address:
    Street: Optional[str] = None
    PostalCode: Optional[str] = None
    Locality: Optional[str] = None
    Region: Optional[str] = None
    Country: Optional[str] = None

@dataclass
class Telephone:
    LocalNumber: Optional[str] = None
    ITUCountryCallingCode: Optional[int] = None

@dataclass
class SocialMedia:
    Type: Optional[str] = None
    Value: Optional[str] = None
    Url: Optional[str] = None

@dataclass
class ContactInformation:
    Address: Optional[Address] = None
    Email: Optional[str] = None
    Telephone: Optional[Telephone] = None
    SocialMedia: Optional[SocialMedia] = None

@dataclass
class Partner:
    PartnerID: Optional[str] = None
    BusinessUnit: Optional[BusinessUnit] = None
    OrganizationTypes:  Optional[List[OrganizationType]] = None
    AlternativeBusinessIDs: Optional[List[BusinessID]] = None
    ContactInformation: Optional[ContactInformation] = None
    DoesBusinessAs: Optional[str] = None
    ParentCompany: Optional[BusinessUnit] = None

@dataclass_json(letter_case=LetterCase.PASCAL)  # now all fields are encoded/decoded from camelCase
@dataclass
class PartnerMaintenance(Partner):
    pass

@dataclass_json(letter_case=LetterCase.PASCAL)  # now all fields are encoded/decoded from camelCase
@dataclass
class DataSyncMessage:
    MessageDateTime: Optional[datetime] = field(metadata=metadata)
    MessageId: Optional[UUID] = None
    MessageType: Optional[int] = None
    MessageDirection: Optional[int] = None
    OriginatingBusinessUnit: Optional[BusinessUnit] = None
    InitiatingBusinessUnit: Optional[BusinessUnit] = None
    DestinationBusinessUnit: Optional[BusinessUnit] = None
    NotifiedBusinessUnits: Optional[List[BusinessUnit]] = None
    DeliveredToBusinessUnits: Optional[List[BusinessUnit]] = None
    Request: Optional[Request] = None
    Response: Optional[Response] = None
    Telemetry: Optional[Telemetry] = None
    RetailTransaction: Optional[RetailTransaction] = None
    ControlTransaction: Optional[ControlTransaction] = None
    InventoryControlTransaction: Optional[InventoryControlTransaction] = None
    InventoryAction: Optional[InventoryAction] = None
    ProductMaintenance: Optional[Product] = None
    ItemMaintenance: Optional[Item] = None
    PriceMaintenance: Optional[PriceMaintenance] = None
    SaleToPOIRequest: Optional[SaleToPOIRequest] = None
    SaleToPOIResponse: Optional[SaleToPOIResponse] = None
    SynchronizationRequest: Optional[SynchronizationRequest] = None
    PurchaseOrderRequest: Optional[PurchaseOrderRequest] = None
    PurchaseOrderResponse: Optional[PurchaseOrderResponse] = None
    PartnerMaintenance: Optional[Partner] = None
