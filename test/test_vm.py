import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
import data_tape_maker as dtm
import asm_core
import vm_core
from common import make_bitarray_from_chars, str_to_bitarray, bitarray_to_str


def make_state(*tapes):
    """Create a VmState from char-sequence tapes. tapes is list of strings."""
    cmd = {i: make_bitarray_from_chars(seq) for i, seq in enumerate(tapes)}
    return vm_core.VmState(cmd)


def set_maker(func):
    dtm.make = func


class TestArrowRight(unittest.TestCase):
    def test_dp_increments(self):
        set_maker(lambda dp: 0)
        s = make_state('>')
        s.step()
        self.assertEqual(s.dp, 1)

    def test_multiple_arrows(self):
        set_maker(lambda dp: 0)
        s = make_state('>>')
        s.step(); s.step()
        self.assertEqual(s.dp, 2)

    def test_pc_increments(self):
        set_maker(lambda dp: 0)
        s = make_state('>>>')
        s.step()
        self.assertEqual(s.current_pc, 1)


class TestArrowLeft(unittest.TestCase):
    def test_dp_decrements(self):
        set_maker(lambda dp: 0)
        s = make_state('>>>>><')
        # step 5 >'s → dp=5, then step < → dp=4
        for _ in range(5): s.step()
        self.assertEqual(s.dp, 5)
        s.step()
        self.assertEqual(s.dp, 4)

    def test_dp_negative_halts(self):
        set_maker(lambda dp: 0)
        s = make_state('<')
        s.step()
        self.assertEqual(s.dp, -1)
        self.assertTrue(s.halted)
        self.assertIn('negative', s.last_error)


class TestFlipX(unittest.TestCase):
    def test_flip_0_to_1(self):
        set_maker(lambda dp: 0)
        s = make_state('x')
        s.step()
        self.assertEqual(bool(s.data_tape[0]), True)

    def test_flip_1_to_0(self):
        set_maker(lambda dp: 1)
        s = make_state('x')
        s.step()
        self.assertEqual(bool(s.data_tape[0]), False)

    def test_flip_twice_returns(self):
        set_maker(lambda dp: 0)
        s = make_state('xx')
        s.step(); s.step()
        self.assertEqual(bool(s.data_tape[0]), False)

    def test_flip_nonzero_position(self):
        set_maker(lambda dp: 0)
        s = make_state('>x')
        s.step(); s.step()
        self.assertEqual(bool(s.data_tape[1]), True)
        self.assertEqual(bool(s.data_tape[0]), False)


class TestConditionalF(unittest.TestCase):
    def test_data_zero_no_jump(self):
        set_maker(lambda dp: 0)
        s = make_state('fn')
        s.step()
        self.assertEqual(s.current_pc, 1)

    def test_data_one_jumps(self):
        set_maker(lambda dp: 1)
        s = make_state('fn')
        s.step()
        self.assertEqual(s.current_pc, 2)

    def test_jump_skips_b(self):
        set_maker(lambda dp: 1)
        s = make_state('fb>')
        s.step()
        self.assertEqual(s.current_pc, 2)
        self.assertFalse(s.halted)

    def test_f_fallthrough_to_b(self):
        set_maker(lambda dp: 0)
        s = make_state('fb')
        s.run()
        self.assertTrue(s.halted)


class TestSwitchS(unittest.TestCase):
    def test_two_tapes_alternates(self):
        set_maker(lambda dp: 0)
        s = make_state('ns', 'ns')
        labels_seen = []
        for _ in range(20):
            labels_seen.append(s.current_label)
            s.step()
        switches = sum(1 for i in range(1, len(labels_seen)) if labels_seen[i] != labels_seen[i - 1])
        self.assertGreaterEqual(switches, 8)

    def test_switch_resets_pc(self):
        set_maker(lambda dp: 0)
        s = make_state('nnns', 'n')
        for _ in range(4): s.step()
        self.assertEqual(s.current_label, 1)
        self.assertEqual(s.current_pc, 0)

    def test_single_tape_s_loops(self):
        set_maker(lambda dp: 0)
        s = make_state('ns')
        for _ in range(10): s.step()
        self.assertEqual(s.current_label, 0)


class TestHaltB(unittest.TestCase):
    def test_halts(self):
        set_maker(lambda dp: 0)
        s = make_state('b')
        s.step()
        self.assertTrue(s.halted)

    def test_truncates_data_tape(self):
        set_maker(lambda dp: 0)
        s = make_state('>x>x>b')
        # dp=3, data_tape = [0,1,1,0,...] → output = data_tape[:3] = "011"
        s.run()
        self.assertEqual(s.final_output, '011')

    def test_b_output_on_empty_tape(self):
        set_maker(lambda dp: 0)
        s = make_state('b')
        s.run()
        self.assertEqual(s.final_output, '')


class TestSnapshotP(unittest.TestCase):
    def test_p_snapshot_is_program_tape(self):
        """p's snapshot is stored verbatim as new program tape."""
        set_maker(lambda dp: 0)
        s = make_state('>x>p')
        # >  dp=1, ensure data
        # x  flip data[1]
        # >  dp=2
        # p  snapshot = data_tape[:2] = [0, 1]
        for _ in range(4): s.step()
        self.assertIn(1, s.cmd_tapes)
        # cmd_tapes[1] bitarray == [0, 1]
        from common import bitarray_to_str
        self.assertEqual(bitarray_to_str(s.cmd_tapes[1])[:2], '01')

    def test_p_queue_after_existing_tapes(self):
        set_maker(lambda dp: 0)
        s = make_state('>p', 'n')
        s.step()  # >
        s.step()  # p → inserts after current position
        self.assertEqual(s.queue[0], 0)
        self.assertIn(1, s.queue)
        self.assertIn(2, s.queue)

    def test_p_data_tape_truncated(self):
        set_maker(lambda dp: lambda dp: 0)
        s = make_state('>x>x>p')
        for _ in range(6): s.step()  # 5 instrs + p
        self.assertLessEqual(len(s.data_tape), s.dp + 5)

    def test_p_current_tape_continues(self):
        set_maker(lambda dp: 0)
        s = make_state('>pn')
        s.step(); s.step()
        # After p (step 2), we're still on tape 0, next instr is n → pc should advance
        self.assertEqual(s.current_pc, 2)


class TestNoopN(unittest.TestCase):
    def test_pc_advances(self):
        set_maker(lambda dp: 0)
        s = make_state('n')
        s.step()
        self.assertEqual(s.current_pc, 1)

    def test_no_side_effect(self):
        set_maker(lambda dp: 0)
        s = make_state('n')
        before_dp = s.dp
        before_len = len(s.data_tape)
        s.step()
        self.assertEqual(s.dp, before_dp)


class TestLoopL(unittest.TestCase):
    def test_resets_pc_to_zero(self):
        set_maker(lambda dp: 0)
        s = make_state('>>>>l')
        for _ in range(4): s.step()
        self.assertEqual(s.current_pc, 4)
        s.step()
        self.assertEqual(s.current_pc, 0)

    def test_l_loops_program(self):
        set_maker(lambda dp: 0)
        s = make_state('nl')
        for _ in range(100):
            if not s.step(): break
        self.assertEqual(s.current_pc, 0)


class TestResetR(unittest.TestCase):
    def test_dp_back_to_zero(self):
        set_maker(lambda dp: 0)
        s = make_state('>>>>>r')
        for _ in range(5): s.step()
        self.assertEqual(s.dp, 5)
        s.step()
        self.assertEqual(s.dp, 0)

    def test_r_after_switch_resets_dp(self):
        set_maker(lambda dp: 0)
        s = make_state('>>>s', 'r')
        # step 1: > dp=1, step 2: > dp=2, step 3: > dp=3, step 4: s switch to tape1, step 5: r dp=0
        for _ in range(5): s.step()
        self.assertEqual(s.current_label, 1)
        self.assertEqual(s.dp, 0)


class TestDataTapeMaker(unittest.TestCase):
    def test_default_all_zero(self):
        set_maker(lambda dp: 0)
        s = make_state('>' * 20)
        for _ in range(10): s.step()
        for i in range(len(s.data_tape)):
            self.assertEqual(bool(s.data_tape[i]), False)

    def test_custom_maker_used(self):
        set_maker(lambda dp: dp % 2)
        s = make_state('>' * 20)
        for _ in range(10): s.step()
        self.assertEqual(bool(s.data_tape[0]), False)
        self.assertEqual(bool(s.data_tape[1]), True)
        self.assertEqual(bool(s.data_tape[2]), False)
        self.assertEqual(bool(s.data_tape[3]), True)


class TestProgramExamples(unittest.TestCase):
    def test_two_tape_loop(self):
        set_maker(lambda dp: 0)
        s = make_state('ns', 'ns')
        count = 0
        for _ in range(200):
            if not s.step(): break
            count += 1
        self.assertEqual(count, 200)
        self.assertFalse(s.halted)

    def test_clear_zeros_program(self):
        set_maker(lambda dp: dp % 2)
        s = make_state('fxx>l')
        for _ in range(1000):
            if not s.step(): break
        # program never halts (no b), just loops
        self.assertFalse(s.halted)

    def test_hello_world_truncates_to_ascii(self):
        set_maker(lambda dp: 0)
        src = '#0\n>x>>>x>*4\n>x>x>>>x>>x>\n>x>x>>x>x>>>\n>x>x>>x>x>>>\n>x>x>>x>x>x>x>\n>>x>*6\n>x>>x>>x>x>x>\n>x>x>>x>x>x>x>\n>x>x>x>>>x>>\n>x>x>>x>x>>>\n>x>x>>>x>*4\nb'
        tapes = asm_core.assemble(src)
        import vm_core
        state = vm_core.VmState(tapes)
        state.run(max_steps=500000)
        self.assertTrue(state.halted)
        self.assertIsNotNone(state.final_output)
        chars = []
        out = state.final_output
        for i in range(0, len(out), 8):
            byte = out[i:i + 8]
            if len(byte) == 8:
                chars.append(chr(int(byte, 2)))
        text = ''.join(chars)
        self.assertEqual(text, 'Hello World')


class TestEdgeCases(unittest.TestCase):
    def test_instruction_fetched_at_tape_end(self):
        set_maker(lambda dp: 0)
        s = make_state('nnn')
        s.step(); s.step(); s.step()
        self.assertEqual(s.current_pc, 3)
        s.step()
        # past end → behaves like 'l' → pc=0
        self.assertEqual(s.current_pc, 0)

    def test_parse_mmbin_no_consecutive_error(self):
        text = '#0\n00000000\n#2\n0000\n'
        with self.assertRaises(ValueError):
            vm_core.parse_mmbin(text)

    def test_three_tapes_round_robin(self):
        set_maker(lambda dp: 0)
        s = make_state('s', 's', 's')
        labels = []
        for _ in range(6):
            labels.append(s.current_label)
            s.step()
        self.assertEqual(labels[:3], [0, 1, 2])
        self.assertEqual(labels[3:6], [0, 1, 2])


if __name__ == '__main__':
    unittest.main(verbosity=2)
