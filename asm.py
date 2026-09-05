import sys
import asm_core


def main():
    files = asm_core.discover_files('.mmlang')
    if not files:
        print('No .mmlang files found in the current directory')
        sys.exit(1)

    fname = asm_core.prompt_select(files, 'assembly source')
    print(f'Assembling: {fname}')

    with open(fname, 'r', encoding='utf-8') as f:
        text = f.read()

    try:
        tapes_bin = asm_core.assemble(text)
    except ValueError as e:
        print(f'Assembly error: {e}')
        sys.exit(1)

    output = fname.replace('.mmlang', '.mmbin')
    asm_core.write_mmbin(tapes_bin, output)
    print(f'Assembly complete -> {output}')

    for label in sorted(tapes_bin.keys()):
        ba = tapes_bin[label]
        instr_count = len(ba) // 4
        print(f'  Tape #{label}: {instr_count} instructions')


if __name__ == '__main__':
    main()
