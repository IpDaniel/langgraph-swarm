"""
Korber WMS API Schemas
Pydantic models for all API payloads based on Functional Design Specification v1.11
"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class KorberModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)  # Allow using both field name and alias
# ============================================================================
# Common / Shared Models
# ============================================================================

class ResultResponse(KorberModel):
    """Standard result response structure used across all API responses"""
    Success: bool = Field(..., description="True or False indicating operation success")
    Code: int = Field(..., description="HTTP status code: 200=Success, 500=Error")
    ErrorMessage: str = Field(default="", description="Error message if applicable")


class EdiData(KorberModel):
    """EDI Data key-value pair"""
    EdiDataID: str = Field(..., max_length=20, description="EDI Data ID Code")
    Value: str = Field(..., max_length=250, description="EDI Data ID Value")


class Remarks(KorberModel):
    """Remarks structure"""
    RemarkLine: str = Field(default="", max_length=2000, description="Remark text")


# ============================================================================
# 1. Inventory Hold Adjustment
# ============================================================================

class InventoryHoldAdjustmentMessageBody(KorberModel):
    """Message body for inventory hold adjustment"""
    CompanyCode: str = Field(..., max_length=2, description="Company Code")
    CustomerCode: str = Field(..., max_length=10, description="Customer Code")
    ItemCode: str = Field(..., max_length=20, description="Item Code")
    InventoryLevel2: str = Field(..., max_length=40, description="Inventory Level 2")
    InventoryLevel3: Optional[str] = Field(default="", max_length=40, description="Inventory Level 3")
    InventoryLevel4: Optional[str] = Field(default="", max_length=40, description="Inventory Level 4")
    HoldCodeFrom: Optional[str] = Field(default="", max_length=4, description="Hold Code From - empty means no hold code")
    HoldCodeTo: Optional[str] = Field(default="", max_length=4, description="Hold Code To - empty means no hold code")


class InventoryHoldAdjustmentRequest(KorberModel):
    """Request payload for inventory hold adjustment API"""
    SourceSystemCode: str = Field(..., max_length=20, description="Name or Code representing the source system")
    MessageId: str = Field(..., max_length=50, description="Unique ID representing a message")
    CreationTime: datetime = Field(..., description="Date & Time in UTC (ISO 8601 format)")
    MessageBody: InventoryHoldAdjustmentMessageBody


class InventoryHoldAdjustmentResponse(KorberModel):
    """Response payload for inventory hold adjustment API"""
    Result: ResultResponse


# ============================================================================
# 2. Inventory Details Query
# ============================================================================

class InventoryDetailsQueryMessageBody(KorberModel):
    """Message body for inventory details query. Does not include headers"""
    CompanyCode: str = Field(..., max_length=2, description="E3PL Company Code")
    CustomerCode: str = Field(..., max_length=10, description="E3PL Customer Code")
    ItemCode: str = Field(..., max_length=20, description="Item Code")
    InventoryLevel2: Optional[str] = Field(default="", max_length=40, description="Inventory Level 2")
    InventoryLevel3: Optional[str] = Field(default="", max_length=40, description="Inventory Level 3")
    InventoryLevel4: Optional[str] = Field(default="", max_length=40, description="Inventory Level 4")


class InventoryDetailsQueryRequest(KorberModel):
    """Request payload for inventory details query API"""
    SourceSystemCode: str = Field(..., max_length=20, description="Name or Code representing the source system")
    MessageId: str = Field(..., max_length=50, description="Unique ID representing a message")
    CreationTime: datetime = Field(..., description="Date & Time in UTC (ISO 8601 format)")
    MessageBody: InventoryDetailsQueryMessageBody


class InventoryDetail(KorberModel):
    """Individual inventory detail record"""
    InventoryLevel2: str = Field(..., max_length=40, description="Inventory Level 2")
    InventoryLevel3: str = Field(..., max_length=40, description="Inventory Level 3")
    InventoryLevel4: str = Field(..., max_length=40, description="Inventory Level 4")
    SkuCode: str = Field(..., max_length=4, description="Unit of Measure / SKU Code (Lowest SKU)")
    QuantityOnHand: str = Field(..., description="Quantity on Hand")
    QuantityAvailable: str = Field(..., description="Quantity Available")
    QuantityOnOrder: str = Field(..., description="Quantity on Order (Allocated)")
    QuantityOnReceipt: str = Field(..., description="Quantity on Receipt")
    QuantityOnShippableHold: str = Field(..., description="Quantity on Shippable Hold Codes")
    QuantityOnNonShippableHold: str = Field(..., description="Quantity on Non-Shippable Hold Codes")
    WeightOnHand: str = Field(..., description="Weight on Hand")
    WeightAvailable: str = Field(..., description="Weight Available")
    WeightOnOrder: str = Field(..., description="Weight on Order (Allocated)")
    WeightOnReceipt: str = Field(..., description="Weight on Receipt")
    WeightOnShippableHold: str = Field(..., description="Weight on Shippable Hold Codes")
    WeightOnNonShippableHold: str = Field(..., description="Weight on Non-Shippable Hold Codes")
    WeightNetOnHand: str = Field(..., description="Weight Net on Hand")
    WeightNetAvailable: str = Field(..., description="Weight Net Available")
    WeightNetOnOrder: str = Field(..., description="Weight Net on Order (Allocated)")
    WeightNetOnReceipt: str = Field(..., description="Weight Net on Receipt")
    WeightNetOnShippableHold: str = Field(..., description="Weight Net on Shippable Hold Codes")
    WeightNetOnNonShippableHold: str = Field(..., description="Weight Net on Non-Shippable Hold Codes")
    WeightMeasureCode: Literal["LBS", "KGS"] = Field(..., description="Weight Measure Code: LBS=Pounds, KGS=Kilograms")


class InventoryDetailsQueryResponse(KorberModel):
    """Result section of inventory details query response"""
    success: bool = Field(..., description="True or False indicating operation success")
    code: str = Field(..., description="HTTP status code")
    ErrorMessage: str = Field(default="", description="Error message if applicable")
    CompanyCode: str = Field(..., max_length=2, description="E3PL Company Code")
    CustomerCode: str = Field(..., max_length=10, description="E3PL Customer Code")
    ItemCode: str = Field(..., max_length=20, description="Item Code")
    Details: List[InventoryDetail] = Field(default_factory=list, description="List of inventory details (max 100 records)")


# ============================================================================
# 3. Inbound Receipt (Create/Replace/Delete)
# ============================================================================

class Shipper(KorberModel):
    """Shipper information"""
    ShipperCode: Optional[str] = Field(default="", max_length=10, description="Shipper Code")
    ShipperName: str = Field(..., max_length=30, description="Shipper Name")
    ShipperAdd1: Optional[str] = Field(default="", max_length=30, description="Shipper Address 1")
    ShipperAdd2: Optional[str] = Field(default="", max_length=30, description="Shipper Address 2")
    ShipperCity: Optional[str] = Field(default="", max_length=30, description="Shipper City")
    ShipperState: Optional[str] = Field(default="", max_length=4, description="Shipper State / Province")
    ShipperZip: Optional[str] = Field(default="", max_length=10, description="Shipper Zip Postal Code")
    ShipperCountry: Optional[str] = Field(default="", max_length=4, description="Shipper Country Code")


class ReceiptDetailLine(KorberModel):
    """Receipt detail line item"""
    ItemCode: str = Field(..., max_length=20, description="Item Code")
    InventoryLevel2: Optional[str] = Field(default="", max_length=40, description="Inventory Level 2")
    InventoryLevel3: Optional[str] = Field(default="", max_length=40, description="Inventory Level 3")
    InventoryLevel4: Optional[str] = Field(default="", max_length=40, description="Inventory Level 4")
    Quantity: int = Field(..., description="Expected Quantity")
    SkuCode: Optional[str] = Field(default="", max_length=4, description="Unit of Measure / SKU Code")
    LineRemarks: Optional[Remarks] = Field(default=None, description="Line Remark")
    EdiDetailData: Optional[List[EdiData]] = Field(default_factory=list, description="EDI Detail Data")


class ReceiptDetails(KorberModel):
    """Receipt details container"""
    DetailLine: List[ReceiptDetailLine] = Field(..., description="List of receipt detail lines")


class CreateReplaceReceiptMessageBody(KorberModel):
    """Message body for create/replace receipt"""
    CompanyCode: str = Field(..., max_length=2, description="E3PL Company Code")
    CustomerCode: str = Field(..., max_length=10, description="E3PL Customer Code")
    WarehouseCode: Optional[str] = Field(default="", max_length=4, description="E3PL Receipt Header Warehouse Code")
    CustomerReferenceNumber: str = Field(..., max_length=20, description="Customer Reference Number")
    ProBillNumber: Optional[str] = Field(default="", max_length=20, description="Customer Pro Bill Number")
    AlternateReference1: Optional[str] = Field(default="", max_length=20, description="Alternate Reference 1")
    AlternateReference2: Optional[str] = Field(default="", max_length=20, description="Alternate Reference 2")
    shipper: Shipper = Field(..., alias="Shipper", description="Shipper information")
    LoadTypeCode: Optional[str] = Field(default="", max_length=4, description="Load Type Code")
    CarrierName: Optional[str] = Field(default="", max_length=30, description="Carrier Name")
    CarrierCode: Optional[str] = Field(default="", max_length=10, description="Carrier Code")
    ReceiptDate: Optional[datetime] = Field(default=None, description="Receipt Date in UTC (default: today)")
    ReceiptExpectedDate: Optional[datetime] = Field(default=None, description="Receipt Expected Date in UTC (default: today)")
    remarks: Optional[Remarks] = Field(default=None, alias="Remarks", description="Header Remark")
    EdiHeaderData: Optional[List[EdiData]] = Field(default_factory=list, description="EDI Header Data")
    Details: ReceiptDetails = Field(..., description="Receipt details")


class CreateReplaceReceiptRequest(KorberModel):
    """Request payload for create/replace receipt API"""
    SourceSystemCode: str = Field(..., max_length=20, description="Name or Code representing the source system")
    MessageId: str = Field(..., max_length=50, description="Unique ID representing a message")
    CreationTime: datetime = Field(..., description="Date & Time in UTC (ISO 8601 format)")
    MessageBody: CreateReplaceReceiptMessageBody


class ReceiptMessage(KorberModel):
    """Receipt message containing receipt number"""
    ReceiptNumber: str = Field(..., description="E3PL Receipt Number")


class ReceiptResponse(KorberModel):
    """Response payload for receipt operations (create/replace/delete)"""
    Message: ReceiptMessage
    Result: ResultResponse


class DeleteReceiptMessageBody(KorberModel):
    """Message body for delete receipt"""
    CompanyCode: str = Field(..., max_length=2, description="E3PL Company Code")
    CustomerCode: Optional[str] = Field(default="", max_length=10, description="E3PL Customer Code")
    CustomerReferenceNumber: Optional[str] = Field(default="", max_length=20, description="Customer Reference Number")
    ReceiptNumber: Optional[str] = Field(default="", description="E3PL Receipt Number")


class DeleteReceiptRequest(KorberModel):
    """Request payload for delete receipt API"""
    SourceSystemCode: str = Field(..., max_length=20, description="Name or Code representing the source system")
    MessageId: str = Field(..., max_length=50, description="Unique ID representing a message")
    CreationTime: datetime = Field(..., description="Date & Time in UTC (ISO 8601 format)")
    MessageBody: DeleteReceiptMessageBody


# ============================================================================
# 4. Outbound Orders (Create/Replace/Delete)
# ============================================================================

class ShipTo(KorberModel):
    """Ship-to address information"""
    ShipToCode: Optional[str] = Field(default="", max_length=10, description="Ship-to Code")
    ShipToName: str = Field(..., max_length=30, description="Ship-to Name")
    ShipToAdd1: Optional[str] = Field(default="", max_length=30, description="Ship-to Address 1")
    ShipToAdd2: Optional[str] = Field(default="", max_length=30, description="Ship-to Address 2")
    ShipToAdd3: Optional[str] = Field(default="", max_length=30, description="Ship-to Address 3")
    ShipToAdd4: Optional[str] = Field(default="", max_length=30, description="Ship-to Address 4")
    ShipToCity: Optional[str] = Field(default="", max_length=30, description="Ship-to City")
    ShipToState: Optional[str] = Field(default="", max_length=4, description="Ship-to State or Province")
    ShipToZip: Optional[str] = Field(default="", max_length=10, description="Ship-to Zip / Postal Code")
    ShipToCountry: Optional[str] = Field(default="", max_length=4, description="Ship-to Country")
    ShipToReference: Optional[str] = Field(default="", max_length=20, description="Ship-to External Reference")


class SoldTo(KorberModel):
    """Sold-to address information"""
    SoldToCode: Optional[str] = Field(default="", max_length=10, description="Sold-to Code")
    SoldToName: Optional[str] = Field(default="", max_length=30, description="Sold-to Name")
    SoldToAdd1: Optional[str] = Field(default="", max_length=30, description="Sold-to Address 1")
    SoldToAdd2: Optional[str] = Field(default="", max_length=30, description="Sold-to Address 2")
    SoldToAdd3: Optional[str] = Field(default="", max_length=30, description="Sold-to Address 3")
    SoldToAdd4: Optional[str] = Field(default="", max_length=30, description="Sold-to Address 4")
    SoldToCity: Optional[str] = Field(default="", max_length=30, description="Sold-to City")
    SoldToState: Optional[str] = Field(default="", max_length=4, description="Sold-to State or Province")
    SoldToZip: Optional[str] = Field(default="", max_length=10, description="Sold-to Zip / Postal Code")
    SoldToCountry: Optional[str] = Field(default="", max_length=4, description="Sold-to Country")


class OrderHeader(KorberModel):
    """Order header information"""
    CompanyCode: str = Field(..., max_length=2, description="E3PL Company Code")
    CustomerCode: str = Field(..., max_length=10, description="E3PL Customer Code")
    CustomerOrderNumber: str = Field(..., max_length=20, description="Customer Order Number")
    ship_to: ShipTo = Field(..., alias="ShipTo", description="Ship-to address")
    WarehouseCode: Optional[str] = Field(default="", max_length=4, description="E3PL Header Warehouse Code")
    PoNumber: Optional[str] = Field(default="", max_length=20, description="PO Number")
    sold_to: Optional[SoldTo] = Field(default=None, alias="SoldTo", description="Sold-to address")
    LoadTypeCode: Optional[str] = Field(default="", max_length=4, description="Load Type Code")
    FreightTermCode: Optional[str] = Field(default="", max_length=4, description="Freight Term Code")
    CodAmount: Optional[str] = Field(default="", description="COD Amount")
    PaymentType: Optional[str] = Field(default="", max_length=4, description="Payment Type")
    CarrierName: Optional[str] = Field(default="", max_length=30, description="Carrier Name")
    CarrierCode: Optional[str] = Field(default="", max_length=4, description="Carrier Code or Carrier SCAC")
    ParcelCarrierAccountNumber: Optional[str] = Field(default="", max_length=20, description="Carrier Account Number")
    OrderDate: Optional[str] = Field(default="", description="Order Date (format: YYYYMMDD or ISO 8601)")
    OrderToShipDate: Optional[str] = Field(default="", description="Order To Ship Date (format: YYYYMMDD or ISO 8601)")
    OrderToArrivepDate: Optional[str] = Field(default="", description="Order To Arrive Date (format: YYYYMMDD or ISO 8601)")
    BillToContaceName: Optional[str] = Field(default="", max_length=30, description="Bill To Contact Name (Carrier Details)")
    BillToTelephone: Optional[str] = Field(default="", max_length=20, description="Bill To Phone (Carrier Details)")
    BillToEmail: Optional[str] = Field(default="", max_length=250, description="Bill To email (Carrier Details)")
    ConsigneeContactName: Optional[str] = Field(default="", max_length=30, description="Consignee Contact Name (Carrier Details)")
    ConsigneeTelephone: Optional[str] = Field(default="", max_length=20, description="Consignee Phone (Carrier Details)")
    ConsigneeEmail: Optional[str] = Field(default="", max_length=250, description="Consignee email (Carrier Details)")
    ConsigneeEiN: Optional[str] = Field(default="", max_length=20, description="Consignee EIN (Carrier Details)")
    ResidentialFlag: Optional[str] = Field(default="", max_length=1, description="Residential Flag (Carrier Details)")
    SignatureRequired: Optional[str] = Field(default="", max_length=1, description="Signature Required (Carrier Details)")
    SaturdayDelivery: Optional[str] = Field(default="", max_length=1, description="Saturday Delivery (Carrier Details)")
    ParcelMessage: Optional[str] = Field(default="", max_length=250, description="Parcel Message (Carrier Details)")
    ParcelReference1: Optional[str] = Field(default="", max_length=40, description="Reference 1 (Carrier Details)")
    ParcelReference2: Optional[str] = Field(default="", max_length=40, description="Reference 2 (Carrier Details)")
    ParcelReference3: Optional[str] = Field(default="", max_length=40, description="Reference 3 (Carrier Details)")
    ParcelReference4: Optional[str] = Field(default="", max_length=40, description="Reference 4 (Carrier Details)")
    ParcelReference5: Optional[str] = Field(default="", max_length=40, description="Reference 5 (Carrier Details)")
    OrderAlternateReference1: Optional[str] = Field(default="", max_length=20, description="Alternate Reference 1")
    OrderAlternateReference2: Optional[str] = Field(default="", max_length=20, description="Alternate Reference 2")


class PartialOrderHeader(BaseModel): # only for updates
    """Partial order header update - only include fields you want to change. All fields are optional."""
    CompanyCode: Optional[str] = Field(default=None, max_length=2, description="E3PL Company Code")
    CustomerCode: Optional[str] = Field(default=None, max_length=10, description="E3PL Customer Code")
    CustomerOrderNumber: Optional[str] = Field(default=None, max_length=20, description="Customer Order Number")
    ship_to: Optional[ShipTo] = Field(default=None, alias="ShipTo", description="Ship-to address")
    WarehouseCode: Optional[str] = Field(default=None, max_length=4, description="E3PL Header Warehouse Code")
    PoNumber: Optional[str] = Field(default=None, max_length=20, description="PO Number")
    sold_to: Optional[SoldTo] = Field(default=None, alias="SoldTo", description="Sold-to address")
    LoadTypeCode: Optional[str] = Field(default=None, max_length=4, description="Load Type Code")
    FreightTermCode: Optional[str] = Field(default=None, max_length=4, description="Freight Term Code")
    CodAmount: Optional[str] = Field(default=None, description="COD Amount")
    PaymentType: Optional[str] = Field(default=None, max_length=4, description="Payment Type")
    CarrierName: Optional[str] = Field(default=None, max_length=30, description="Carrier Name")
    CarrierCode: Optional[str] = Field(default=None, max_length=4, description="Carrier Code or Carrier SCAC")
    ParcelCarrierAccountNumber: Optional[str] = Field(default=None, max_length=20, description="Carrier Account Number")
    OrderDate: Optional[str] = Field(default=None, description="Order Date (format: YYYYMMDD or ISO 8601)")
    OrderToShipDate: Optional[str] = Field(default=None, description="Order To Ship Date (format: YYYYMMDD or ISO 8601)")
    OrderToArrivepDate: Optional[str] = Field(default=None, description="Order To Arrive Date (format: YYYYMMDD or ISO 8601)")
    BillToContaceName: Optional[str] = Field(default=None, max_length=30, description="Bill To Contact Name (Carrier Details)")
    BillToTelephone: Optional[str] = Field(default=None, max_length=20, description="Bill To Phone (Carrier Details)")
    BillToEmail: Optional[str] = Field(default=None, max_length=250, description="Bill To email (Carrier Details)")
    ConsigneeContactName: Optional[str] = Field(default=None, max_length=30, description="Consignee Contact Name (Carrier Details)")
    ConsigneeTelephone: Optional[str] = Field(default=None, max_length=20, description="Consignee Phone (Carrier Details)")
    ConsigneeEmail: Optional[str] = Field(default=None, max_length=250, description="Consignee email (Carrier Details)")
    ConsigneeEiN: Optional[str] = Field(default=None, max_length=20, description="Consignee EIN (Carrier Details)")
    ResidentialFlag: Optional[str] = Field(default=None, max_length=1, description="Residential Flag (Carrier Details)")
    SignatureRequired: Optional[str] = Field(default=None, max_length=1, description="Signature Required (Carrier Details)")
    SaturdayDelivery: Optional[str] = Field(default=None, max_length=1, description="Saturday Delivery (Carrier Details)")
    ParcelMessage: Optional[str] = Field(default=None, max_length=250, description="Parcel Message (Carrier Details)")
    ParcelReference1: Optional[str] = Field(default=None, max_length=40, description="Reference 1 (Carrier Details)")
    ParcelReference2: Optional[str] = Field(default=None, max_length=40, description="Reference 2 (Carrier Details)")
    ParcelReference3: Optional[str] = Field(default=None, max_length=40, description="Reference 3 (Carrier Details)")
    ParcelReference4: Optional[str] = Field(default=None, max_length=40, description="Reference 4 (Carrier Details)")
    ParcelReference5: Optional[str] = Field(default=None, max_length=40, description="Reference 5 (Carrier Details)")
    OrderAlternateReference1: Optional[str] = Field(default=None, max_length=20, description="Alternate Reference 1")
    OrderAlternateReference2: Optional[str] = Field(default=None, max_length=20, description="Alternate Reference 2")


class OrderDetailLine(KorberModel):
    """Order detail line item"""
    ItemCode: str = Field(..., max_length=20, description="Item Code")
    InventoryLevel2: Optional[str] = Field(default="", max_length=40, description="Inventory Level 2")
    InventoryLevel3: Optional[str] = Field(default="", max_length=40, description="Inventory Level 3")
    InventoryLevel4: Optional[str] = Field(default="", max_length=40, description="Inventory Level 4")
    Quantity: int = Field(..., description="Order Quantity")
    SkuCode: Optional[str] = Field(default="", max_length=4, description="Unit of Measure / SKU Code")
    LineRemarks: Optional[Remarks] = Field(default=None, description="Line Remark")
    EdiDetailData: Optional[List[EdiData]] = Field(default_factory=list, description="EDI Detail Data")


class PartialOrderDetailLine(BaseModel):  # only for updates
    """Partial order detail line update - only include fields you want to change. All fields are optional."""
    ItemCode: Optional[str] = Field(default=None, max_length=20, description="Item Code")
    InventoryLevel2: Optional[str] = Field(default=None, max_length=40, description="Inventory Level 2")
    InventoryLevel3: Optional[str] = Field(default=None, max_length=40, description="Inventory Level 3")
    InventoryLevel4: Optional[str] = Field(default=None, max_length=40, description="Inventory Level 4")
    Quantity: Optional[int] = Field(default=None, description="Order Quantity")
    SkuCode: Optional[str] = Field(default=None, max_length=4, description="Unit of Measure / SKU Code")
    LineRemarks: Optional[Remarks] = Field(default=None, description="Line Remark")
    EdiDetailData: Optional[List[EdiData]] = Field(default=None, description="EDI Detail Data")


class OrderDetails(KorberModel):
    """Order details container"""
    DetailLine: List[OrderDetailLine] = Field(..., description="List of order detail lines")


class CreateReplaceOrderMessageBody(KorberModel):
    """Message body for create/replace order"""
    order_header: OrderHeader = Field(..., alias="OrderHeader", description="Order header information")
    remarks: Optional[Remarks] = Field(default=None, alias="Remarks", description="Header Remark")
    EdiHeaderData: Optional[List[EdiData]] = Field(default_factory=list, description="EDI Header Data")
    Details: OrderDetails = Field(..., description="Order details")

class AgentOrder(KorberModel):
    """Represents one order placed by a user, though it requires multiple different orders at the korber level"""
    orders: List[CreateReplaceOrderMessageBody] = Field(default_factory=list, description="All of the orders as they each get placed into korber")

class CreateReplaceOrderRequest(KorberModel):
    """Request payload for create/replace order API"""
    SourceSystemCode: str = Field(..., max_length=20, description="Name or Code representing the source system")
    MessageId: str = Field(..., max_length=50, description="Unique ID representing a message")
    CreationTime: datetime = Field(..., description="Date & Time in UTC (ISO 8601 format)")
    MessageBody: CreateReplaceOrderMessageBody


class OrderMessage(KorberModel):
    """Order message containing order number"""
    OrderNumber: str = Field(..., description="E3PL Order Number")


class OrderResponse(KorberModel):
    """Response payload for order operations (create/replace/delete)"""
    Message: OrderMessage
    Result: ResultResponse


class DeleteOrderMessageBody(KorberModel):
    """Message body for delete order"""
    CompanyCode: str = Field(..., max_length=2, description="E3PL Company Code")
    CustomerCode: Optional[str] = Field(default="", max_length=10, description="E3PL Customer Code")
    CustomerOrderNumber: Optional[str] = Field(default="", max_length=20, description="Customer Order Number")
    OrderNumber: Optional[str] = Field(default="", description="E3PL Order Number")


class DeleteOrderRequest(KorberModel):
    """Request payload for delete order API"""
    SourceSystemCode: str = Field(..., max_length=20, description="Name or Code representing the source system")
    MessageId: str = Field(..., max_length=50, description="Unique ID representing a message")
    CreationTime: datetime = Field(..., description="Date & Time in UTC (ISO 8601 format)")
    MessageBody: DeleteOrderMessageBody

