(function exposeCipher(root) {
  "use strict";
  const LFSR_PERIOD_BITS = 0xffff;

  function nextBit(state) {
    // TODO(student 4): replace this reference state transition in the handout.
    
  }

  function keystream(length, seed, offset = 0) {
    if (!Number.isInteger(seed) || seed < 1 || seed > 0xffff) throw new RangeError("invalid seed");
    if (!Number.isInteger(length) || length < 0 || !Number.isInteger(offset) || offset < 0) {
      throw new RangeError("invalid length or offset");
    }
    // TODO(student 5): replace this reference generator in the handout.
  }

  function xorBytes(data, seed, offset = 0) {
    // TODO(student 6): replace this reference XOR operation in the handout.
  }

  const cipher = { keystream, xorBytes };
  root.LfsrCipher = cipher;
  if (typeof module !== "undefined") module.exports = cipher;
}(typeof self !== "undefined" ? self : globalThis));
