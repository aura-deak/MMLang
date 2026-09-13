import sys
import vm_core


def bits_to_ascii(bits):
    if len(bits) % 8 != 0 or not bits:
        return None
    chars = []
    for i in range(0, len(bits), 8):
        byte = bits[i:i + 8]
        code = int(byte, 2)
        if not (0x20 <= code < 0x7F):
            return None
        chars.append(chr(code))
    return ''.join(chars)


def main():
    files = vm_core.discover_files('.mmbin')
    if not files:
        print('No .mmbin files found in the current directory')
        sys.exit(1)

    fname = vm_core.prompt_select(files, 'binary')
    print(f'Loading: {fname}')

    state = vm_core.load_mmbin_from_file(fname)
    print(f'Program tapes: {list(state.queue)}')

    output = state.run(max_steps=10000000)
    print(f'Steps executed: {state.step_count}')

    if state.last_error:
        print(f'Execution error: {state.last_error}')
        sys.exit(1)

    if state.halted and output is not None:
        print(f'Final output (truncated by b instruction):')
        print(output)
        ascii_text = bits_to_ascii(output)
        if ascii_text is not None:
            print(f'ASCII decoded: {ascii_text}')
    elif not state.halted:
        print('Program did not halt (max steps reached or infinite loop)')
    else:
        print('Program exited normally')


if __name__ == '__main__':
    main()
