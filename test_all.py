"""综合测试脚本：覆盖正常流程(汇编→运行→调试)与异常指令处理。

运行方式: python3 test_all.py
"""
import os
import shutil
import sys
import tempfile
import unittest

import asm_core
import vm_core
import debug as debug_mod
from common import INSTR_ENCODE


# ---------------- 正常流程：汇编 ----------------
class TestAssembleNormal(unittest.TestCase):
    def test_simple_tape(self):
        text = "#0\n>x>f\nb\n"
        tapes = asm_core.parse_mmlang(text)
        self.assertEqual(tapes[0], '>x>fb')

    def test_expand_repeat_syntax(self):
        text = "#0\n>*5\nx*2\n"
        tapes = asm_core.parse_mmlang(text)
        self.assertEqual(tapes[0], '>>>>>xx')

    def test_multiple_tapes(self):
        text = "#0\nns\n#1\nns\n#2\nb\n"
        tapes = asm_core.parse_mmlang(text)
        self.assertEqual(list(tapes.keys()), [0, 1, 2])
        self.assertEqual(tapes[1], 'ns')

    def test_comments_are_ignored(self):
        text = "#0\n> x > f  # comment\nb\nanything here\n"
        tapes = asm_core.parse_mmlang(text)
        self.assertEqual(tapes[0], '>x>fb')

    def test_assemble_produces_bitarray(self):
        tapes_bin = asm_core.assemble("#0\n>x\n")
        self.assertEqual(vm_core.bitarray_to_str(tapes_bin[0]), '00000010')

    def test_empty_tape_ok(self):
        tapes = asm_core.parse_mmlang("#0\n")
        self.assertEqual(tapes[0], '')


# ---------------- 异常处理：汇编 ----------------
class TestAssembleErrors(unittest.TestCase):
    def test_no_tapes_raises(self):
        with self.assertRaises(ValueError):
            asm_core.parse_mmlang("just some comments\n")

    def test_non_consecutive_labels_raises(self):
        with self.assertRaises(ValueError) as ctx:
            asm_core.parse_mmlang("#0\nns\n#2\nb\n")
        self.assertIn('not consecutive', str(ctx.exception))

    def test_repeat_wildcard_unmatched(self):
        # `*` 不匹配合法指令时不展开，留作注释被丢弃
        tapes = asm_core.parse_mmlang("#0\n>x*2\n")
        self.assertEqual(tapes[0], '>xx')


# ---------------- 正常流程：运行 ----------------
class TestRunNormal(unittest.TestCase):
    def test_hello_style_output(self):
        # 数据磁带初始为0，x翻转得到 'H'(72) 的位模式
        state = vm_core.VmState(vm_core.parse_mmbin(_write_mmbin_str("#0\n>x>>>x>*4\n>x>x>>>x>>x>\n>x>x>>x>x>>\nb\n")))
        out = state.run()
        # 72 = 0b01001000，去除前导0后输出为 '1001000'
        self.assertIsNotNone(out)
        self.assertEqual(out, '1001000')

    def test_tape_switch(self):
        text = "#0\nns\n#1\nb\n"
        state = vm_core.VmState(vm_core.parse_mmbin(asm_core.write_mmbin_str(text)))
        out = state.run()
        self.assertEqual(out, '')

    def test_f_conditional_skip(self):
        # dp=0 时单元为0, f 不跳转
        state = vm_core.VmState(vm_core.parse_mmbin(asm_core.write_mmbin_str("#0\nf\nb\n")))
        state.run()
        self.assertEqual(state.final_output, '')

    def test_negative_dp_error(self):
        state = vm_core.VmState(vm_core.parse_mmbin(asm_core.write_mmbin_str("#0\n<b\n")))
        state.run()
        self.assertTrue(state.halted)
        self.assertIsNotNone(state.last_error)
        self.assertIn('negative', state.last_error)

    def test_unknown_instruction_is_skipped(self):
        # 反汇编为 '?' 的指令按 nop 处理(默认 pc+1)
        state = vm_core.VmState(vm_core.parse_mmbin(asm_core.write_mmbin_str("#0\n1111\nb\n")))
        out = state.run()
        self.assertEqual(out, '')


# ---------------- 正常流程：调试显示 ----------------
class TestDebugRender(unittest.TestCase):
    def test_render_basic(self):
        text = "#0\n>x\nb\n"
        state = vm_core.VmState(vm_core.parse_mmbin(asm_core.write_mmbin_str(text)))
        out = debug_mod.render(state)
        self.assertIn('[>]', out)
        self.assertIn('pc:0', out)
        self.assertIn('dp:0', out)

    def test_invalid_bits_render_question(self):
        # 1111 无法反汇编 -> ?
        text = "#0\n1111\n"
        state = vm_core.VmState(vm_core.parse_mmbin(asm_core.write_mmbin_str(text)))
        self.assertEqual(debug_mod.disassemble_chunk(state.cmd_tapes[0], 0), ['?'])

    def test_truncated_tail_render_question(self):
        # 末尾不足4位 -> ?
        state = vm_core.VmState(vm_core.parse_mmbin("0123456789"))
        ba = vm_core.str_to_bitarray('111')
        self.assertEqual(debug_mod.disassemble_chunk(ba, 0), ['?'])


# ---------------- 异常处理：加载 .mmbin ----------------
class TestMmbinErrors(unittest.TestCase):
    def test_non_consecutive_labels_raises(self):
        with self.assertRaises(ValueError):
            vm_core.parse_mmbin("#0\n0000\n#2\n0000\n")

    def test_no_tapes_raises(self):
        with self.assertRaises(ValueError):
            vm_core.parse_mmbin("")


# ---------------- 辅助：将内存中内容写为字符串 ----------------
def _write_mmbin_str(assemble_me):
    """把 .mmlang 文本汇编成 .mmbin 格式的字符串。"""
    tapes_bin = asm_core.assemble(assemble_me)
    lines = []
    for label in sorted(tapes_bin.keys()):
        lines.append(f'#{label}')
        s = vm_core.bitarray_to_str(tapes_bin[label])
        i = 0
        while i < len(s):
            lines.append(s[i:i + 8])
            i += 8
    return '\n'.join(lines) + '\n'


def main():
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()