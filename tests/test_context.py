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

    def test_succession_caption_extracts_party_without_confirming_case_shape(self):
        event = Event(
            application="Lex Doctor",
            title="Procesos ~ Boasso, Gloria Beatriz S/ Sucesión ab intestato",
        )

        enrich(event)

        self.assertEqual(event.client, "Boasso, Gloria Beatriz")
        self.assertEqual(
            event.case,
            "Boasso, Gloria Beatriz S/ Sucesión ab intestato",
        )


if __name__ == "__main__":
    unittest.main()
