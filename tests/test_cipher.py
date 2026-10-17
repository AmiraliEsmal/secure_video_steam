import unittest

from stream_cipher import keystream, xor_bytes


class CipherTests(unittest.TestCase):
    def test_known_vector(self):
        self.assertEqual(keystream(4, 0xACE1), bytes.fromhex("873544e2"))

    def test_xor_is_its_own_inverse(self):
        plaintext = b"stream ciphers operate one byte at a time"
        ciphertext = xor_bytes(plaintext, 0xACE1)
        self.assertNotEqual(ciphertext, plaintext)
        self.assertEqual(xor_bytes(ciphertext, 0xACE1), plaintext)

    def test_chunk_offsets_match_whole_message(self):
        plaintext = bytes(range(256)) * 3
        whole = xor_bytes(plaintext, 0xBEEF)
        chunks = b"".join(
            xor_bytes(plaintext[start : start + 97], 0xBEEF, start)
            for start in range(0, len(plaintext), 97)
        )
        self.assertEqual(chunks, whole)

    def test_keystream_repeats_after_maximal_lfsr_period(self):
        self.assertEqual(keystream(32, 0xACE1), keystream(32, 0xACE1, 65535))

    def test_rejects_invalid_seed_and_offset(self):
        for seed in (0, -1, 65536):
            with self.subTest(seed=seed), self.assertRaises(ValueError):
                keystream(1, seed)
        with self.assertRaises(ValueError):
            xor_bytes(b"data", 1, -1)


if __name__ == "__main__":
    unittest.main()
