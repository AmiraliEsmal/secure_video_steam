"""Compare the LFSR, NLFSR, and Geffe generators after students implement them."""

from __future__ import annotations

import argparse
import json
from time import perf_counter

from cipher_variants import DEFAULT_GEFFE_SEEDS, geffe_keystream, nlfsr_keystream
from stream_cipher import keystream
from tools.evaluate import nist_report_for_bytes

DEFAULT_TESTS = ("monobit", "frequency_within_block", "runs", "binary_matrix_rank")


def compare(byte_count: int, test_names: tuple[str, ...] = DEFAULT_TESTS) -> list[dict]:
    generators = {
        "lfsr": lambda: keystream(byte_count, 0xACE1),
        "nlfsr": lambda: nlfsr_keystream(byte_count, 0xACE1),
        "geffe": lambda: geffe_keystream(byte_count, DEFAULT_GEFFE_SEEDS),
    }
    reports = []
    for name, generate in generators.items():
        started = perf_counter()
        data = generate()
        elapsed = perf_counter() - started
        reports.append(
            {
                "generator": name,
                "throughput_mbps": byte_count * 8 / elapsed / 1_000_000,
                "nist_sp800_22": nist_report_for_bytes(data, test_names),
            }
        )
    return reports


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bytes", type=int, default=64 * 1024, dest="byte_count")
    parser.add_argument("--tests", nargs="*", default=DEFAULT_TESTS)
    args = parser.parse_args()
    print(
        json.dumps(
            {
                "warning": "Statistical results do not establish cryptographic security.",
                "results": compare(args.byte_count, tuple(args.tests)),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
