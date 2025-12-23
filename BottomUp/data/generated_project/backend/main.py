from fastapi import FastAPI
from pydantic import BaseModel
from calculator import CalculatorAPI, CalculatorRequest, CalculatorResponse
from calculator import CalculatorService
import uvicorn

app = FastAPI()

class CalculatorRequestModel(BaseModel):
    operation: str
    num1: float
    num2: float

@app.post("/calculate")
async def calculate(request: CalculatorRequestModel):
    operation_map = {
        "add": CalculatorRequest.Operation.ADD,
        "subtract": CalculatorRequest.Operation.SUBTRACT,
        "multiply": CalculatorRequest.Operation.MULTIPLY,
        "divide": CalculatorRequest.Operation.DIVIDE
    }
    request = CalculatorRequest(
        operation=operation_map[request.operation],
        num1=request.num1,
        num2=request.num2
    )
    calculator = CalculatorAPI(CalculatorService())
    response = calculator.calculate(request)
    return response.dict()

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
