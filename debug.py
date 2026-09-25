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

    if len(dt) + 2 <= avail:
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


def fetch_current(state):
    return state.fetch_instr()


def render(state):
    w = _terminal_width()
    lines = []
    for label in sorted(state.cmd_tapes.keys()):
        lines.append(format_tape(state, label, w))
    lines.append(format_data_tape(state, w))
    lines.append(f'pc:{state.current_pc}')
    lines.append(f'dp:{state.dp}')
    lines.append(f'steps:{state.step_count}')
    return '\n'.join(lines)


HELP_TEXT = """命令:
  [enter] / n    单步执行
  c              continue, 连续运行到下一个断点 (n) 或停机
  r              run, 连续运行到底
  q              quit, 退出调试器
  h / ?          显示帮助"""


def clear_screen():
    print('\033[2J\033[H', end='')


def prompt():
    try:
        return input('[n/c/r/q/h]> ').strip()
    except EOFError:
        return 'q'


def show_state(state, banner=None):
    clear_screen()
    if banner:
        print(banner)
    print(render(state))


def run_to_next_breakpoint(state):
    while not state.halted:
        if not state.step():
            return False
        instr = fetch_current(state)
        if instr == 'n':
            return True
    return False


def run_to_end(state, max_steps=1000000):
    state.run(max_steps=max_steps)


def step_one(state):
    if state.halted:
        return False
    return state.step()


def main():
    files = vm_core.discover_files('.mmbin')
    if not files:
        print('No .mmbin files found in the current directory')
        sys.exit(1)

    fname = vm_core.prompt_select(files, 'binary')
    print(f'Loading: {fname}')
    print(f'断点触发条件: n 指令')

    state = vm_core.load_mmbin_from_file(fname)

    while not state.halted:
        instr = fetch_current(state)
        is_bp = (instr == 'n')

        banner = ''
        if is_bp:
            banner = f'>>> 断点: 遇到 n 指令 at tape #{state.current_label} pc={state.current_pc} <<<'
        show_state(state, banner)

        cmd = prompt()
        if cmd in ('q', 'quit', 'exit'):
            print('调试已退出')
            return
        elif cmd in ('h', '?', 'help'):
            show_state(state, banner)
            print(HELP_TEXT)
            input('按回车继续...')
            continue
        elif cmd in ('c', 'continue'):
            run_to_next_breakpoint(state)
        elif cmd in ('r', 'run'):
            run_to_end(state)
        elif cmd in ('', 'n', 'step', 'next'):
            step_one(state)
        else:
            print(f'未知命令: {cmd}')
            show_state(state, banner)
            print(HELP_TEXT)
            input('按回车继续...')
            continue

    clear_screen()
    print(render(state))
    print(f'\n程序结束, 总步数: {state.step_count}')
    if state.last_error:
        print(f'错误: {state.last_error}')
    elif state.final_output is not None:
        from run import bits_to_ascii
        print(f'最终输出 (b 指令): {state.final_output}')
        ascii_text = bits_to_ascii(state.final_output)
        if ascii_text is not None:
            print(f'ASCII 解码: {ascii_text}')


if __name__ == '__main__':
    main()
