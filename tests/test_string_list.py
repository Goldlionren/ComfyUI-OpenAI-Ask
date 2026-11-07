import unittest

from node_string_list import JRStringToList


class DynamicStringListTests(unittest.TestCase):
    def test_input_schema_supports_arbitrary_named_ports(self):
        inputs = JRStringToList.INPUT_TYPES()["optional"]
        self.assertEqual(list(inputs), ["text_1"])
        self.assertEqual(inputs["text_1"], ("STRING", {"forceInput": True}))
        self.assertEqual(inputs["text_99"], ("STRING", {"forceInput": True}))
        self.assertNotIn("other", inputs)
        self.assertNotIn("text_0", inputs)

    def test_comfy_list_flags(self):
        self.assertTrue(JRStringToList.INPUT_IS_LIST)
        self.assertEqual(JRStringToList.OUTPUT_IS_LIST, (True,))

    def test_numeric_port_order_and_preserve_strings(self):
        result = JRStringToList().combine(text_10=["ten"], text_2=["two"], text_1=[" one "])
        self.assertEqual(result, ([" one ", "two", "ten"],))

    def test_flatten_upstream_lists_in_port_order(self):
        result = JRStringToList().combine(text_1=["a", "b"], text_2=["c"])
        self.assertEqual(result, (["a", "b", "c"],))

    def test_empty_inputs_and_empty_strings(self):
        self.assertEqual(JRStringToList().combine(), ([],))
        self.assertEqual(JRStringToList().combine(text_1=[""]), ([""],))

    def test_reject_non_string_values(self):
        with self.assertRaises(TypeError):
            JRStringToList().combine(text_1=[123])


if __name__ == "__main__":
    unittest.main()
