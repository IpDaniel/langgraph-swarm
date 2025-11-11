from typing_extensions import ParamSpecKwargs
import requests
import yaml
from typing import Optional
from datetime import datetime
from src.agent.services.wms_interface.interface import WMSInterface
from src.agent.services.wms_interface.korber.schemas import (
    AgentOrder,
    CreateReplaceOrderMessageBody,
    KorberModel,
    InventoryDetailsQueryRequest,
    InventoryDetailsQueryMessageBody,
    InventoryDetailsQueryResponse,
    OrderDetails,
    OrderDetailLine,
    OrderHeader,
    CreateReplaceOrderRequest,
    OrderResponse
)

class KorberInterface(WMSInterface):
    def __init__(self):
        self.token: str = ""
        self.base_url: str= ""
        self.INVENTORY_LOOKUP_ENDPOINT = None
        self.CREATE_REPLACE_ORDER_ENDPOINT = None

    def get(self, payload: KorberModel, endpoint: str):
        headers = {'Authorization': f"Bearer {self.token}"}
        full_url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        response = requests.get(full_url, headers=headers, params=payload.model_dump())
        response.raise_for_status()
        return response.json()

    def post(self, payload: KorberModel, endpoint: str):
        headers = {'Authorization': f"Bearer {self.token}", 'Content-Type': 'application/json'}
        full_url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        response = requests.post(full_url, headers=headers, json=payload.model_dump())
        response.raise_for_status()
        return response.json()

    def put(self, payload: KorberModel, endpoint: str):
        headers = {'Authorization': f"Bearer {self.token}", 'Content-Type': 'application/json'}
        full_url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        response = requests.put(full_url, headers=headers, json=payload.model_dump())
        response.raise_for_status()
        return response.json()

    def delete(self, payload: KorberModel, endpoint: str):
        headers = {'Authorization': f"Bearer {self.token}", 'Content-Type': 'application/json'}
        full_url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        response = requests.delete(full_url, headers=headers, json=payload.model_dump())
        response.raise_for_status()
        return response.json()

    def lookup_item(self, query_body: InventoryDetailsQueryMessageBody) -> InventoryDetailsQueryResponse:
        return self.lookup_item(
            company_code=query_body.CompanyCode,
            customer_code=query_body.CustomerCode,
            item_code=query_body.ItemCode,
            inventory_level2=query_body.InventoryLevel2,
            inventory_level3=query_body.InventoryLevel3,
            inventory_level4=query_body.InventoryLevel4
        )
    
    def lookup_item(
        self,
        company_code: str,
        customer_code: str,
        item_code: str,
        inventory_level2: Optional[str] = None,
        inventory_level3: Optional[str] = None,
        inventory_level4: Optional[str] = None
    ) -> InventoryDetailsQueryResponse:
        """Look up inventory details for a specific item in the WMS.
        
        Returns inventory quantities, weights, and hold status information.
        
        Args:
            company_code: E3PL Company Code (2 characters, e.g., "W1")
            customer_code: E3PL Customer Code (max 10 characters, e.g., "ABC")
            item_code: Item Code to look up (max 20 characters)
            inventory_level2: Optional inventory level 2 filter (max 40 characters)
            inventory_level3: Optional inventory level 3 filter (max 40 characters)
            inventory_level4: Optional inventory level 4 filter (max 40 characters)
        
        Returns:
            Dictionary containing inventory details with quantities and weights
        """
        payload = InventoryDetailsQueryRequest(
            SourceSystemCode="MovoMind",
            MessageId=f"lookup_{datetime.utcnow().timestamp()}",
            CreationTime=datetime.utcnow(),
            MessageBody=InventoryDetailsQueryMessageBody(
                CompanyCode=company_code,
                CustomerCode=customer_code,
                ItemCode=item_code,
                InventoryLevel2=inventory_level2 or "",
                InventoryLevel3=inventory_level3 or "",
                InventoryLevel4=inventory_level4 or ""
            )
        )
        
        response_json = self.get(
            payload=payload, 
            endpoint=self.INVENTORY_LOOKUP_ENDPOINT
            )
        return InventoryDetailsQueryResponse(**response_json)

    # TODO: [API DETAILS NEEDED]: need to know how to determine if the header data is available (dropdowns)
    def check_availability(self, agent_order: AgentOrder) -> str:
        results = [self.check_availability(order=order) for order in agent_order.orders]
        return yaml.dump(results, default_flow_style=False)

    # TODO: [API DETAILS NEEDED]: need to know how to determine if the header data is available (dropdowns)
    def check_availability(self, order: CreateReplaceOrderMessageBody):
        header = order.order_header
        details = order.Details
        return {
            "header": self.check_availability(header=header),
            "details": self.check_availability(details=details)
        }

    # TODO: [API DETAILS NEEDED]: need to know how to determine if the header data is available (dropdowns)
    def check_availability(self, header: OrderHeader):
        pass

    def check_availability(self, details: OrderDetails, header: OrderHeader):
        return [self.check_availability(detail=detail, header=header) for detail in details.DetailLine]

    def check_availability(self, detail: OrderDetailLine, header: OrderHeader):
        try:
            inventory_detail: InventoryDetailsQueryResponse = self.lookup_item(
                company_code=header.CompanyCode,
                customer_code=header.CustomerCode, 
                item_code=detail.ItemCode,
                inventory_level2=detail.InventoryLevel2,
                inventory_level3=detail.InventoryLevel3,
                inventory_level4=detail.InventoryLevel4,
            )
            if inventory_detail.Details:
                total_available_quantity = sum(float(item.QuantityAvailable) for item in inventory_detail.Details)
                is_available = total_available_quantity > detail.Quantity
                return {"item_code": detail.ItemCode, "is_available": is_available, "inventory_details": [item.model_dump() for item in inventory_detail.Details]}
            else:
                return {"item_code": detail.ItemCode, "is_available": False, "inventory_details": []}
        except Exception as e:
            print(f"Error checking availability for item {detail.ItemCode}: {e}")
            return {"item_code": detail.ItemCode, "is_available": False, "error": str(e)}

    # TODO: [API DETAILS NEEDED]: need to know how to get a customer's header mappings
    def check_customer_schema(self, customer_code: str) -> str:
        pass

    def place_order(self, order: CreateReplaceOrderMessageBody):
        payload = CreateReplaceOrderRequest(
            SourceSystemCode="MovoMind",
            MessageId=f"lookup_{datetime.utcnow().timestamp()}",
            CreationTime=datetime.utcnow(),
            MessageBody=order
        )

        response_json = self.get(
            payload=payload, 
            endpoint=self.INVENTORY_LOOKUP_ENDPOINT
            )
        return OrderResponse(**response_json)