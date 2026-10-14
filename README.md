# Aplicación web de pila

Interfaz en español para practicar una pila LIFO (último en entrar, primero en salir). La aplicación usa Flask, Bootstrap 5.3.3 y JavaScript; no incluye CSS personalizado. Bootstrap se sirve localmente desde `static/vendor/bootstrap/` para que la interfaz no dependa de la disponibilidad de un CDN. Cada navegador mantiene su propia pila en una cookie de sesión firmada. La capacidad máxima es de 20 elementos y cada valor admite hasta 100 caracteres.

## Ejecutar en Windows

Desde la carpeta del proyecto, en PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:FLASK_SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
python -m flask --app app run --debug
```

Abre `http://127.0.0.1:5000` en el navegador. Para tomar y agregar una foto, crea la pila, pulsa **Activar cámara**, concede permiso al navegador y después pulsa **Tomar foto** y **Agregar foto a la pila**. La cámara requiere permiso y un contexto seguro: `localhost`/`127.0.0.1` para pruebas locales o HTTPS al publicar la aplicación. Las fotos se guardan en `instance/photos/`, no en la cookie de sesión, y se sirven únicamente si pertenecen a la pila de esa sesión. Se eliminan al desapilar la foto, vaciar la pila o reiniciarla. La clave aleatoria se puede omitir para una demostración local; si no se define, las sesiones se invalidan al reiniciar el servidor. Para producción, configura una clave secreta estable y administra la pila en almacenamiento del servidor.

## Probar

```powershell
python -m unittest -v test_app.py
```

La aplicación permite crear o reiniciar la pila, apilar valores o fotos, consultar el tope, desapilarlo y vaciar la pila. También valida la capacidad y los valores en el servidor, limita las fotos JPEG a 2 MB antes del procesamiento, y protege los formularios con tokens CSRF.
