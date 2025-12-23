from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

class Operation(Enum):
    ADD = 1
    SUBTRACT = 2
    MULTIPLY = 3
    DIVIDE = 4

@dataclass
class CalculatorRequest:
    operation: Operation
    num1: float
    num2: float

@dataclass
class CalculatorResponse:
    result: float
    message: str

class CalculatorService:
    def calculate(self, request: CalculatorRequest) -> CalculatorResponse:
        if request.operation == Operation.ADD:
            return CalculatorResponse(request.num1 + request.num2, "Result of addition")
        elif request.operation == Operation.SUBTRACT:
            return CalculatorResponse(request.num1 - request.num2, "Result of subtraction")
        elif request.operation == Operation.MULTIPLY:
            return CalculatorResponse(request.num1 * request.num2, "Result of multiplication")
        elif request.operation == Operation.DIVIDE:
            if request.num2 != 0:
                return CalculatorResponse(request.num1 / request.num2, "Result of division")
            else:
                return CalculatorResponse(0, "Cannot divide by zero")
        else:
            return CalculatorResponse(0, "Invalid operation")

class CalculatorAPI:
    def __init__(self, service: CalculatorService):
        self.service = service

    def calculate(self, request: CalculatorRequest) -> CalculatorResponse:
        return self.service.calculate(request)

class Calculator:
    def __init__(self):
        self.history = []

    def add(self, num1, num2):
        """Add two numbers"""
        result = num1 + num2
        self.history.append(f"Added {num1} and {num2}, result = {result}")
        return result

    def subtract(self, num1, num2):
        """Subtract two numbers"""
        result = num1 - num2
        self.history.append(f"Subtracted {num2} from {num1}, result = {result}")
        return result

    def multiply(self, num1, num2):
        """Multiply two numbers"""
        result = num1 * num2
        self.history.append(f"Multiplied {num1} and {num2}, result = {result}")
        return result

    def divide(self, num1, num2):
        """Divide two numbers"""
        if num2 == 0:
            raise ValueError("Cannot divide by zero")
        result = num1 / num2
        self.history.append(f"Divided {num1} by {num2}, result = {result}")
        return result

    def get_history(self):
        """Get the calculation history"""
        return self.history

# === file: main.py ===




# === file: .env ===


# === file: __init__.py ===

# This file is empty, but it's required for Python packages

# === file: main.py (updated) ===

