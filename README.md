# MMLang
mobius-programming-machine-language

A new machine, and a new esolang.

It merges the Turing machine, the von Neumann machine, the Harvard architecture, BrainFuck, some interesting new features, and some odd stuff. I created it while exploring the history of computing.

This machine is called the Möbius Machine, and its dedicated programming language is called the Möbius Machine Programming Language.

I can hardly believe this thing is Turing-complete. (That's what the big blue fat fish said; I really don't want to verify it myself. If you're interested, feel free to research it.)

## The Möbius Machine
The Möbius Machine is a modified Turing machine whose read/write head moves bidirectionally over an infinitely long tape of digits.

Instructions are fed in via the tape, which is read only, sequentially, and in one direction. Program looping is achieved by physically connecting the two ends of the tape, and this looping is optional.

The tape has a sequence. When an exchange-tape instruction is executed, the machine halts, preserves the current read/write head position and the data tape data, and switches to the next tape, starting to read from the beginning; the PC state of the previous tape is lost.

The tape-exchange sequence is cyclic. For example, in a three-tape sequence, the exchange follows 1, 2, 3, 1. If there is only a single tape, executing an exchange-tape instruction restarts execution of that same tape from the beginning.

Any number of tapes can be inserted into the queue before the program starts; after the program starts, tapes can only be added to the queue by the program itself.

It supports truncating the current output tape from the right of the read/write head, and inserting the left portion of the cut tape, taken as a new program tape, into the position immediately after the current tape. At this point the read/write head has no tape above it, so a right-move instruction must be executed.

## The Möbius Machine Programming Language

| Mnemonic | Binary | Description |
| :--- | :--- | :--- |
| `>` | `0000` | Move the data read/write head one cell to the right |
| `<` | `0001` | Move the data read/write head one cell to the left |
| `x` | `0010` | Flip the current data cell (0 to 1, 1 to 0) |
| `f` | `0011` | If the current cell is 0, execute the next instruction normally; if it is 1, skip the next instruction (PC+2) |
| `s` | `0100` | Tape-exchange halt: suspend the current tape, discard the PC, switch to the next tape in the scheduling queue (start reading the new tape from the beginning); the data tape and the read/write head position are fully preserved |
| `b` | `0101` | Global halt: terminate the whole system, truncate the current entire data tape from the right of the read/write head, and take the left portion of the cut tape as the final computation output |
| `p` | `0110` | Truncate snapshot: truncate from the right of the read/write head, and take the truncated data tape as a new program tape, inserting it into the tape sequence immediately after the current tape; at this point the read/write head has no tape above it, so a move-back instruction must be executed; the current tape continues running unaffected |
| `n` | `0111` | No operation |
| `l` | `1000` | **End of tape only**: **these 4 bits are stripped during loading**, and the head of the tape is spliced to the tail, forming a physical loop (at runtime, the PC automatically wraps back to the beginning when it reaches the end). **This is a marker, not code** |
| `r` | `1001` | Rewind instruction; after execution, it rewinds to the beginning of the data tape, which makes memory addressing possible. **Note: p may change the position of the data, because tape truncation shortens the tape and thus changes the origin** |

Case-sensitive. Anything not in the instruction set is treated as a comment.

Using `[?]` to represent the read/write head, demonstration follows:

**b instruction**:
Original data `1111 11[1]0 000`
Output data `1111 111`, i.e. the right side is discarded

**p command**:
Original data `0000 0111 011[1] 0000`
Output code `0000 0111 0111`, which is `>nn`, i.e. the right side is discarded

## Demonstration programs
### Set all cells of a chaotic data tape to zero
`f x x > l`

### Hello World ASCII encoded output
```
Hello World in ASCII... (output through the b instruction)
```

## Original Chinese README
[README_zh-cn.md](./README_zh-cn.md)