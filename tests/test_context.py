import unittest

from src.context.engine import enrich
from src.models.event import Event


class ContextTests(unittest.TestCase):

    def test_enrich_synchronizes_context_and_typed_fields(self):
        event = Event(
            application="Lex Doctor",
            title="Procesos - Cliente C/ Demandado",
        )

        enrich(event)

        self.assertEqual(event.context["section"], "Procesos")
        self.assertEqual(event.section, "Procesos")
        self.assertEqual(event.client, "Cliente")
        self.assertEqual(event.case, "Cliente C/ Demandado")


if __name__ == "__main__":
    unittest.main()
