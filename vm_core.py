import os
import re
from bitarray import bitarray
from common import INSTR_DECODE, str_to_bitarray, bitarray_to_str


def discover_files(ext, directory='.'):
    return sorted(f for f in os.listdir(directory) if f.endswith(ext))


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
            idx = int(input('Enter index: ').strip())
            if 0 <= idx < len(files):
                return files[idx]
        except ValueError:
            pass
        print(f'Please enter an integer between 0 and {len(files)-1}')


def parse_mmbin(text):
    tapes = {}
    current_label = None
    current_bits = []

    def flush():
        nonlocal current_bits
        if current_label is not None:
            tapes[current_label] = ''.join(current_bits)
            current_bits = []

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        label_match = re.fullmatch(r'#(\d+)', stripped)
        if label_match:
            flush()
            current_label = int(label_match.group(1))
            continue
        if all(c in '01' for c in stripped):
            current_bits.append(stripped)

    flush()

    expected = 0
    for key in sorted(tapes.keys()):
        if key != expected:
            raise ValueError(f'Tape labels are not consecutive: expected #{expected}, found #{key}')
        expected += 1

    tapes_bin = {}
    for label, bits_str in tapes.items():
        ba = str_to_bitarray(bits_str)
        tapes_bin[label] = ba

    return tapes_bin


class VmState:
    def __init__(self, cmd_tapes):
        self.cmd_tapes = dict(cmd_tapes)
        self.queue = sorted(cmd_tapes.keys())
        self.tape_pcs = {label: 0 for label in self.queue}
        self.current_idx = 0
        self.data_tape = bitarray()
        self.dp = 0
        self.halted = False
        self.final_output = None
        self.step_count = 0
        self.last_error = None

    @property
    def current_label(self):
        return self.queue[self.current_idx] if self.queue else None

    @property
    def current_pc(self):
        return self.tape_pcs.get(self.current_label, 0)

    @current_pc.setter
    def current_pc(self, val):
        self.tape_pcs[self.current_label] = val

    def current_tape_len(self):
        lbl = self.current_label
        return len(self.cmd_tapes[lbl]) // 4 if lbl is not None else 0

    def fetch_instr(self):
        lbl = self.current_label
        tape = self.cmd_tapes[lbl]
        pc = self.current_pc
        start = pc * 4
        end = start + 4
        if end > len(tape):
            return None
        bits = tape[start:end]
        return INSTR_DECODE.get(bitarray_to_str(bits), '?')

    def ensure_data_tape(self):
        while self.dp + 5 > len(self.data_tape):
            try:
                import data_tape_maker
                v = data_tape_maker.make(len(self.data_tape))
            except Exception:
                v = 0
            self.data_tape.append(bool(v))

    def expand_data_tape_to(self, target_len):
        while len(self.data_tape) < target_len:
            try:
                import data_tape_maker
                v = data_tape_maker.make(len(self.data_tape))
            except Exception:
                v = 0
            self.data_tape.append(bool(v))

    def step(self):
        if self.halted:
            return False
        self.ensure_data_tape()

        instr = self.fetch_instr()
        if instr is None:
            instr = 'l'

        self.step_count += 1

        if instr == '>':
            self.dp += 1
            self.current_pc += 1
        elif instr == '<':
            self.dp -= 1
            if self.dp < 0:
                self.last_error = f'Data pointer became negative (dp={self.dp}), terminating'
                self.halted = True
                self.final_output = None
                return False
            self.current_pc += 1
        elif instr == 'x':
            self.expand_data_tape_to(self.dp + 1)
            self.data_tape.invert(self.dp)
            self.current_pc += 1
        elif instr == 'f':
            self.expand_data_tape_to(self.dp + 1)
            if self.data_tape[self.dp]:
                self.current_pc += 2
            else:
                self.current_pc += 1
        elif instr == 's':
            self.current_idx = (self.current_idx + 1) % len(self.queue)
            self.current_pc = 0
        elif instr == 'b':
            self.expand_data_tape_to(self.dp)
            result = self.data_tape[:self.dp]
            self.final_output = bitarray_to_str(result)
            self.halted = True
            return False
        elif instr == 'p':
            self.expand_data_tape_to(self.dp)
            snapshot = self.data_tape[:self.dp]
            new_label = max(self.cmd_tapes.keys()) + 1 if self.cmd_tapes else 0
            self.cmd_tapes[new_label] = snapshot.copy()
            self.tape_pcs[new_label] = 0
            self.queue.insert(self.current_idx + 1, new_label)
            self.data_tape = self.data_tape[:self.dp]
            if len(self.data_tape) == 0:
                self.dp += 1
            self.current_pc += 1
        elif instr == 'n':
            self.current_pc += 1
        elif instr == 'l':
            self.current_pc = 0
        elif instr == 'r':
            self.dp = 0
            self.current_pc += 1
        else:
            self.current_pc += 1

        return True

    def run(self, max_steps=1000000):
        steps = 0
        while steps < max_steps:
            if not self.step():
                break
            steps += 1
        return self.final_output


def load_mmbin_from_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    cmd_tapes = parse_mmbin(text)
    return VmState(cmd_tapes)
