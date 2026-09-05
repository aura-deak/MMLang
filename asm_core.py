import os
import re
from common import INSTR_ENCODE, VALID_INSTRUCTIONS, make_bitarray_from_chars, str_to_bitarray, bitarray_to_str
from bitarray import bitarray


def discover_files(ext, directory='.'):
    files = sorted(f for f in os.listdir(directory) if f.endswith(ext))
    return files


def prompt_select(files, label='file'):
    if not files:
        return None
    if len(files) == 1:
        return files[0]
    print(f'Multiple {label} files found, please select one:')
    for i, f in enumerate(files):
        print(f'  [{i}] {f}')
    while True:
        try:
            choice = input('Enter index: ').strip()
            idx = int(choice)
            if 0 <= idx < len(files):
                return files[idx]
        except ValueError:
            pass
        print(f'Please enter an integer between 0 and {len(files)-1}')


def expand_repeat(text):
    pattern = re.compile(r'([>xfsbpnlr])\*(\d+)')
    prev = None
    while prev != text:
        prev = text
        text = pattern.sub(lambda m: m.group(1) * int(m.group(2)), text)
    return text


def parse_mmlang(text):
    text = expand_repeat(text)
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    tapes = {}
    current_label = None
    current_chars = []

    def flush_current():
        if current_label is not None:
            tapes[current_label] = ''.join(current_chars)

    for line in text.split('\n'):
        stripped = line.strip()
        if not stripped:
            continue
        label_match = re.fullmatch(r'#(\d+)', stripped)
        if label_match:
            flush_current()
            current_label = int(label_match.group(1))
            current_chars = []
            continue
        for c in stripped:
            if c in VALID_INSTRUCTIONS:
                current_chars.append(c)

    flush_current()

    if not tapes:
        raise ValueError('No valid instructions or tape labels found in source')

    expected = 0
    for key in sorted(tapes.keys()):
        if key != expected:
            raise ValueError(f'Tape labels are not consecutive: expected #{expected}, found #{key}')
        expected += 1

    return tapes


def assemble(mmlang_text):
    tapes_chars = parse_mmlang(mmlang_text)
    tapes_bin = {}
    for label, chars in tapes_chars.items():
        if not chars:
            tapes_bin[label] = bitarray()
        else:
            tapes_bin[label] = make_bitarray_from_chars(chars)
    return tapes_bin


def write_mmbin(tapes_bin, output_path):
    lines = []
    for label in sorted(tapes_bin.keys()):
        ba = tapes_bin[label]
        lines.append(f'#{label}')
        s = bitarray_to_str(ba)
        i = 0
        while i < len(s):
            chunk = s[i:i + 8]
            lines.append(chunk)
            i += 8
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
