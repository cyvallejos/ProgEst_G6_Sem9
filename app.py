"""Aplicación web para interactuar con una pila por sesión."""

import base64
import binascii
import os
import re
import secrets
import uuid
from io import BytesIO
from pathlib import Path
from typing import cast

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from flask_wtf.csrf import CSRFProtect
from PIL import Image, UnidentifiedImageError

from pila import pop_stack, push

MAX_STACK_CAPACITY = 20
MAX_ITEM_LENGTH = 100
MAX_PHOTO_BYTES = 2 * 1024 * 1024
PHOTO_PREFIX = "foto:"
PHOTO_ID_PATTERN = re.compile(r"[a-f0-9]{32}\Z")
PHOTO_DIRECTORY = Path("photos")

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    MAX_CONTENT_LENGTH=3 * 1024 * 1024,
)
CSRFProtect(app)


def _photo_path(photo_id: str) -> Path:
    if not PHOTO_ID_PATTERN.fullmatch(photo_id):
        abort(404)
    return Path(app.instance_path) / PHOTO_DIRECTORY / f"{photo_id}.jpg"


def _delete_photo(item: str) -> bool:
    if not item.startswith(PHOTO_PREFIX):
        return True
    try:
        _photo_path(item.removeprefix(PHOTO_PREFIX)).unlink(missing_ok=True)
    except OSError:
        app.logger.exception("No se pudo eliminar una foto de la pila.")
        return False
    return True


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
        photo_prefix=PHOTO_PREFIX,
    )


@app.get("/fotos/<photo_id>")
def photo(photo_id: str):
    state = _get_stack_state()
    if state is None or f"{PHOTO_PREFIX}{photo_id}" not in state[0]:
        abort(404)
    path = _photo_path(photo_id)
    if not path.is_file():
        abort(404)
    return send_file(path, mimetype="image/jpeg", conditional=True)


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

    photos_deleted = True
    state = _get_stack_state()
    if state is not None:
        for item in state[0]:
            if not _delete_photo(item):
                photos_deleted = False
    session["stack"] = []
    session["capacity"] = capacity
    flash(f"Pila configurada con capacidad para {capacity} elementos.", "success")
    if not photos_deleted:
        flash("No se pudieron borrar todas las fotos de la pila anterior.", "warning")
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


@app.post("/apilar-foto")
def add_photo():
    state = _require_stack()
    if state is None:
        return redirect(url_for("index"))

    stack, capacity = state
    if len(stack) >= capacity:
        flash("La pila está llena. Desapila un elemento antes de agregar una foto.", "warning")
        return redirect(url_for("index"))

    photo_data = request.form.get("photo_data", "")
    header, separator, encoded_photo = photo_data.partition(",")
    if (
        not separator
        or header != "data:image/jpeg;base64"
        or len(encoded_photo) > (MAX_PHOTO_BYTES * 4 // 3) + 4
    ):
        flash("Captura una foto válida antes de agregarla a la pila.", "danger")
        return redirect(url_for("index"))

    try:
        image_bytes = base64.b64decode(encoded_photo, validate=True)
        if len(image_bytes) > MAX_PHOTO_BYTES:
            raise ValueError("La foto supera el tamaño permitido.")
        with Image.open(BytesIO(image_bytes)) as image:
            if image.format != "JPEG" or image.width > 1920 or image.height > 1920:
                raise ValueError("La imagen debe ser una foto JPEG de hasta 1920 px.")
            image.verify()
        with Image.open(BytesIO(image_bytes)) as image:
            image = image.convert("RGB")
            image.thumbnail((1280, 1280))
            photo_buffer = BytesIO()
            image.save(photo_buffer, format="JPEG", quality=82, optimize=True)
    except (
        binascii.Error,
        Image.DecompressionBombError,
        UnidentifiedImageError,
        OSError,
        ValueError,
    ):
        flash("No se pudo procesar la foto. Vuelve a tomarla e inténtalo de nuevo.", "danger")
        return redirect(url_for("index"))

    photo_id = uuid.uuid4().hex
    photo_path = _photo_path(photo_id)
    try:
        photo_path.parent.mkdir(parents=True, exist_ok=True)
        photo_path.write_bytes(photo_buffer.getvalue())
    except OSError:
        app.logger.exception("No se pudo guardar la foto capturada.")
        flash("No se pudo guardar la foto. Inténtalo de nuevo.", "danger")
        return redirect(url_for("index"))

    photo_item = f"{PHOTO_PREFIX}{photo_id}"
    if not push(stack, photo_item, capacity):
        _delete_photo(photo_item)
        flash("La pila está llena. Desapila un elemento antes de agregar una foto.", "warning")
        return redirect(url_for("index"))

    session["stack"] = stack
    flash("La foto se agregó a la pila.", "success")
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
        photo_deleted = _delete_photo(item)
        if item.startswith(PHOTO_PREFIX):
            flash("Se desapiló la foto.", "success")
            if not photo_deleted:
                flash("No se pudo borrar el archivo de foto del servidor.", "warning")
        else:
            flash(f"Se desapiló «{item}».", "success")
    return redirect(url_for("index"))


@app.post("/consultar-tope")
def show_top():
    state = _require_stack()
    if state is None:
        return redirect(url_for("index"))

    stack, _ = state
    if stack:
        if stack[-1].startswith(PHOTO_PREFIX):
            flash("El elemento en el tope es una foto.", "info")
        else:
            flash(f"El elemento en el tope es «{stack[-1]}».", "info")
    else:
        flash("La pila está vacía; todavía no tiene un elemento en el tope.", "warning")
    return redirect(url_for("index"))


@app.post("/vaciar")
def clear_stack():
    state = _require_stack()
    if state is None:
        return redirect(url_for("index"))

    stack, capacity = state
    photos_deleted = True
    for item in stack:
        if not _delete_photo(item):
            photos_deleted = False
    session["stack"] = []
    session["capacity"] = capacity
    flash("La pila se vació.", "success")
    if not photos_deleted:
        flash("No se pudieron borrar todas las fotos del servidor.", "warning")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
