# Third-party
from django.test import SimpleTestCase

# First-party/Local
from legal_tools.markdown_utils import legal_code_html_to_markdown


class MarkdownUtilsTest(SimpleTestCase):
    def test_legal_code_html_to_markdown(self):
        html = """
        <main>
          <div id="legal-code-body">
            <h2>Attribution 4.0 International</h2>
            <p>
              <span style="text-decoration: underline;">Adapted Material</span>
              means material described in <a href="#s1">Section 1</a>.
            </p>
            <ol type="a">
              <li>First item</li>
              <li>
                Second item
                <ol type="i">
                  <li>Nested item</li>
                  <li>Second nested item</li>
                </ol>
              </li>
            </ol>
          </div>
        </main>
        """
        expected = (
            "# Attribution 4.0 International\n\n"
            "<u>Adapted Material</u> means material described in "
            "[Section 1](#s1).\n\n"
            '<ol type="a">\n'
            "<li>First item</li>\n"
            "<li>\n"
            "Second item\n"
            '<ol type="i">\n'
            "<li>Nested item</li>\n"
            "<li>Second nested item</li>\n"
            "</ol>\n"
            "</li>\n"
            "</ol>\n"
        )

        self.assertEqual(expected, legal_code_html_to_markdown(html))

    def test_legal_code_html_to_markdown_heading_levels(self):
        html = """
        <div id="legal-code-body">
          <h1>Title</h1>
          <h2>Section</h2>
          <h3>Subsection</h3>
        </div>
        """

        self.assertEqual(
            "# Title\n\n# Section\n\n## Subsection\n",
            legal_code_html_to_markdown(html),
        )

    def test_legal_code_html_to_markdown_uppercase_list_and_emphasis(self):
        html = """
        <div id="legal-code-body">
          <ol type="A">
            <li>
              <strong>Notice</strong> and <em>care</em> must be retained.
            </li>
          </ol>
        </div>
        """

        self.assertEqual(
            '<ol type="A">\n'
            "<li><strong>Notice</strong> and <em>care</em> must be "
            "retained.</li>\n"
            "</ol>\n",
            legal_code_html_to_markdown(html),
        )

    def test_legal_code_html_to_markdown_decimal_list(self):
        html = """
        <div id="legal-code-body">
          <ol>
            <li>First decimal item.</li>
            <li>Second decimal item.</li>
          </ol>
        </div>
        """

        self.assertEqual(
            "<ol>\n"
            "<li>First decimal item.</li>\n"
            "<li>Second decimal item.</li>\n"
            "</ol>\n",
            legal_code_html_to_markdown(html),
        )

    def test_legal_code_html_to_markdown_wraps_paragraphs(self):
        text = (
            "Alpha beta gamma delta epsilon zeta eta theta iota kappa lambda "
            "mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega."
        )
        html = f"""
        <div id="legal-code-body">
          <p>{text}</p>
        </div>
        """

        markdown = legal_code_html_to_markdown(html)
        lines = markdown.splitlines()

        self.assertGreater(len(lines), 1)
        self.assertEqual(text, " ".join(lines))
        self.assertTrue(all(len(line) <= 80 for line in lines))

    def test_legal_code_html_to_markdown_wraps_direct_text_nodes(self):
        text = (
            "Alpha beta gamma delta epsilon zeta eta theta iota kappa lambda "
            "mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega."
        )
        html = f"""
        <div id="legal-code-body">
          <h2>Notice</h2>
          {text}
        </div>
        """

        markdown = legal_code_html_to_markdown(html)
        lines = markdown.splitlines()

        self.assertEqual("# Notice", lines[0])
        self.assertEqual(text, " ".join(lines[2:]))
        self.assertTrue(all(len(line) <= 80 for line in lines))

    def test_legal_code_html_to_markdown_wraps_markdown_emphasis(self):
        html = """
        <div id="legal-code-body">
          <p>
            Alpha <strong>strong emphasis</strong> and <em>emphasis
            text</em> continue through enough words to require wrapping in
            generated Markdown output.
          </p>
        </div>
        """

        markdown = legal_code_html_to_markdown(html)

        self.assertIn("**strong emphasis**", markdown)
        self.assertIn("*emphasis text*", markdown)
        self.assertTrue(all(len(line) <= 80 for line in markdown.splitlines()))

    def test_legal_code_html_to_markdown_wraps_html_list_items(self):
        text = (
            "Alpha beta gamma delta epsilon zeta eta theta iota kappa lambda "
            "mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega."
        )
        html = f"""
        <div id="legal-code-body">
          <ol type="a">
            <li>{text}</li>
          </ol>
        </div>
        """

        markdown = legal_code_html_to_markdown(html)
        lines = markdown.splitlines()

        self.assertEqual('<ol type="a">', lines[0])
        self.assertEqual("<li>", lines[1])
        self.assertEqual("</li>", lines[-2])
        self.assertEqual("</ol>", lines[-1])
        self.assertNotIn("", lines)
        self.assertEqual(text, " ".join(lines[2:-2]))
        self.assertTrue(all(len(line) <= 80 for line in lines))

    def test_legal_code_html_to_markdown_wraps_html_block_tags(self):
        text = (
            "Alpha beta gamma delta epsilon zeta eta theta iota kappa lambda "
            "mu nu xi omicron pi rho sigma tau."
        )
        html = f"""
        <div id="legal-code-body">
          <ol>
            <li><p>{text}</p></li>
          </ol>
        </div>
        """

        markdown = legal_code_html_to_markdown(html)
        lines = markdown.splitlines()

        self.assertIn("<p>", lines)
        self.assertIn("</p>", lines)
        self.assertTrue(all(len(line) <= 80 for line in lines))

    def test_legal_code_html_to_markdown_preserves_long_tokens(self):
        token = f"https://creativecommons.org/{'licensepath' * 9}"
        html = f"""
        <div id="legal-code-body">
          <p>{token}</p>
        </div>
        """

        markdown = legal_code_html_to_markdown(html)

        self.assertEqual(f"{token}\n", markdown)
        self.assertGreater(len(markdown.splitlines()[0]), 80)

    def test_legal_code_html_to_markdown_nested_decimal_list(self):
        html = """
        <div id="legal-code-body">
          <ol type="a">
            <li>
              Parent item
              <ol>
                <li>Nested decimal item.</li>
                <li>Second nested decimal item.</li>
              </ol>
            </li>
          </ol>
        </div>
        """

        self.assertEqual(
            '<ol type="a">\n'
            "<li>\n"
            "Parent item\n"
            "<ol>\n"
            "<li>Nested decimal item.</li>\n"
            "<li>Second nested decimal item.</li>\n"
            "</ol>\n"
            "</li>\n"
            "</ol>\n",
            legal_code_html_to_markdown(html),
        )
