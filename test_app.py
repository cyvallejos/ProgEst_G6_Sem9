import base64
from io import BytesIO
from pathlib import Path
import unittest

from PIL import Image

from app import app


class StackWebAppTests(unittest.TestCase):
    def setUp(self):
        app.config.update(
            TESTING=True,
            SECRET_KEY="test-secret",
            WTF_CSRF_ENABLED=False,
        )
        self.client = app.test_client()

    def configure_stack(self, capacity: str = "2"):
        return self.client.post("/configurar", data={"capacity": capacity})

    @staticmethod
    def jpeg_data_url():
        image_buffer = BytesIO()
        Image.new("RGB", (32, 24), color="blue").save(image_buffer, format="JPEG")
        encoded = base64.b64encode(image_buffer.getvalue()).decode("ascii")
        return f"data:image/jpeg;base64,{encoded}"

    def test_configures_stack_and_adds_items_in_lifo_order(self):
        response = self.configure_stack()
        self.assertEqual(response.status_code, 302)

        self.client.post("/apilar", data={"item": "A"})
        self.client.post("/apilar", data={"item": "B"})
        response = self.client.post("/desapilar", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Se desapiló «B».", response.get_data(as_text=True))
        self.assertIn("A", response.get_data(as_text=True))
        self.assertNotIn(">B<", response.get_data(as_text=True))

    def test_rejects_invalid_capacity_and_full_stack(self):
        response = self.client.post(
            "/configurar",
            data={"capacity": "0"},
            follow_redirects=True,
        )
        self.assertIn("La capacidad debe estar entre 1 y 20.", response.get_data(as_text=True))

        self.configure_stack("1")
        self.client.post("/apilar", data={"item": "A"})
        response = self.client.post("/apilar", data={"item": "B"}, follow_redirects=True)

        self.assertIn("La pila está llena.", response.get_data(as_text=True))

    def test_rejects_blank_item_and_handles_empty_stack(self):
        self.configure_stack()
        response = self.client.post("/apilar", data={"item": "  "}, follow_redirects=True)
        self.assertIn("Escribe un valor", response.get_data(as_text=True))

        response = self.client.post("/desapilar", follow_redirects=True)
        self.assertIn("La pila está vacía", response.get_data(as_text=True))

    def test_stack_is_isolated_per_browser_session(self):
        self.configure_stack()
        self.client.post("/apilar", data={"item": "Privado"})
        other_client = app.test_client()

        response = other_client.get("/")

        self.assertNotIn("Privado", response.get_data(as_text=True))
        self.assertIn("Configura una pila para empezar.", response.get_data(as_text=True))

    def test_requires_csrf_token_for_browser_forms(self):
        app.config["WTF_CSRF_ENABLED"] = True

        response = self.client.post("/configurar", data={"capacity": "2"})

        self.assertEqual(response.status_code, 400)

    def test_captured_photo_is_added_and_removed_with_stack_item(self):
        self.configure_stack()
        response = self.client.post(
            "/apilar-foto",
            data={"photo_data": self.jpeg_data_url()},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("La foto se agregó a la pila.", response.get_data(as_text=True))
        with self.client.session_transaction() as browser_session:
            photo_item = browser_session["stack"][-1]
        photo_id = photo_item.removeprefix("foto:")
        photo_path = Path(app.instance_path) / "photos" / f"{photo_id}.jpg"

        image_response = self.client.get(f"/fotos/{photo_id}")
        self.assertEqual(image_response.status_code, 200)
        self.assertEqual(image_response.mimetype, "image/jpeg")
        image_response.close()
        self.assertEqual(app.test_client().get(f"/fotos/{photo_id}").status_code, 404)

        self.client.post("/desapilar")
        self.assertEqual(self.client.get(f"/fotos/{photo_id}").status_code, 404)
        self.assertFalse(photo_path.exists())

    def test_rejects_invalid_photo_data_and_full_stack(self):
        self.configure_stack("1")
        response = self.client.post(
            "/apilar-foto",
            data={"photo_data": "not-a-photo"},
            follow_redirects=True,
        )
        self.assertIn("Captura una foto válida", response.get_data(as_text=True))

        self.client.post("/apilar", data={"item": "Completo"})
        response = self.client.post(
            "/apilar-foto",
            data={"photo_data": self.jpeg_data_url()},
            follow_redirects=True,
        )
        self.assertIn("La pila está llena", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
