
(function exposeCipher(root) {
  "use strict";
  const LFSR_PERIOD_BITS = 0xffff;

  function nextBit(state) {
    const outputBit = state & 1;

    const feedback =
      ((state >> 0) & 1) ^
      ((state >> 2) & 1) ^
      ((state >> 3) & 1) ^
      ((state >> 5) & 1);

    const nextState = (state >>> 1) | (feedback << 15);

    return [outputBit, nextState];
  }

  function keystream(length, seed, offset = 0) {
    if (!Number.isInteger(seed) || seed < 1 || seed > 0xffff) {
      throw new RangeError("invalid seed");
    }
    if (!Number.isInteger(length) || length < 0 ||
        !Number.isInteger(offset) || offset < 0) {
      throw new RangeError("invalid length or offset");
    }

    let state = seed;

    // Skip all bits before the requested byte offset.
    for (let i = 0; i < offset * 8; i++) {
      [, state] = nextBit(state);
    }

    const result = new Uint8Array(length);

    for (let i = 0; i < length; i++) {
      let byte = 0;

      // The first generated bit becomes the most significant bit.
      for (let j = 0; j < 8; j++) {
        const [bit, nextState] = nextBit(state);
        state = nextState;
        byte = (byte << 1) | bit;
      }

      result[i] = byte;
    }

    return result;
  }

  function xorBytes(data, seed, offset = 0) {
    if (!Number.isInteger(offset) || offset < 0) {
      throw new RangeError("invalid length or offset");
    }

    const input = data instanceof Uint8Array
      ? data
      : new Uint8Array(data);

    const key = keystream(input.length, seed, offset);
    const result = new Uint8Array(input.length);

    for (let i = 0; i < input.length; i++) {
      result[i] = input[i] ^ key[i];
    }

    return result;
  }

  const cipher = { keystream, xorBytes };
  root.LfsrCipher = cipher;
  if (typeof module !== "undefined") module.exports = cipher;
}(typeof self !== "undefined" ? self : globalThis));
