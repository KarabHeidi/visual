import unittest
from typing import Optional
from .validate_docx import get_jinja_errors
from pathlib import Path


class TestGetJinjaErrors(unittest.TestCase):
    def test_working_template(self):
        working_template = Path(__file__).parent / "test/made_up_variables.docx"
        result: Optional[str] = get_jinja_errors(working_template)
        self.assertIsNone(result)

    def test_failing_template(self):
        failing_template = Path(__file__).parent / "test/valid_word_invalid_jinja.docx"
        result: Optional[str] = get_jinja_errors(failing_template)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)


if __name__ == "__main__":
    unittest.main()
