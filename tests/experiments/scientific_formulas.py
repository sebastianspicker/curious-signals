"""Evaluate only scalar arithmetic used by the scientific regression fixtures.

This is not a phyphox execution engine: buffer scheduling and mobile rendering
remain outside these tests. Unsupported syntax fails instead of executing code.
"""

from __future__ import annotations

import ast
import math
import operator
import re

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}
FUNCTIONS = {"floor": math.floor, "sqrt": math.sqrt}


def arithmetic(expression: str, inputs: list[float]) -> float:
    expression = re.sub(
        r"\[(\d+)_?\]", lambda match: f"({inputs[int(match[1]) - 1]!r})", expression
    ).replace("^", "**")

    def visit(node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            return OPERATORS[type(node.op)](visit(node.left), visit(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -visit(node.operand)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in FUNCTIONS
            and len(node.args) == 1
            and not node.keywords
        ):
            return FUNCTIONS[node.func.id](visit(node.args[0]))
        raise AssertionError(f"Unsupported scientific fixture expression: {ast.dump(node)}")

    return visit(ast.parse(expression, mode="eval").body)


def scalar_output(root, output: str, values: dict[str, float]) -> float:
    if output in values:
        return values[output]
    # Experiments may also route another instrument or reset into this buffer.
    # These fixtures isolate the arithmetic path, not conditional buffer routing.
    matches = [
        node
        for node in root.findall("./analysis/*")
        if node.findtext("output") == output and node.tag in ("formula", "multiply", "power")
    ]
    assert len(matches) == 1, f"Expected one scalar producer for {output}"
    node = matches[0]
    inputs = [
        float(item.text) if item.get("type") == "value" else scalar_output(root, item.text, values)
        for item in node.findall("input")
    ]
    if node.tag == "formula":
        return arithmetic(node.attrib["formula"], inputs)
    if node.tag == "multiply":
        return math.prod(inputs)
    if node.tag == "power":
        by_role = {item.get("as"): value for item, value in zip(node.findall("input"), inputs)}
        return by_role["base"] ** by_role["exponent"]
    raise AssertionError(f"Unsupported scalar fixture producer: {node.tag}")
