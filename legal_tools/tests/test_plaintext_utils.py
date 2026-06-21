# Third-party
from django.test import SimpleTestCase

# First-party/Local
from legal_tools.plaintext_utils import (
    PLAIN_TEXT_SEPARATOR,
    legal_code_html_to_plain_text,
)


class PlainTextUtilsTest(SimpleTestCase):
    def test_legal_code_html_to_plain_text_document_regions(self):
        html = """
        <div id="legal-code-document">
          <h1>Document Title</h1>
          <div class="notice-top">
            <h2>About</h2>
            <p>Preface text.</p>
          </div>
          <div class="notice-top">
            <h2>Using</h2>
            <p>More preface text.</p>
            <hr class="divider">
            <h3>Internal</h3>
            <p>Internal notice text.</p>
          </div>
          <div id="legal-code-body">
            <h2>Body Title</h2>
            <p>Body text.</p>
          </div>
          <div class="notice-bottom">
            <h2>Footer</h2>
            <p>Footer text.</p>
          </div>
        </div>
        """

        self.assertEqual(
            "Document Title\n\n"
            f"{PLAIN_TEXT_SEPARATOR}\n\n"
            "About\n\n"
            "Preface text.\n\n"
            "Using\n\n"
            "More preface text.\n\n"
            "Internal\n\n"
            "Internal notice text.\n\n"
            f"{PLAIN_TEXT_SEPARATOR}\n\n"
            "Body Title\n\n"
            "Body text.\n\n"
            f"{PLAIN_TEXT_SEPARATOR}\n\n"
            "Footer\n\n"
            "Footer text.\n",
            legal_code_html_to_plain_text(html),
        )

    def test_legal_code_html_to_plain_text_wraps_paragraphs(self):
        text = (
            "Alpha beta gamma delta epsilon zeta eta theta iota kappa lambda "
            "mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega."
        )
        html = f"""
        <div id="legal-code-body">
          <p>{text}</p>
        </div>
        """

        plain_text = legal_code_html_to_plain_text(html)
        lines = plain_text.splitlines()

        self.assertGreater(len(lines), 1)
        self.assertEqual(text, " ".join(lines))
        self.assertTrue(all(len(line) <= 71 for line in lines))

    def test_legal_code_html_to_plain_text_ordered_list_markers(self):
        html = """
        <div id="legal-code-body">
          <ol>
            <li>World</li>
          </ol>
          <ol type="a" start="2">
            <li>Lower alpha</li>
          </ol>
          <ol type="A" start="3">
            <li>Upper alpha</li>
          </ol>
          <ol type="i" start="3">
            <li>Lower roman</li>
          </ol>
          <ol type="I" start="2">
            <li>Upper roman</li>
          </ol>
          <ol reversed start="3">
            <li>Three</li>
            <li>Two</li>
          </ol>
        </div>
        """

        self.assertEqual(
            "  1. World\n\n"
            "  b. Lower alpha\n\n"
            "  C. Upper alpha\n\n"
            "iii. Lower roman\n\n"
            " II. Upper roman\n\n"
            "  3. Three\n\n"
            "  2. Two\n",
            legal_code_html_to_plain_text(html),
        )

    def test_legal_code_html_to_plain_text_nested_list_indentation(self):
        html = """
        <div id="legal-code-body">
          <ol>
            <li>
              Parent item
              <ol type="i">
                <li>Nested item</li>
              </ol>
            </li>
          </ol>
        </div>
        """

        self.assertEqual(
            "  1. Parent item\n"
            "       i. Nested item\n",
            legal_code_html_to_plain_text(html),
        )

    def test_legal_code_html_to_plain_text_unordered_list(self):
        html = """
        <div id="legal-code-body">
          <ul>
            <li>Bullet item</li>
          </ul>
        </div>
        """

        self.assertEqual(
            "  -. Bullet item\n",
            legal_code_html_to_plain_text(html),
        )

    def test_legal_code_html_to_plain_text_long_marker(self):
        html = """
        <div id="legal-code-body">
          <ol type="i" start="8">
            <li>
              Alpha beta gamma delta epsilon zeta eta theta iota kappa lambda
              mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega.
            </li>
          </ol>
        </div>
        """

        self.assertEqual(
            "viii. Alpha beta gamma delta epsilon zeta eta theta iota kappa "
            "lambda\n"
            "      mu nu xi omicron pi rho sigma tau upsilon phi chi psi "
            "omega.\n",
            legal_code_html_to_plain_text(html),
        )

    def test_legal_code_html_to_plain_text_links(self):
        html = """
        <div id="legal-code-body">
          <p>
            See <a href="#s1">Section 1</a> and
            <a href="https://example.test/">example</a>.
          </p>
        </div>
        """

        self.assertEqual(
            "See Section 1 and example: https://example.test/.\n",
            legal_code_html_to_plain_text(html),
        )

    def test_legal_code_html_to_plain_text_sentence_link(self):
        html = """
        <div id="legal-code-body">
          <p>
            Read <a href="https://example.test/">the full document.</a>
          </p>
        </div>
        """

        self.assertEqual(
            "Read the full document. https://example.test/\n",
            legal_code_html_to_plain_text(html),
        )
