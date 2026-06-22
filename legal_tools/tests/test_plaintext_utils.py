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
          <div id="notice-about-licenses-and-cc" class="notice-top">
            <h2>About</h2>
            <p>Preface text.</p>
          </div>
          <div id="about-cc-and-license" class="notice-top">
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
          <div id="notice-about-cc-and-trademark" class="notice-bottom">
            <h2>Footer</h2>
            <p>Footer text.</p>
          </div>
        </div>
        """

        self.assertEqual(
            "Document Title\n\n"
            f"{PLAIN_TEXT_SEPARATOR}\n\n"
            "Preface text.\n\n"
            "Using\n\n"
            "More preface text.\n\n"
            "     Internal: Internal notice text.\n\n"
            f"{PLAIN_TEXT_SEPARATOR}\n\n"
            "Body Title\n\n"
            "Body text.\n\n"
            f"{PLAIN_TEXT_SEPARATOR}\n\n"
            "Footer text.\n",
            legal_code_html_to_plain_text(html),
        )

    def test_legal_code_html_to_plain_text_legal_section_spacing(self):
        html = """
        <div id="legal-code-document">
          <h1>Document Title</h1>
          <div id="legal-code-body">
            <h2 id="legal-code-title">Body Title</h2>
            <p>Intro text.</p>
            <h3 id="s1">Section 1 – Definitions.</h3>
            <p>First section text.</p>
            <h3 id="s2">Section 2 – Scope.</h3>
            <p>Second section text.</p>
          </div>
          <div id="notice-about-cc-and-trademark" class="notice-bottom">
            <h2>Footer</h2>
            <p>Footer text.</p>
          </div>
        </div>
        """

        self.assertEqual(
            "Document Title\n\n"
            f"{PLAIN_TEXT_SEPARATOR}\n\n"
            "Body Title\n\n"
            "Intro text.\n\n"
            "Section 1 -- Definitions.\n\n"
            "First section text.\n\n\n"
            "Section 2 -- Scope.\n\n"
            "Second section text.\n\n\n"
            f"{PLAIN_TEXT_SEPARATOR}\n\n"
            "Footer text.\n",
            legal_code_html_to_plain_text(html),
        )

    def test_legal_code_html_to_plain_text_non_section_heading_spacing(self):
        html = """
        <div id="legal-code-body">
          <h3 id="topic">Topic</h3>
          <p>Topic text.</p>
          <h3>Another Topic</h3>
          <p>Another text.</p>
        </div>
        """

        self.assertEqual(
            "Topic\n\n"
            "Topic text.\n\n"
            "Another Topic\n\n"
            "Another text.\n",
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

    def test_legal_code_html_to_plain_text_notice_asides(self):
        html = """
        <div id="about-cc-and-license" class="notice-top">
          <h2>Using</h2>
          <p>Intro text.</p>
          <hr class="divider">
          <h3>Licensors</h3>
          <p>
            Alpha beta gamma delta epsilon zeta eta theta iota kappa lambda
            mu nu.
          </p>
          <hr class="divider">
          <h3>Public</h3>
          <p>Gamma delta.</p>
        </div>
        """

        plain_text = legal_code_html_to_plain_text(html)

        self.assertEqual(
            "Using\n\n"
            "Intro text.\n\n"
            "     Licensors: Alpha beta gamma delta epsilon zeta eta theta iota\n"
            "     kappa lambda mu nu.\n\n"
            "     Public: Gamma delta.\n",
            plain_text,
        )
        aside_lines = [
            line
            for line in plain_text.splitlines()
            if line.startswith("     ")
        ]
        self.assertTrue(aside_lines)
        self.assertTrue(all(len(line) <= 66 for line in aside_lines))
        self.assertTrue(all(line == line.rstrip() for line in aside_lines))

    def test_legal_code_html_to_plain_text_notice_divider_fallback(self):
        html = """
        <div id="about-cc-and-license" class="notice-top">
          <h2>Using</h2>
          <hr class="divider">
          <p>Fallback text.</p>
        </div>
        """

        self.assertEqual(
            "Using\n\n"
            "Fallback text.\n",
            legal_code_html_to_plain_text(html),
        )

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
            "  1. Parent item\n\n"
            "       i. Nested item\n",
            legal_code_html_to_plain_text(html),
        )

    def test_legal_code_html_to_plain_text_list_item_block_spacing(self):
        html = """
        <div id="legal-code-body">
          <ol>
            <li>
              Intro
              <ol>
                <li>Nested item</li>
              </ol>
              Tail
            </li>
          </ol>
        </div>
        """

        self.assertEqual(
            "  1. Intro\n\n"
            "       1. Nested item\n\n"
            "     Tail\n",
            legal_code_html_to_plain_text(html),
        )

    def test_legal_code_html_to_plain_text_list_item_paragraph_spacing(self):
        html = """
        <div id="legal-code-body">
          <ol type="a" start="2">
            <li>
              <strong>ShareAlike</strong>.
              <p>In addition, the following conditions also apply.</p>
              <ol>
                <li>Nested condition</li>
              </ol>
            </li>
          </ol>
        </div>
        """

        self.assertEqual(
            "  b. ShareAlike.\n\n"
            "     In addition, the following conditions also apply.\n\n"
            "       1. Nested condition\n",
            legal_code_html_to_plain_text(html),
        )

    def test_legal_code_html_to_plain_text_list_item_first_paragraph(self):
        html = """
        <div id="legal-code-body">
          <ol>
            <li>
              <p>Only paragraph.</p>
            </li>
          </ol>
        </div>
        """

        self.assertEqual(
            "  1. Only paragraph.\n",
            legal_code_html_to_plain_text(html),
        )

    def test_legal_code_html_to_plain_text_unordered_list(self):
        html = """
        <div id="legal-code-body">
          <ul>
            <li>First bullet item</li>
            <li>Second bullet item</li>
          </ul>
        </div>
        """

        self.assertEqual(
            "   - First bullet item\n\n"
            "   - Second bullet item\n",
            legal_code_html_to_plain_text(html),
        )

    def test_legal_code_html_to_plain_text_unordered_list_wrap(self):
        html = """
        <div id="legal-code-body">
          <ul>
            <li>
              Alpha beta gamma delta epsilon zeta eta theta iota kappa lambda
              mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega.
            </li>
          </ul>
        </div>
        """

        lines = legal_code_html_to_plain_text(html).splitlines()

        self.assertTrue(lines[0].startswith("   - "))
        self.assertTrue(all(line.startswith("     ") for line in lines[1:]))

    def test_legal_code_html_to_plain_text_replaces_en_dash(self):
        html = """
        <div id="legal-code-body">
          <h3>Section 1 – Definitions.</h3>
        </div>
        """

        self.assertEqual(
            "Section 1 -- Definitions.\n",
            legal_code_html_to_plain_text(html),
        )

    def test_legal_code_html_to_plain_text_replaces_curly_quotes(self):
        html = """
        <div id="legal-code-body">
          <p>The licensor’s “request” is reasonable.</p>
        </div>
        """

        self.assertEqual(
            'The licensor\'s "request" is reasonable.\n',
            legal_code_html_to_plain_text(html),
        )

    def test_legal_code_html_to_plain_text_does_not_wrap_after_en_dash(self):
        html = """
        <div id="legal-code-body">
          <p>
            xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            reason–for example.
          </p>
        </div>
        """

        self.assertEqual(
            "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n"
            "reason--for example.\n",
            legal_code_html_to_plain_text(html),
        )

    def test_legal_code_html_to_plain_text_wraps_after_hyphens(self):
        html = """
        <div id="legal-code-body">
          <p>
            Alpha Alpha Alpha Alpha Alpha Alpha Alpha Alpha Alpha Alpha x
            CC-licensed material.
          </p>
        </div>
        """

        self.assertIn(
            "CC-\nlicensed",
            legal_code_html_to_plain_text(html),
        )

    def test_legal_code_html_to_plain_text_bold_style_uppercase(self):
        html = """
        <div id="legal-code-body">
          <ol type="a">
            <li style="font-weight: bold;">
              <strong>Unless otherwise undertaken.</strong>
            </li>
          </ol>
        </div>
        """

        self.assertEqual(
            "  a. UNLESS OTHERWISE UNDERTAKEN.\n",
            legal_code_html_to_plain_text(html),
        )

    def test_legal_code_html_to_plain_text_strong_not_uppercase(self):
        html = """
        <div id="legal-code-body">
          <p><strong>Your</strong> has a corresponding meaning.</p>
        </div>
        """

        self.assertEqual(
            "Your has a corresponding meaning.\n",
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
