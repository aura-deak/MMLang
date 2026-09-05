# MMLang

mobius-programming-machine-language

[中文文档](README_zh-cn.md)

New machine, and new esolang

Integrates Turing machine, von Neumann machine, Harvard architecture, BrainFuck, some interesting new features, and some weird things. I created it while exploring the history of computer development.

This machine is called the Mobius machine, and its dedicated programming language is called the Mobius machine programming language.

I find it hard to believe that this damn thing is Turing complete. (Said by Blue Big Fish; I really don't want to verify it myself, but if you are interested, you can research it on your own.)

## Mobius Machine

The Mobius machine is a modified Turing machine. The read/write head moves bidirectionally on an infinitely long digital tape.

Instructions are fed through the tape; the tape is unidirectional and sequential, read-only. Program looping is achieved by physically connecting the two ends of the tape; this looping is optional.

The tape has a sequence. When a tape‑switch instruction is executed, the machine halts, retains the current read/write head position and data tape data, switches to the next tape in the scheduling queue and starts reading from the beginning, while the PC state of the previous tape is discarded.

The tape‑switch sequence is cyclic. For example, with three tapes, switching follows the order 1, 2, 3, 1. If there is only a single tape, executing the tape‑switch instruction means restarting from the beginning of the same tape.

Before the program starts, any number of tapes can be inserted into the queue. After the program starts, only the program itself can add tapes to the queue.

It supports cutting the current output tape from the right side of the read/write head, taking the left part of the cut tape as a new program tape and inserting it after the current tape in the sequence. At this time, there is no tape on the read/write head, and a right‑shift instruction must be executed.

## Mobius Machine Programming Language

| Mnemonic | Binary | Description                                                                                                                                                                                                                                                                                                                                                                               |
| :------- | :----- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `>`      | `0000` | Move data read/write head one cell to the right                                                                                                                                                                                                                                                                                                                                           |
| `<`      | `0001` | Move data read/write head one cell to the left                                                                                                                                                                                                                                                                                                                                            |
| `x`      | `0010` | Flip the current data cell (0 becomes 1, 1 becomes 0)                                                                                                                                                                                                                                                                                                                                     |
| `f`      | `0011` | If the current cell is 0, execute the next instruction normally; if 1, skip the next instruction (PC+2)                                                                                                                                                                                                                                                                                   |
| `s`      | `0100` | Tape‑switch halt: suspend the current tape, discard PC, switch to the next tape in the scheduling queue (new tape reads from beginning); data tape and read/write head position are fully preserved                                                                                                                                                                                       |
| `b`      | `0101` | Global halt: terminate the entire system, cut the current entire data tape from the right side of the read/write head, take the left part of the cut tape as the final computation result output                                                                                                                                                                                          |
| `p`      | `0110` | Snapshot cut: truncate the data tape at the read/write head, use the left portion as a new program tape, insert the new tape immediately after the current tape in the scheduling queue; the remaining data tape is the right portion and the data pointer is reset to zero                                                                                                               |
| `n`      | `0111` | No operation                                                                                                                                                                                                                                                                                                                                                                              |
| `l`      | `1000` | **Only at the end of a tape**: if this instruction appears at the end on a physical machine, these 4 bits should be trimmed off, and the head of the tape should be spliced to the tail to form a physical loop (at runtime, when PC reaches the end it automatically returns to the beginning). In a virtual machine, this instruction is retained and its effect is to reset PC to zero |
| `r`      | `1001` | Rewind instruction: after execution, rewind to the beginning of the data tape, which makes memory addressing possible. **Note:** **`p`** **may change the position of data because cutting the tape shortens it and changes the origin**                                                                                                                                                  |

Case‑sensitive. Anything not in the instruction set is treated as a comment.

Use `[?]` to denote the read/write head; examples are shown below.

**b instruction**:\
Original data: `1111 11[1]0 000`\
Output data: `1111 111`, i.e., the right side is discarded.

**p instruction**:\
Original data: `0000 0111 011[1] 1000`\
Snapshot (new program tape): `0000 0111 0111`, i.e., `>nn`\
Remaining data tape after execution: `1000`. Because the original dp now points past the end of the truncated tape, dp is automatically reset to zero (read/write head is restored to the beginning of the remaining data tape). Example state after p completes: `[1]000`.

### Assembly‑time Preprocessing Special Syntax

| Symbol | Purpose                                                                                                            |
| :----- | :----------------------------------------------------------------------------------------------------------------- |
| `*`    | Repetition syntax. Expanded during preprocessing, e.g., `>*1024` expands to 1024 `>` characters.                   |
| `#0`   | Tape label, appears in `.mmlang` and `.mmbin` files, used to distinguish tapes. Labels start from 0 and increment. |

## Toolchain Usage

### Dependency Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Only `bitarray` is required as a third‑party library.

### Files

| File                     | Purpose                                                                        |
| :----------------------- | :----------------------------------------------------------------------------- |
| `asm.py` / `asm_core.py` | Assembler: converts `.mmlang` source to `.mmbin`                               |
| `run.py` / `vm_core.py`  | Executor: loads `.mmbin` and simulates the machine                             |
| `debug.py`               | Single‑step debugger: visual tape state, Enter to step                         |
| `common.py`              | Shared module: instruction encoding table, disassembly table, bitarray helpers |
| `data_tape_maker.py`     | Data tape generator: user‑editable custom initial tape logic                   |
| `test/`                  | Unit tests using Python's stdlib `unittest`; covers all 10 instructions        |

### Assemble `.mmlang` → `.mmbin`

```bash
python3 asm.py
```

Scans the current directory for `.mmlang` files; if exactly one is found, it is assembled directly; if multiple are found, you are prompted to select one by number. Output: a `.mmbin` file with the same name.

### Execute `.mmbin`

```bash
python3 run.py
```

Scans the current directory for a `.mmbin` file and executes it. When the `b` instruction halts the machine, the truncated binary result sequence is printed.

### Single‑step Debugging

```bash
python3 debug.py
```

Each Enter key press executes one instruction. Prints the disassembly state of all program tapes, the data tape, and the current PC / DP values.

### Custom Data Tape

Edit `data_tape_maker.py` and change the return value of `make(dp)` to customise the initial tape logic:

```python
# Returns the parity of the Fibonacci sequence
def make(dp):
    a, b = 0, 1
    for _ in range(dp):
        a, b = b, a + b
    return a % 2
```

The default implementation returns an all‑zero tape.

### Hello World Example

Save the Hello World source from this README as `hello.mmlang`, then:

```bash
python3 asm.py    # produces hello.mmbin
python3 run.py    # executes and prints the bit sequence
```

The output bit sequence, grouped every 8 bits, corresponds to the ASCII bytes of `Hello World`.

### Running Tests

Unit tests live under `test/` and use Python's standard `unittest` — no extra dependencies required. They cover the assembler, the executor, all 10 instructions, and edge cases. 60 tests total.

```bash
# Discover and run all (recommended)
python3 -m unittest discover -s test

# Run assembler / executor tests separately
python3 test/test_asm.py
python3 test/test_vm.py

# Verbose mode
python3 -m unittest discover -s test -v
```

When everything passes, expect output like:

```
Ran 60 tests in 0.004s
OK
```

## Demo Programs

### Zero out all cells on a chaotic data tape

```
#0
f x x > l
```

### Simple two‑tape infinite loop demo

Used to demonstrate multi‑tape writing and the `s` instruction.

```
#0
ns
#1
ns
```

### Hello World ASCII Encoding Output

```
YES, THIS PROGRAM OUTPUTS THE ENCODING DIRECTLY. IS THERE A BETTER SOLUTION?
EACH LINE REPRESENTS A LETTER OR SPACE.
#0
>x>>>x>*4
>x>x>>>x>>x>
>x>x>>x>x>>>
>x>x>>x>x>>>
>x>x>>x>x>x>x>
>>x>*6
>x>>x>>x>x>x>
>x>x>>x>x>x>x>
>x>x>x>>>x>>
>x>x>>x>x>>>
>x>x>>>x>*4
b
```

