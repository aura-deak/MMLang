from bitarray import bitarray

INSTR_ENCODE = {
    '>': '0000',
    '<': '0001',
    'x': '0010',
    'f': '0011',
    's': '0100',
    'b': '0101',
    'p': '0110',
    'n': '0111',
    'l': '1000',
    'r': '1001',
}

INSTR_DECODE = {v: k for k, v in INSTR_ENCODE.items()}

VALID_INSTRUCTIONS = set(INSTR_ENCODE.keys())

HEX_CHARS = set('0123456789abcdefABCDEF')


def str_to_bitarray(bits_str):
    ba = bitarray()
    for c in bits_str:
        if c == '0':
            ba.append(False)
        elif c == '1':
            ba.append(True)
    return ba


def bitarray_to_str(ba):
    return ''.join('1' if b else '0' for b in ba)


def char_to_bitarray(c):
    return str_to_bitarray(INSTR_ENCODE[c])


def bitarray_to_char(ba):
    return INSTR_DECODE.get(bitarray_to_str(ba), None)


def make_bitarray_from_chars(chars):
    ba = bitarray()
    for c in chars:
        if c in INSTR_ENCODE:
            ba.extend(char_to_bitarray(c))
    return ba
