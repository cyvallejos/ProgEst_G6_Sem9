from flask import Flask, jsonify, render_template, request

from cola import Queue, QueueEmptyError, QueueFullError

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # máximo 2 MB por petición

DEFAULT_CAPACITY = 5
PHOTO_PREFIX = "data:image/jpeg;base64,"
queue = Queue(DEFAULT_CAPACITY)


def describe(item: dict) -> str:
    """Texto corto para mostrar un elemento en los mensajes."""
    return f"«{item['value']}»" if item["type"] == "text" else "una foto"


def queue_response(message: str = "", category: str = "success", status: int = 200):
    """Devuelve el estado actual de la cola junto con un mensaje para el usuario."""
    payload = {
        "items": queue.to_list(),
        "capacity": queue.capacity,
        "size": len(queue),
        "message": message,
        "category": category,  # clase de alerta de Bootstrap
    }
    return jsonify(payload), status


@app.errorhandler(413)
def too_large(_error):
    return queue_response("La imagen es demasiado grande.", "danger", 413)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/queue")
def get_queue():
    return queue_response()


@app.post("/api/queue/config")
def configure():
    global queue
    data = request.get_json(silent=True) or {}
    try:
        queue = Queue(int(data.get("capacity")))
    except (TypeError, ValueError):
        return queue_response(
            "Capacidad inválida: escribe un número entero mayor a 0.", "danger", 400
        )
    return queue_response(f"Cola creada con capacidad {queue.capacity}.")


@app.post("/api/queue/enqueue")
def enqueue():
    data = request.get_json(silent=True) or {}
    value = str(data.get("item", "")).strip()
    if not value:
        return queue_response("Escribe un valor antes de encolar.", "warning", 400)
    try:
        queue.enqueue({"type": "text", "value": value})
    except QueueFullError as error:
        return queue_response(str(error), "warning", 409)
    return queue_response(f"«{value}» encolado correctamente.")


@app.post("/api/queue/enqueue-photo")
def enqueue_photo():
    data = request.get_json(silent=True) or {}
    image = data.get("image", "")
    if not isinstance(image, str) or not image.startswith(PHOTO_PREFIX):
        return queue_response("La imagen recibida no es válida.", "danger", 400)
    try:
        queue.enqueue({"type": "photo", "value": image})
    except QueueFullError as error:
        return queue_response(str(error), "warning", 409)
    return queue_response("Foto encolada correctamente.")


@app.post("/api/queue/dequeue")
def dequeue():
    try:
        item = queue.dequeue()
    except QueueEmptyError as error:
        return queue_response(str(error), "warning", 409)
    return queue_response(f"Desencolado: {describe(item)}.", "info")


@app.get("/api/queue/peek")
def peek():
    try:
        item = queue.peek()
    except QueueEmptyError as error:
        return queue_response(str(error), "warning", 409)
    return queue_response(f"El frente de la cola es {describe(item)}.", "info")


if __name__ == "__main__":
    app.run(debug=True)

