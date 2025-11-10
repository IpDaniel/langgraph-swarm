import requests
from typing import Optional
from datetime import datetime
from src.agent.services.wms_interface.interface import WMSInterface
from src.agent.services.wms_interface.korber.schemas import (
    KorberModel,
    InventoryDetailsQueryRequest,
    InventoryDetailsQueryMessageBody,
    InventoryDetailsQueryResponse
)

class KorberInterface(WMSInterface):
    def __init__(self, token: str, base_url: str):
        self.token = token
        self.base_url = base_url

        # constants
        self.INVENTORY_LOOKUP_ENDPOINT = None

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