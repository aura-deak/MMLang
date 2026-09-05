import sys
import vm_core
from common import INSTR_DECODE, bitarray_to_str


def disassemble_chunk(ba, offset, length=1):
    chars = []
    for i in range(length):
        start = (offset + i) * 4
        end = start + 4
        if end > len(ba):
            chars.append('?')
            continue
        chunk = ba[start:end]
        chars.append(INSTR_DECODE.get(bitarray_to_str(chunk), '?'))
    return chars


def format_tape(state, label):
    tape = state.cmd_tapes[label]
    tape_len = len(tape) // 4
    pc = state.tape_pcs[label] if label in state.tape_pcs else 0

    if label != state.current_label:
        show = min(10, tape_len)
        if show == 0:
            return f'{label}:'
        chars = disassemble_chunk(tape, 0, show)
        suffix = '...' if tape_len > show else ''
        return f'{label}:{"".join(chars)}{suffix}'

    if pc <= 5:
        show = min(10, tape_len - pc)
        if show <= 0:
            return f'[{label}]:[?]'
        chars = disassemble_chunk(tape, pc, show)
        marked = []
        for i, ch in enumerate(chars):
            if i == 0:
                marked.append(f'[{ch}]')
            else:
                marked.append(ch)
        return f'[{label}]:{"".join(marked)}'
    else:
        start = max(0, pc - 5)
        end = min(tape_len, pc + 6)
        span = end - start
        chars = disassemble_chunk(tape, start, span)
        mid = pc - start
        marked = []
        for i, ch in enumerate(chars):
            if i == mid:
                marked.append(f'[{ch}]')
            else:
                marked.append(ch)
        prefix = '...' if start > 0 else ''
        suffix = '...' if end < tape_len else ''
        return f'[{label}]:{prefix}{"".join(marked)}{suffix}'


def format_data_tape(state):
    dt = state.data_tape
    dp = state.dp
    left_start = max(0, dp - 5)
    right_end = min(len(dt), dp + 6)
    left_str = bitarray_to_str(dt[left_start:dp]) if dp > left_start else ''
    mid_str = bitarray_to_str(dt[dp:dp + 1]) if dp < len(dt) else '?'
    right_str = bitarray_to_str(dt[dp + 1:right_end]) if dp + 1 < right_end else ''
    prefix = '...' if left_start > 0 else ''
    suffix = '...' if right_end < len(dt) else ''
    return f'data-tape:{prefix}{left_str}[{mid_str}]{right_str}{suffix}'


def render(state):
    lines = []
    for label in sorted(state.cmd_tapes.keys()):
        lines.append(format_tape(state, label))
    lines.append(format_data_tape(state))
    lines.append(f'pc:{state.current_pc}')
    lines.append(f'dp:{state.dp}')
    lines.append('---')
    lines.append('press enter to continue')
    return '\n'.join(lines)


def main():
    files = vm_core.discover_files('.mmbin')
    if not files:
        print('No .mmbin files found in the current directory')
        sys.exit(1)

    fname = vm_core.prompt_select(files, 'binary')
    print(f'Loading: {fname}')

    state = vm_core.load_mmbin_from_file(fname)

    while not state.halted:
        print('\033[2J\033[H', end='')
        print(render(state))
        try:
            line = input()
        except EOFError:
            break
        if not state.step():
            break

    print('\033[2J\033[H', end='')
    print(render(state))
    print(f'\nProgram ended, steps executed: {state.step_count}')
    if state.last_error:
        print(f'Error: {state.last_error}')
    elif state.final_output is not None:
        print(f'Final output (b instruction): {state.final_output}')


if __name__ == '__main__':
    main()
