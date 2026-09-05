import sys
import vm_core


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
    elif not state.halted:
        print('Program did not halt (max steps reached or infinite loop)')
    else:
        print('Program exited normally')


if __name__ == '__main__':
    main()
