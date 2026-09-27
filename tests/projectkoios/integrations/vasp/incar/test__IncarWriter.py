from __future__ import annotations

import unittest

from projectkoios.integrations.vasp.incar import (
    IncarAssignment,
    IncarFile,
    IncarParser,
    IncarWriter,
)


class IncarWriterTest(unittest.TestCase):
    def test_render_uses_direct_tag_syntax_and_is_parser_stable(self) -> None:
        input_file = IncarFile(
            assignments=(
                IncarAssignment(tag="ENCUT", value="400"),
                IncarAssignment(tag="EDIFF", value="1e-6"),
                IncarAssignment(tag="PLUGINS/STRUCTURE", value="T"),
            )
        )

        rendered = IncarWriter().render(input_file)

        self.assertEqual(
            rendered,
            "ENCUT = 400\nEDIFF = 1e-6\nPLUGINS/STRUCTURE = T\n",
        )
        self.assertEqual(IncarParser().parse(rendered), input_file)

    def test_render_empty_input_as_empty_text(self) -> None:
        self.assertEqual(IncarWriter().render(IncarFile(assignments=())), "")


if __name__ == "__main__":
    unittest.main()
