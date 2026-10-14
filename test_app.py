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

    def test_captured_photo_is_added_to_queue_and_removed_from_front(self):
        self.configure_stack()
        response = self.client.post(
            "/apilar-foto",
            data={"photo_data": self.jpeg_data_url()},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("La foto se encoló al final de la cola de imágenes.", response.get_data(as_text=True))
        with self.client.session_transaction() as browser_session:
            self.assertEqual(browser_session["stack"], [])
            self.assertEqual(len(browser_session["image_queue"]), 1)
            photo_item = browser_session["image_queue"][0]
        photo_id = photo_item.removeprefix("foto:")
        photo_path = Path(app.instance_path) / "photos" / f"{photo_id}.jpg"

        image_response = self.client.get(f"/fotos/{photo_id}")
        self.assertEqual(image_response.status_code, 200)
        self.assertEqual(image_response.mimetype, "image/jpeg")
        image_response.close()
        self.assertEqual(app.test_client().get(f"/fotos/{photo_id}").status_code, 404)

        self.client.post("/desencolar-foto")
        self.assertEqual(self.client.get(f"/fotos/{photo_id}").status_code, 404)
        self.assertFalse(photo_path.exists())

    def test_photos_are_removed_from_queue_in_fifo_order(self):
        self.configure_stack()
        for _ in range(2):
            self.client.post("/apilar-foto", data={"photo_data": self.jpeg_data_url()})
        with self.client.session_transaction() as browser_session:
            first_photo_id = browser_session["image_queue"][0].removeprefix("foto:")
            second_photo_id = browser_session["image_queue"][1].removeprefix("foto:")
        first_photo_path = Path(app.instance_path) / "photos" / f"{first_photo_id}.jpg"
        second_photo_path = Path(app.instance_path) / "photos" / f"{second_photo_id}.jpg"

        response = self.client.post("/desencolar-foto", follow_redirects=True)

        self.assertIn("Se retiró la foto del frente de la cola.", response.get_data(as_text=True))
        with self.client.session_transaction() as browser_session:
            self.assertEqual(
                browser_session["image_queue"],
                [f"foto:{second_photo_id}"],
            )
        self.assertFalse(first_photo_path.exists())
        self.assertTrue(second_photo_path.exists())
        self.client.post("/vaciar-cola-fotos")
        self.assertFalse(second_photo_path.exists())

    def test_rejects_invalid_photo_data_and_full_image_queue(self):
        self.configure_stack("1")
        response = self.client.post(
            "/apilar-foto",
            data={"photo_data": "not-a-photo"},
            follow_redirects=True,
        )
        self.assertIn("Captura una foto válida", response.get_data(as_text=True))

        self.client.post("/apilar", data={"item": "Texto en pila"})
        with self.client.session_transaction() as browser_session:
            browser_session["image_queue"] = ["foto:11111111111111111111111111111111"]
        response = self.client.post(
            "/apilar-foto",
            data={"photo_data": self.jpeg_data_url()},
            follow_redirects=True,
        )
        self.assertIn("La cola de imágenes está llena", response.get_data(as_text=True))
        with self.client.session_transaction() as browser_session:
            self.assertEqual(browser_session["stack"], ["Texto en pila"])


if __name__ == "__main__":
    unittest.main()
