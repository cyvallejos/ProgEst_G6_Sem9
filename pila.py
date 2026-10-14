"""Operaciones básicas para una pila limitada."""

from collections.abc import Sequence


def is_empty(stack: Sequence[str]) -> bool:
    return not stack


def is_full(stack: Sequence[str], capacity: int) -> bool:
    if capacity < 1:
        raise ValueError("La capacidad debe ser un entero positivo.")
    return len(stack) >= capacity


def push(stack: list[str], item: str, capacity: int) -> bool:
    if is_full(stack, capacity):
        return False
    stack.append(item)
    return True


def peek(stack: Sequence[str]) -> str | None:
    return stack[-1] if stack else None


def pop_stack(stack: list[str]) -> str | None:
    return stack.pop() if stack else None
