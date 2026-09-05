import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tempfile
import unittest

import asm_core
import vm_core
from common import (
    INSTR_ENCODE, INSTR_DECODE, VALID_INSTRUCTIONS,
    make_bitarray_from_chars, str_to_bitarray, bitarray_to_str,
)


class TestInstructionTable(unittest.TestCase):
    def test_encode_table_complete(self):
        expected = {
            '>': '0000', '<': '0001', 'x': '0010', 'f': '0011',
            's': '0100', 'b': '0101', 'p': '0110', 'n': '0111',
            'l': '1000', 'r': '1001',
        }
        self.assertEqual(INSTR_ENCODE, expected)

    def test_all_4bit(self):
        for k, v in INSTR_ENCODE.items():
            self.assertEqual(len(v), 4, f'{k} not 4 bits')

    def test_roundtrip(self):
        for k, v in INSTR_ENCODE.items():
            self.assertEqual(INSTR_DECODE[v], k)
        self.assertEqual(len(INSTR_DECODE), 10)

    def test_valid_set(self):
        self.assertEqual(VALID_INSTRUCTIONS, set(INSTR_ENCODE.keys()))


class TestParseMmlang(unittest.TestCase):
    def test_repeat_syntax(self):
        result = asm_core.parse_mmlang('#0\n>*5')
        self.assertEqual(result[0], '>>>>>')

    def test_repeat_syntax_multiple(self):
        result = asm_core.parse_mmlang('#0\n>x*3')
        self.assertEqual(result[0], '>xxx')

    def test_repeat_zero(self):
        result = asm_core.parse_mmlang('#0\n>x*0>')
        self.assertEqual(result[0], '>>')

    def test_collects_valid_ignores_non_valid(self):
        # Non-instruction chars (h,e,l,o,w,r,d) are ignored;
        # valid chars (x, >, <, l, r) are collected from EVERY position.
        result = asm_core.parse_mmlang('#0\nx hello > world')
        # 'x', 'l', 'l', '>', 'r', 'l' are all valid instructions
        valid = set('>xfsbpnlr')
        self.assertTrue(all(c in valid for c in result[0]))
        self.assertEqual(result[0].count('x'), 1)
        self.assertEqual(result[0].count('>'), 1)

    def test_collects_valid_instr_inside_garbage(self):
        # foo->f,o,o (f valid), bar->b,a,r (b,r valid), n valid, baz->b,a,z (b valid)
        result = asm_core.parse_mmlang('#0\nfoo s bar n baz')
        valid = set('>xfsbpnlr')
        self.assertTrue(all(c in valid for c in result[0]))
        self.assertIn('s', result[0])
        self.assertIn('n', result[0])

    def test_multi_tape(self):
        result = asm_core.parse_mmlang('#0\nns\n#1\nns')
        self.assertEqual(sorted(result.keys()), [0, 1])
        self.assertEqual(result[0], 'ns')
        self.assertEqual(result[1], 'ns')

    def test_consecutive_labels_required(self):
        with self.assertRaises(ValueError):
            asm_core.parse_mmlang('#0\nn\n#2\nn')

    def test_empty_program_no_instructions(self):
        # A label with no instructions produces empty chars but no error
        result = asm_core.parse_mmlang('#0')
        self.assertEqual(result[0], '')

    def test_fully_empty_source_errors(self):
        with self.assertRaises(ValueError):
            asm_core.parse_mmlang('')

    def test_ignore_blank_lines_and_tabs(self):
        result = asm_core.parse_mmlang('#0\n\nn\n\t  x  \n\n>')
        self.assertEqual(result[0], 'nx>')

    def test_crlf_newlines(self):
        result = asm_core.parse_mmlang('#0\r\nn\r\n#1\r\nx\r\n')
        self.assertEqual(sorted(result.keys()), [0, 1])


class TestAssembleAndWrite(unittest.TestCase):
    def test_assemble_single_tape(self):
        tapes = asm_core.assemble('#0\nf x x > l')
        self.assertEqual(list(tapes.keys()), [0])
        self.assertEqual(len(tapes[0]), 5 * 4)

    def test_assemble_multi_tape(self):
        tapes = asm_core.assemble('#0\nns\n#1\nns')
        self.assertEqual(sorted(tapes.keys()), [0, 1])
        self.assertEqual(len(tapes[0]), 2 * 4)
        self.assertEqual(len(tapes[1]), 2 * 4)

    def test_assemble_roundtrip(self):
        chars = '>xsfnblrp'
        tapes = asm_core.assemble(f'#0\n{chars}')
        self.assertEqual(len(tapes[0]), len(chars) * 4)

    def test_write_then_parse_mmbin(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 't.mmlang')
            out = os.path.join(tmp, 't.mmbin')
            with open(src, 'w') as f:
                f.write('#0\nf x x > l\n')
            with open(src) as f:
                tapes = asm_core.assemble(f.read())
            asm_core.write_mmbin(tapes, out)
            with open(out) as f:
                loaded = vm_core.parse_mmbin(f.read())
            self.assertEqual(sorted(loaded.keys()), [0])
            self.assertEqual(len(loaded[0]), len(tapes[0]))

    def test_mmbin_line_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 't.mmlang')
            out = os.path.join(tmp, 't.mmbin')
            with open(src, 'w') as f:
                f.write('#0\nns\n')
            with open(src) as f:
                tapes = asm_core.assemble(f.read())
            asm_core.write_mmbin(tapes, out)
            with open(out) as f:
                content = f.read()
            self.assertIn('#0', content)
            for line in content.strip().split('\n'):
                if line.startswith('#'):
                    continue
                self.assertTrue(all(c in '01' for c in line))
                self.assertLessEqual(len(line), 8)

    def test_discover_and_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            for fname in ('a.mmlang', 'b.mmlang'):
                with open(os.path.join(tmp, fname), 'w') as f:
                    f.write('#0\nn\n')
            files = asm_core.discover_files('.mmlang', directory=tmp)
            self.assertEqual(files, ['a.mmlang', 'b.mmlang'])


class TestInstructionEncoding(unittest.TestCase):
    def test_each_instruction_code(self):
        samples = [
            ('>', '0000'), ('<', '0001'), ('x', '0010'), ('f', '0011'),
            ('s', '0100'), ('b', '0101'), ('p', '0110'), ('n', '0111'),
            ('l', '1000'), ('r', '1001'),
        ]
        for ch, bits in samples:
            ba = make_bitarray_from_chars(ch)
            self.assertEqual(bitarray_to_str(ba), bits, f'{ch} code mismatch')

    def test_unknown_bits_disassembly(self):
        from common import INSTR_DECODE
        self.assertIsNone(INSTR_DECODE.get('1111'))
        self.assertIsNone(INSTR_DECODE.get('01110'))  # 5 bits, not 4
        self.assertEqual(INSTR_DECODE['0000'], '>')
        self.assertEqual(INSTR_DECODE['0111'], 'n')


if __name__ == '__main__':
    unittest.main(verbosity=2)
