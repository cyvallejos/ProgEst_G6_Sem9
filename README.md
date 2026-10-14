# Aplicación web de pila

Interfaz en español para practicar estructuras de datos: los valores de texto van a una pila LIFO (último en entrar, primero en salir) y las fotos a una cola FIFO (primero en entrar, primero en salir). La aplicación usa Flask, Bootstrap 5.3.3 y JavaScript; no incluye CSS personalizado. Bootstrap se sirve localmente desde `static/vendor/bootstrap/` para que la interfaz no dependa de la disponibilidad de un CDN. Cada navegador mantiene su pila y su cola en una cookie de sesión firmada. El límite de la pila y de la cola es de 20 elementos; cada valor de texto admite hasta 100 caracteres.

## Ejecutar en Windows

Desde la carpeta del proyecto, en PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:FLASK_SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
python -m flask --app app run --debug
```

Abre `http://127.0.0.1:5000` en el navegador. Para tomar y agregar una foto, crea la pila, pulsa **Activar cámara**, concede permiso al navegador y después pulsa **Tomar foto** y **Agregar foto a la cola**. Las fotos se muestran desde la más antigua hasta la más reciente y se retiran del frente en orden FIFO. La cámara requiere permiso y un contexto seguro: `localhost`/`127.0.0.1` para pruebas locales o HTTPS al publicar la aplicación. Las fotos se guardan en `instance/photos/`, no en la cookie de sesión, y se sirven únicamente si pertenecen a la cola de esa sesión. Se eliminan al retirar la foto del frente, vaciar la cola o reiniciar las estructuras. La clave aleatoria se puede omitir para una demostración local; si no se define, las sesiones se invalidan al reiniciar el servidor. Para producción, configura una clave secreta estable y administra la pila en almacenamiento del servidor.

## Probar

```powershell
python -m unittest -v test_app.py
```

La aplicación permite crear o reiniciar las estructuras, apilar y desapilar valores de texto, y encolar fotos, consultar el frente, desencolar la foto más antigua y vaciar la cola. Ambas estructuras tienen la capacidad configurada para la sesión. También valida la capacidad y los valores en el servidor, limita las fotos JPEG a 2 MB antes del procesamiento, y protege los formularios con tokens CSRF.
