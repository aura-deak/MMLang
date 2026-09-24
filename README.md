# Mobius Machine & MMLang

这台机器被叫作莫比乌斯机（Mobius Machine），它的专属编程语言被称为莫比乌斯机编程语言（Mobius Machine programming Language）

莫比乌斯机融合了图灵机、冯·诺伊曼机、哈佛架构，等等。

莫比乌斯机的结构极其简单，不需要ALU、寄存器和状态转移表，电子控制部件结构非常简单，却可以实现现代计算机的一些特性，并执行通用计算任务。而代价是让程序员完成本来应当由硬件完成的工作。它可能是最适合从零手搓的图灵机变体之一。

我在探究计算机发展的时候创造了它，它的很多逻辑都来源于历史上真实存在过的那些机器，如首尾相连实现循环的程序纸带、多程序纸带切换、以及那个蛮荒年代里对代码自生成的大胆探索。

理论上，这应当属于一次对计算模型边界的探讨，而不仅仅是创造了一个esolang。

MMLang相比其他的esolang最大的不同在于，**它的困难不是被设计的，而是由它的硬件结构决定的**，它将简陋的硬件结构无抽象地暴露给程序员。

## MMLang文档阅读目录

- [莫比乌斯机概念、MMLang指令集与语法](doc/mobius-machine-and-MMLang.md)
- [工具链用法](doc/tools.md)
- [高级特性、高级编程技巧](doc/advanced.md)
- [程序示例](doc/examples.md)
- [工具链的单元测试](doc/test.md)
- [MMLang 图灵完备性验证报告（AI）](doc/turing-completeness.md)

**必读**：MMLang指令集与语法、工具链用法。或阅读下面的文档快速开始。

## Quick Start

将以hello world为例，展示MMLang的基本用法。

### 安装MMLang工具链

```bash
git clone https://github.com/aura-deak/MMLang.git
cd MMLang
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
或
`yay -S mmlang`

### 编译与执行hello world

```bash
python3 data_tape_maker.py
# 向程序输入hello world，生成hello_world.mmbin
python3 asm.py hello_world.mmlang
python3 run.py hello_world.mmbin
```