"""Tests for the markdown parser."""
from briefkit.extractor import parse_markdown


class TestHeadings:
    def test_h1(self):
        blocks = parse_markdown("# Hello World")
        assert len(blocks) == 1
        assert blocks[0]["type"] == "heading"
        assert blocks[0]["level"] == 1
        assert blocks[0]["text"] == "Hello World"

    def test_h2_through_h6(self):
        md = "\n".join(f"{'#' * i} Heading {i}" for i in range(2, 7))
        blocks = parse_markdown(md)
        assert len(blocks) == 5
        for i, block in enumerate(blocks, start=2):
            assert block["level"] == i

    def test_heading_with_inline_formatting(self):
        blocks = parse_markdown("## **Bold** and *italic*")
        assert "<b>Bold</b>" in blocks[0]["text"]
        assert "<i>italic</i>" in blocks[0]["text"]


class TestParagraphs:
    def test_simple_paragraph(self):
        blocks = parse_markdown("This is a paragraph.")
        assert len(blocks) == 1
        assert blocks[0]["type"] == "paragraph"
        assert blocks[0]["text"] == "This is a paragraph."

    def test_multi_line_paragraph(self):
        blocks = parse_markdown("Line one\nLine two")
        assert len(blocks) == 1
        assert "Line one" in blocks[0]["text"]
        assert "Line two" in blocks[0]["text"]

    def test_paragraphs_separated_by_blank_line(self):
        blocks = parse_markdown("Para one.\n\nPara two.")
        assert len(blocks) == 2
        assert blocks[0]["type"] == "paragraph"
        assert blocks[1]["type"] == "paragraph"


class TestTables:
    def test_basic_table(self):
        md = "| A | B |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |"
        blocks = parse_markdown(md)
        assert len(blocks) == 1
        assert blocks[0]["type"] == "table"
        assert blocks[0]["headers"] == ["A", "B"]
        assert blocks[0]["rows"] == [["1", "2"], ["3", "4"]]

    def test_empty_table(self):
        md = "| A | B |\n|---|---|"
        blocks = parse_markdown(md)
        assert len(blocks) == 1
        assert blocks[0]["rows"] == []


class TestCodeBlocks:
    def test_fenced_code(self):
        md = "```python\nprint('hello')\n```"
        blocks = parse_markdown(md)
        assert len(blocks) == 1
        assert blocks[0]["type"] == "code"
        assert blocks[0]["lang"] == "python"
        assert blocks[0]["text"] == "print('hello')"

    def test_code_block_no_lang(self):
        md = "```\nsome code\n```"
        blocks = parse_markdown(md)
        assert blocks[0]["lang"] == ""


class TestLists:
    def test_unordered_list(self):
        md = "- Item 1\n- Item 2\n- Item 3"
        blocks = parse_markdown(md)
        assert len(blocks) == 3
        assert all(b["type"] == "list_item" for b in blocks)
        assert all(not b["ordered"] for b in blocks)

    def test_ordered_list(self):
        md = "1. First\n2. Second\n3. Third"
        blocks = parse_markdown(md)
        assert len(blocks) == 3
        assert all(b["ordered"] for b in blocks)
        assert blocks[0]["index"] == 1


class TestBlockquotes:
    def test_simple_blockquote(self):
        blocks = parse_markdown("> This is a quote.")
        assert len(blocks) == 1
        assert blocks[0]["type"] == "blockquote"
        assert "This is a quote." in blocks[0]["text"]

    def test_multi_line_blockquote(self):
        md = "> Line one\n> Line two"
        blocks = parse_markdown(md)
        assert len(blocks) == 1
        assert "Line one" in blocks[0]["text"]
        assert "Line two" in blocks[0]["text"]


class TestRules:
    def test_horizontal_rule_dashes(self):
        blocks = parse_markdown("---")
        assert len(blocks) == 1
        assert blocks[0]["type"] == "rule"

    def test_horizontal_rule_asterisks(self):
        blocks = parse_markdown("***")
        assert blocks[0]["type"] == "rule"


class TestInlineFormatting:
    def test_bold(self):
        blocks = parse_markdown("This is **bold** text.")
        assert "<b>bold</b>" in blocks[0]["text"]

    def test_italic(self):
        blocks = parse_markdown("This is *italic* text.")
        assert "<i>italic</i>" in blocks[0]["text"]

    def test_inline_code(self):
        blocks = parse_markdown("Use `print()` here.")
        assert '<font name="Courier">print()</font>' in blocks[0]["text"]

    def test_link_preserved_as_hot_link(self):
        # Markdown links are now preserved as ReportLab <link> tags so
        # the URL survives into the PDF and the click target is hot.
        blocks = parse_markdown("See [docs](https://example.com) here.")
        assert "docs" in blocks[0]["text"]
        assert "https://example.com" in blocks[0]["text"]
        assert "<link" in blocks[0]["text"]


class TestMixedContent:
    def test_heading_then_paragraph_then_table(self):
        md = "# Title\n\nSome text.\n\n| A | B |\n|---|---|\n| 1 | 2 |"
        blocks = parse_markdown(md)
        assert blocks[0]["type"] == "heading"
        assert blocks[1]["type"] == "paragraph"
        assert blocks[2]["type"] == "table"

    def test_empty_input(self):
        blocks = parse_markdown("")
        assert blocks == []
