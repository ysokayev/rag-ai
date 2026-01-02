import re
import math
from typing import Dict, List, Any, Optional
import simpleeval

class SafeCalculator:
    """
    A deterministic safe calculator using simpleeval.
    Prevents injection while allowing math expressions.
    """
    
    def __init__(self):
        self.functions = simpleeval.DEFAULT_FUNCTIONS.copy()
        self.functions.update({
            'min': min,
            'max': max,
            'pow': math.pow,
            'sqrt': math.sqrt,
            'ceil': math.ceil,
            'floor': math.floor
        })
        self.operators = simpleeval.DEFAULT_OPERATORS.copy()
        
    def _strip_units(self, expression: str) -> str:
        """
        Removes common unit suffixes (VA, W, A, ft, etc.) to clean expression.
        "180 VA * 10" -> "180 * 10"
        """
        # Units to strip - be careful not to strip variable names if possible
        # Strategy: Remove ' VA', ' Amps', ' V', etc. if preceded by digit or space
        # Simple regex for common code units
        units = ['VA', 'A', 'Amps', 'W', 'Watts', 'V', 'Volts', 'ft', 'm', 'sq ft']
        cleaned = expression
        for unit in units:
             # Case insensitive replace of unit if at end or boundary
             # Match number + space + unit? Or just unit boundary
             # e.g. "120V" -> "120"
             pattern = re.compile(f"(\\d)\\s*{unit}\\b", re.IGNORECASE)
             cleaned = pattern.sub(r"\1", cleaned)
             
        return cleaned

    def evaluate_expression(self, expression: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Evaluates a math string safely.
        """
        if variables is None:
            variables = {}
            
        clean_expr = self._strip_units(expression)
        
        try:
            result = simpleeval.simple_eval(
                clean_expr,
                names=variables,
                functions=self.functions,
                operators=self.operators
            )
            return {"result": result, "original": expression, "cleaned": clean_expr}
        except Exception as e:
            return {"error": f"Calculation failed: {e}", "expression": expression}

    def receptacle_demand(self, quantity: int, va_per_yoke: float = 180.0) -> Dict[str, Any]:
        """
        NEC Receptacle Demand Helper.
        """
        total = quantity * va_per_yoke
        return {
            "result": total,
            "unit": "VA",
            "formula": f"{quantity} * {va_per_yoke}",
            "description": "Standard receptacle calculation"
        }
    
    # Generic wrapper for tool usage
    def compute_demand(self, items: List[Dict]) -> Dict[str, Any]:
        # Keep backward compatibility with previous implementation if needed
        total = 0
        details = []
        for item in items:
            q = float(item.get('quantity', 0))
            v = float(item.get('load_va', 0))
            total += q * v
            details.append(f"{q} * {v}")
        return {"result": total, "unit": "VA", "steps": details}
