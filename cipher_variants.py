"""Student exercises for nonlinear stream-generator variants."""

from stream_cipher import LFSR_PERIOD_BITS, MAX_SEED, _next_bit

DEFAULT_GEFFE_SEEDS = (0xACE1, 0xBEEF, 0x1234)


def _validate(length: int, seeds: tuple[int, ...], offset: int) -> None:
    if not isinstance(length, int) or length < 0:
        raise ValueError("length must be a non-negative integer")
    if not isinstance(offset, int) or offset < 0:
        raise ValueError("offset must be a non-negative integer")
    if any(not isinstance(seed, int) or not 1 <= seed <= MAX_SEED for seed in seeds):
        raise ValueError("every seed must be an integer from 1 to 65535")


def nlfsr_keystream(length: int, seed: int, offset: int = 0) -> bytes:
    """Generate bytes from an NLFSR with one nonlinear AND feedback term.

    Use the base feedback bits 0, 2, 3, and 5, then XOR them with
    (bit 1 AND bit 7). Output, shifting, offset, and packing match the LFSR.
    """
    _validate(length, (seed,), offset)
    # TODO(student 7): replace this reference NLFSR in the handout.
    pass


def geffe_keystream(
    length: int,
    seeds: tuple[int, int, int] = DEFAULT_GEFFE_SEEDS,
    offset: int = 0,
) -> bytes:
    """Combine three LFSR output bits with the nonlinear Geffe function.

    If the three output bits are x, y, and z, emit
    (x AND y) XOR ((1 XOR x) AND z). Each component uses the base LFSR.
    """
    if len(seeds) != 3:
        raise ValueError("the Geffe generator needs exactly three seeds")
    _validate(length, seeds, offset)
    # TODO(student 8): replace this reference Geffe generator in the handout.
    pass
