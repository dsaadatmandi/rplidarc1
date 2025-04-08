"""
Tests for the utils module.
"""

import unittest
from rplidarc1.utils import ByteEnum


class TestByteEnum(unittest.TestCase):
    """
    Test cases for the ByteEnum class.
    """

    def setUp(self):
        """
        Set up test fixtures.
        """

        # Create a test enum class that inherits from ByteEnum
        class TestEnum(ByteEnum):
            TEST_VALUE = b"\x01"
            ANOTHER_VALUE = b"\x02"

        self.TestEnum = TestEnum
        self.test_value = TestEnum.TEST_VALUE
        self.another_value = TestEnum.ANOTHER_VALUE

    def test_bytes_conversion(self):
        """
        Test that ByteEnum values can be converted to bytes.
        """
        self.assertEqual(bytes(self.test_value), b"\x01")
        self.assertEqual(bytes(self.another_value), b"\x02")

    def test_addition_with_byteenum(self):
        """
        Test that ByteEnum values can be added to other ByteEnum values.
        """
        result = self.test_value + self.another_value
        self.assertEqual(result, b"\x01\x02")

    def test_addition_with_bytes(self):
        """
        Test that ByteEnum values can be added to bytes objects.
        """
        result = self.test_value + b"\x03"
        self.assertEqual(result, b"\x01\x03")

    def test_right_addition_with_bytes(self):
        """
        Test that bytes objects can be added to ByteEnum values.
        """
        result = b"\x03" + self.test_value
        self.assertEqual(result, b"\x03\x01")

    def test_equality_with_byteenum(self):
        """
        Test that ByteEnum values can be compared with other ByteEnum values.
        """
        self.assertEqual(self.test_value, self.TestEnum.TEST_VALUE)
        self.assertNotEqual(self.test_value, self.another_value)

    def test_equality_with_bytes(self):
        """
        Test that ByteEnum values can be compared with bytes objects.
        """
        self.assertEqual(self.test_value, b"\x01")
        self.assertNotEqual(self.test_value, b"\x02")

    def test_addition_with_invalid_type(self):
        """
        Test that adding an invalid type to a ByteEnum raises NotImplemented.
        """
        with self.assertRaises(TypeError):
            self.test_value + 1

    def test_right_addition_with_invalid_type(self):
        """
        Test that adding a ByteEnum to an invalid type raises NotImplemented.
        """
        with self.assertRaises(TypeError):
            1 + self.test_value


if __name__ == "__main__":
    unittest.main()
