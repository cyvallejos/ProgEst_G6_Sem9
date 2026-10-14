import unittest

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


if __name__ == "__main__":
    unittest.main()
