import os
import sys
import vm_core
from common import INSTR_DECODE, bitarray_to_str


def _terminal_width(default=80):
    try:
        return os.get_terminal_size().columns
    except OSError:
        return default


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


def format_tape(state, label, term_width):
    tape = state.cmd_tapes[label]
    tape_len = len(tape) // 4
    pc = state.tape_pcs.get(label, 0)

    if label != state.current_label:
        prefix = f'{label}:'
        suffix_space = 3 if tape_len > 0 else 0
        show = max(0, term_width - len(prefix) - suffix_space)
        if show == 0 or tape_len == 0:
            return prefix
        show = min(show, tape_len)
        chars = disassemble_chunk(tape, 0, show)
        suffix = '...' if tape_len > show else ''
        return f'{prefix}{"".join(chars)}{suffix}'

    cursor_prefix = f'[{label}]:'
    cursor_prefix_len = len(cursor_prefix)

    if tape_len == 0:
        return f'{cursor_prefix}[?]'

    avail = max(1, term_width - cursor_prefix_len)

    if tape_len + 2 <= avail:
        chars = disassemble_chunk(tape, 0, tape_len)
        marked = []
        for i, ch in enumerate(chars):
            if i == pc:
                marked.append(f'[{ch}]')
            else:
                marked.append(ch)
        return f'{cursor_prefix}{"".join(marked)}'

    cursor_len = 3
    if avail < cursor_len + 2:
        return f'{cursor_prefix}[?]'

    left_slots = (avail - cursor_len - 6) // 2
    right_slots = avail - cursor_len - 6 - left_slots
    start = pc - left_slots
    end = pc + right_slots + 1
    prefix = '...'
    suffix = '...'

    if start <= 0:
        prefix = ''
        start = 0
    if end >= tape_len:
        suffix = ''
        end = tape_len

    need = avail - len(prefix) - len(suffix)
    if end - start > need:
        end = start + need
        if end >= tape_len:
            suffix = ''
        else:
            suffix = '...'

    chars = disassemble_chunk(tape, start, end - start)
    mid = pc - start
    marked = []
    for i, ch in enumerate(chars):
        if i == mid:
            marked.append(f'[{ch}]')
        else:
            marked.append(ch)
    return f'{cursor_prefix}{prefix}{"".join(marked)}{suffix}'


def format_data_tape(state, term_width):
    dt = state.data_tape
    dp = state.dp
    prefix = 'data-tape:'
    prefix_len = len(prefix)
    avail = max(1, term_width - prefix_len)

    if len(dt) == 0:
        return f'{prefix}?' * min(avail, 1) + '?' * max(0, avail - 1)

    total_without_cursor = len(dt) - 1
    if total_without_cursor + 2 <= avail:
        return f'{prefix}{bitarray_to_str(dt[:dp])}[{bitarray_to_str(dt[dp:dp+1])}]{bitarray_to_str(dt[dp+1:])}'

    cursor_len = 3
    if avail < cursor_len + 2:
        return f'{prefix}[?]'

    left_slots = (avail - cursor_len - 6) // 2
    right_slots = avail - cursor_len - 6 - left_slots
    left_start = dp - left_slots
    right_end = dp + right_slots + 1
    pre = '...'
    post = '...'

    if left_start <= 0:
        pre = ''
        left_start = 0
    if right_end >= len(dt):
        post = ''
        right_end = len(dt)

    need = avail - cursor_len - len(pre) - len(post)
    if right_end - left_start > need:
        right_end = left_start + need
        if right_end >= len(dt):
            post = ''
        else:
            post = '...'

    left_str = bitarray_to_str(dt[left_start:dp]) if dp > left_start else ''
    mid_str = bitarray_to_str(dt[dp:dp + 1]) if dp < len(dt) else '?'
    right_str = bitarray_to_str(dt[dp + 1:right_end]) if dp + 1 < right_end else ''
    return f'{prefix}{pre}{left_str}[{mid_str}]{right_str}{post}'


def render(state):
    w = _terminal_width()
    lines = []
    for label in sorted(state.cmd_tapes.keys()):
        lines.append(format_tape(state, label, w))
    lines.append(format_data_tape(state, w))
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
