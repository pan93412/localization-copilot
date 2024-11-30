import unittest

from structure import Translatable
from structure.translatable import Translation
from .gpt4o import _construct_input


class TestConstructInput(unittest.TestCase):
    def test_source_only(self):
        input_text = Translatable(source="Hello, world!")
        expected_output = "<source>Hello, world!</source>\n"

        self.assertEqual(_construct_input(input_text), expected_output)

    def test_source_and_target(self):
        input_text = Translatable(source="Hello, world!", context="A greeting")
        expected_output = '<source context="A greeting">Hello, world!</source>\n'

        self.assertEqual(_construct_input(input_text), expected_output)

    def test_source_and_single_references(self):
        input_text = Translatable(source="Hello, world!", references=[
            Translation(source="Hello, World!", translation="哈囉，世界！", fuzzy=False)
        ])
        expected_output = """
<source>Hello, world!</source>
<references>
\t<translation source="Hello, World!">哈囉，世界！</translation>
</references>
""".strip() + "\n"

        self.assertEqual(_construct_input(input_text), expected_output)

    def test_source_and_multiple_references(self):
        input_text = Translatable(source="Hello, world!", references=[
            Translation(source="Hello, World!", translation="哈囉，世界！", fuzzy=False),
            Translation(source="Hi, World!", translation="你好，世界！", fuzzy=False)
        ])
        expected_output = """
<source>Hello, world!</source>
<references>
\t<translation source="Hello, World!">哈囉，世界！</translation>
\t<translation source="Hi, World!">你好，世界！</translation>
</references>
""".strip() + "\n"

        self.assertEqual(_construct_input(input_text), expected_output)

    def test_source_and_single_fuzzy_reference(self):
        input_text = Translatable(source="Hello, world!", references=[
            Translation(source="Hello, World!", translation="哈囉，世界！", fuzzy=True)
        ])
        expected_output = """
<source>Hello, world!</source>
<references>
\t<translation source="Hello, World!" fuzzy>哈囉，世界！</translation>
</references>
""".strip() + "\n"

        self.assertEqual(_construct_input(input_text), expected_output)

    def test_source_and_multiple_references_with_fuzzy(self):
        input_text = Translatable(source="Hello, world!", references=[
            Translation(source="Hello, World!", translation="哈囉，世界！", fuzzy=True),
            Translation(source="Hi, World!", translation="你好，世界！", fuzzy=False)
        ])
        expected_output = """
<source>Hello, world!</source>
<references>
\t<translation source="Hello, World!" fuzzy>哈囉，世界！</translation>
\t<translation source="Hi, World!">你好，世界！</translation>
</references>
""".strip() + "\n"

        self.assertEqual(_construct_input(input_text), expected_output)


    def test_source_with_context_and_multiple_references_with_fuzzy(self):
        input_text = Translatable(source="Hello, world!", context="A greeting", references=[
            Translation(source="Hello, World!", translation="哈囉，世界！", fuzzy=True),
            Translation(source="Hi, World!", translation="你好，世界！", fuzzy=False)
        ])
        expected_output = """
<source context="A greeting">Hello, world!</source>
<references>
\t<translation source="Hello, World!" fuzzy>哈囉，世界！</translation>
\t<translation source="Hi, World!">你好，世界！</translation>
</references>
""".strip() + "\n"

        self.assertEqual(_construct_input(input_text), expected_output)


    def test_source_with_reference_with_context(self):
        input_text = Translatable(source="Hello, world!", references=[
            Translation(source="Hello, World!", context="A greeting", translation="哈囉，世界！", fuzzy=True),
        ])
        expected_output = """
<source>Hello, world!</source>
<references>
\t<translation source="Hello, World!" context="A greeting" fuzzy>哈囉，世界！</translation>
</references>
""".strip() + "\n"

        self.assertEqual(_construct_input(input_text), expected_output)

