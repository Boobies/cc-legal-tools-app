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
            "## Attribution 4.0 International\n\n"
            "<u>Adapted Material</u> means material described in "
            "[Section 1](#s1).\n\n"
            "(a) First item\n"
            "\n"
            "(b) Second item\n"
            "\n"
            "&nbsp;&nbsp;&nbsp;&nbsp;(i) Nested item\n"
            "\n"
            "&nbsp;&nbsp;&nbsp;&nbsp;(ii) Second nested item\n"
        )

        self.assertEqual(expected, legal_code_html_to_markdown(html))

    def test_legal_code_html_to_markdown_uppercase_list_and_strong(self):
        html = """
        <div id="legal-code-body">
          <ol type="A">
            <li><strong>Notice</strong> must be retained.</li>
          </ol>
        </div>
        """

        self.assertEqual(
            "(A) **Notice** must be retained.\n",
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
            "1. First decimal item.\n2. Second decimal item.\n",
            legal_code_html_to_markdown(html),
        )

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
            "(a) Parent item\n\n"
            "&nbsp;&nbsp;&nbsp;&nbsp;1. Nested decimal item.\n"
            "\n"
            "&nbsp;&nbsp;&nbsp;&nbsp;2. Second nested decimal item.\n",
            legal_code_html_to_markdown(html),
        )
