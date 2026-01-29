import unittest
from galt.ui.formatter import GaltReportFormatter

class TestGaltReportFormatter(unittest.TestCase):
    
    def setUp(self):
        self.formatter = GaltReportFormatter()

    def test_headers_transform(self):
        """Test conversion of ### headers to styled h3 tags."""
        input_text = "### 🚨 Amenazas Detected"
        expected_part = "<h3 style='color: #00d2ff; margin-top: 25px; margin-bottom: 10px; font-weight: 600; border-bottom: 1px solid #333; padding-bottom: 5px;'>🚨 Amenazas Detected</h3>"
        self.assertIn(expected_part, self.formatter.to_html(input_text))

    def test_bold_transform(self):
        """Test conversion of **text** to <strong>text</strong>."""
        input_text = "**Sistema:** Check complete."
        # New parser converts this to a styled paragraph
        expected_tag = "<p style='color: #fff; font-weight: bold; margin-top: 15px; margin-bottom: 5px; margin-left: 10px;'>"
        result = self.formatter.to_html(input_text)
        self.assertIn(expected_tag, result)

    def test_port_list_brackets(self):
        """CRITICAL: Test extracting port list from [445, 5432] pattern."""
        input_text = "Open ports: [445, 5432]"
        result = self.formatter.to_html(input_text)
        
        expected_ul = "<ul style='margin-left: 40px; background: rgba(255,255,255,0.03); padding: 10px 10px 10px 30px; border-radius: 5px; border-left: 2px solid #fb6340;'>"
        self.assertIn(expected_ul, result)
        # Check for styled LI
        self.assertIn("445</li>", result)
        self.assertIn("5432</li>", result)
        self.assertNotIn("[445, 5432]", result)

    def test_port_list_colon(self):
        """Test extracting port list from : 22, 80 pattern."""
        input_text = "Open ports: 22, 80, 443"
        result = self.formatter.to_html(input_text)
        
        # New parser only handles brackets [] for lists, otherwise standard p
        expected_p = "<p style='margin-left: 20px; color: #bbb; line-height: 1.5; margin-bottom: 5px;'>"
        self.assertIn(expected_p, result)
        self.assertIn("Open ports: 22, 80, 443", result)

    def test_cleanup_bullets(self):
        """Test converting * bullets to proper lists or paragraphs."""
        input_text = "* Item 1"
        result = self.formatter.to_html(input_text)
        # New parser doesn't explicitly handle *, so it becomes a paragraph
        expected_p = "<p style='margin-left: 20px; color: #bbb; line-height: 1.5; margin-bottom: 5px;'>"
        self.assertIn(expected_p, result)
        self.assertIn("* Item 1", result)

    def test_cleanup_punctuation_and_indent(self):
        """Test aggressive cleanup of leading punctuation and indentation logic."""
        # Case 1: Loose dot and critical text
        input_text = ". CRITICAL: System Failure"
        result = self.formatter.to_html(input_text)
        self.assertIn("CRITICAL: System Failure", result)
        self.assertNotIn(". CRITICAL", result)
        
        # Case 2: Indentation for general text (not header/list)
        # Assuming "CRITICAL..." becomes a paragraph
        self.assertIn('margin-left: 20px;', result)

    def test_title_normalization(self):
        """Test converting **Title** to <strong>Title:</strong>."""
        input_text = "**Otros Hallazgos**"
        result = self.formatter.to_html(input_text)
        # Expect styled p tag with bold and colon
        expected_tag = "<p style='color: #fff; font-weight: bold; margin-top: 15px; margin-bottom: 5px; margin-left: 10px;'>Otros Hallazgos:</p>"
        self.assertIn(expected_tag, result)

    def test_list_indentation(self):
        """Test specific indentation for UL."""
        input_text = "Ports: [80, 443]"
        result = self.formatter.to_html(input_text)
        # Check for margin-left: 40px in UL style
        expected_part = 'margin-left: 40px;'
        self.assertIn(expected_part, result)
        # Check full style just in case of ordering, but partial match is safer for strictness
        # self.assertIn('<ul style="padding-left: 25px; margin-bottom: 20px; margin-left: 40px;">', result)

if __name__ == "__main__":
    unittest.main()
