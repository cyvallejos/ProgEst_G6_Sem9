"""Aplicación web para interactuar con una pila por sesión."""

import os
import secrets
from typing import cast

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_wtf.csrf import CSRFProtect

from pila import pop_stack, push

MAX_STACK_CAPACITY = 20
MAX_ITEM_LENGTH = 100

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    MAX_CONTENT_LENGTH=16 * 1024,
)
CSRFProtect(app)


def _get_stack_state() -> tuple[list[str], int] | None:
    """Obtiene y valida el estado de pila guardado en la sesión."""
    stack = session.get("stack")
    capacity = session.get("capacity")
    if (
        not isinstance(stack, list)
        or not all(isinstance(item, str) for item in stack)
        or isinstance(capacity, bool)
        or not isinstance(capacity, int)
        or not 1 <= capacity <= MAX_STACK_CAPACITY
    ):
        return None
    return cast(list[str], stack), capacity


def _require_stack() -> tuple[list[str], int] | None:
    state = _get_stack_state()
    if state is None:
        flash("Primero configura una pila para continuar.", "warning")
        return None
    return state


@app.get("/")
def index():
    state = _get_stack_state()
    stack, capacity = state if state is not None else ([], None)
    return render_template(
        "index.html",
        stack_reversed=list(reversed(stack)),
        capacity=capacity,
        item_count=len(stack),
        max_capacity=MAX_STACK_CAPACITY,
        max_item_length=MAX_ITEM_LENGTH,
    )


@app.post("/configurar")
def configure():
    try:
        capacity = int(request.form.get("capacity", ""))
    except ValueError:
        flash("Ingresa una capacidad válida.", "danger")
        return redirect(url_for("index"))

    if not 1 <= capacity <= MAX_STACK_CAPACITY:
        flash(
            f"La capacidad debe estar entre 1 y {MAX_STACK_CAPACITY}.",
            "danger",
        )
        return redirect(url_for("index"))

    session["stack"] = []
    session["capacity"] = capacity
    flash(f"Pila configurada con capacidad para {capacity} elementos.", "success")
    return redirect(url_for("index"))


@app.post("/apilar")
def add_item():
    state = _require_stack()
    if state is None:
        return redirect(url_for("index"))

    stack, capacity = state
    item = request.form.get("item", "").strip()
    if not item:
        flash("Escribe un valor antes de apilarlo.", "danger")
    elif len(item) > MAX_ITEM_LENGTH:
        flash(f"El valor no puede superar {MAX_ITEM_LENGTH} caracteres.", "danger")
    elif push(stack, item, capacity):
        session["stack"] = stack
        flash(f"«{item}» se agregó a la pila.", "success")
    else:
        flash("La pila está llena. Desapila un elemento para continuar.", "warning")
    return redirect(url_for("index"))


@app.post("/desapilar")
def remove_item():
    state = _require_stack()
    if state is None:
        return redirect(url_for("index"))

    stack, _ = state
    item = pop_stack(stack)
    if item is None:
        flash("La pila está vacía; no hay elementos para desapilar.", "warning")
    else:
        session["stack"] = stack
        flash(f"Se desapiló «{item}».", "success")
    return redirect(url_for("index"))


@app.post("/consultar-tope")
def show_top():
    state = _require_stack()
    if state is None:
        return redirect(url_for("index"))

    stack, _ = state
    if stack:
        flash(f"El elemento en el tope es «{stack[-1]}».", "info")
    else:
        flash("La pila está vacía; todavía no tiene un elemento en el tope.", "warning")
    return redirect(url_for("index"))


@app.post("/vaciar")
def clear_stack():
    state = _require_stack()
    if state is None:
        return redirect(url_for("index"))

    _, capacity = state
    session["stack"] = []
    session["capacity"] = capacity
    flash("La pila se vació.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
