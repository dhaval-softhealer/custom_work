from ast import Str
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID
from dataclasses_json import dataclass_json, LetterCase, config
from marshmallow import fields
from ...pharmx_edi.dataclasses.datasyncmessage import Operator, Partner, AlternativeID, MerchandiseHierarchy, Item, Attribute, RetailTransaction,Order

from odoo.tools.misc import str2bool

class str(Enum):
    string = "string"

metadata = {}

dataclass_json_config = config(
    encoder=datetime.isoformat,
    decoder=datetime.fromisoformat,
    mm_field=fields.DateTime(format='iso')
)

metadata.update(dataclass_json_config)

@dataclass
class Brand:
    Name: str = None
    
@dataclass
class Manufacturer:
    Name: str = None

@dataclass
class Migration:
    Employees: Optional[List[Operator]] = None
    Suppliers: Optional[List[Partner]] = None
    Brands: Optional[List[Brand]] = None
    Manufacturers: Optional[List[Manufacturer]] = None
    Categories: Optional[List[MerchandiseHierarchy]] = None
    Customers: Optional[List[Partner]] = None
    Items: Optional[List[Item]] = None
    RetailTransactions: Optional[List[RetailTransaction]] = None
    Order: Optional[List[Order]] = None
