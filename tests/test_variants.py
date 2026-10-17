import unittest

from cipher_variants import geffe_keystream, nlfsr_keystream


class NonlinearVariantTests(unittest.TestCase):
    def test_nlfsr_known_vector(self):
        self.assertEqual(nlfsr_keystream(8, 0xACE1), bytes.fromhex("87354ec1db72b33a"))

    def test_geffe_known_vector(self):
        self.assertEqual(
            geffe_keystream(8, (0xACE1, 0xBEEF, 0x1234)),
            bytes.fromhex("af7d76c4bb0a17b4"),
        )

    def test_variant_offsets_match_whole_stream(self):
        for generator in (
            lambda length, offset=0: nlfsr_keystream(length, 0xACE1, offset),
            lambda length, offset=0: geffe_keystream(
                length, (0xACE1, 0xBEEF, 0x1234), offset
            ),
        ):
            with self.subTest(generator=generator):
                whole = generator(96)
                self.assertEqual(generator(31, 27), whole[27:58])

    def test_variants_validate_inputs(self):
        with self.assertRaises(ValueError):
            nlfsr_keystream(1, 0)
        with self.assertRaises(ValueError):
            geffe_keystream(1, (1, 2))


if __name__ == "__main__":
    unittest.main()
