from pydantic import BaseModel
from typing import List

class Detail(BaseModel):
    code: int
    content: str

    def __str__(self):
        return f"- {self.code:04d}: {self.content}"

class CustomerContext(BaseModel):
    details: List[Detail] = []

    def __str__(self):
        output = ""
        for detail in self.details:
            output += str(detail)

    def delete_detail(self, code: int):
        self.details = [detail for detail in self.details if detail.code != code]

    def add_detail(self, content: int):
        existing_codes = {detail.code for detail in self.details}
        
        if existing_codes:
            new_code = max(existing_codes) + 1
        else:
            new_code = 1
            
        new_detail = Detail(code=new_code, content=str(content))
        self.details.append(new_detail)
    
    def change_detail(self, code: int, new_content: str):
        for detail in self.details:
            if detail.code == code:
                detail.content = new_content
                return 
