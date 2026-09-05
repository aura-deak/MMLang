# MMLang 工具链 - 产品需求文档

## Overview
- **Summary**: 为莫比乌斯机（Mobius Machine）实现一套完整的编程语言工具链，包括汇编器（.mmlang → .mmbin）、执行器（模拟器）、单步调试器和可配置的数据纸带生成器。这是一个从零开始的项目，项目目录中目前只有设计文档，没有任何实现代码。
- **Purpose**: 将莫比乌斯机这一 esolang 的设计文档转化为可运行的工具链，使设计者和爱好者能够编写、汇编、执行和调试莫比乌斯机程序。
- **Target Users**: MMLang 语言设计者、esolang 爱好者、计算理论学习者。

## Goals
- 实现能将 .mmlang 汇编源码转换为 .mmbin 二进制指令文件的汇编器
- 实现能加载 .mmbin 并模拟莫比乌斯机运行的执行器，完整支持全部 10 条指令（>、<、x、f、s、b、p、n、l、r）
- 实现依赖执行器的单步调试器，提供纸带状态可视化、pc/dp 跟踪、手动单步/快速运行模式
- 提供 data_tape_maker.py 接口让用户自定义初始数据纸带生成逻辑
- 所有组件支持从当前工作目录自动发现对应文件，多文件时交互选择

## Non-Goals (Out of Scope)
- 不实现编辑器集成（VSCode 插件、语法高亮等）
- 不实现图形化 IDE（Tkinter/PyQt 界面）
- 不实现莫比乌斯机的硬件仿真
- 不提供跨语言绑定（如 JS/WASM 移植）
- 不添加文档中未定义的新指令或新语法

## Background & Context
- 莫比乌斯机是一种改版图灵机，融合了图灵机、冯·诺伊曼机、哈佛架构、BrainFuck 等特性
- 指令集共 10 条，每条 4 bit（半字节）：`>`(0000)、`<`(0001)、`x`(0010)、`f`(0011)、`s`(0100)、`b`(0101)、`p`(0110)、`n`(0111)、`l`(1000)、`r`(1001)
- 纸带分为两类：**程序纸带**（cmd_tapes，只读，单向顺序执行，支持 s 换带和 b 停机）和**数据纸带**（data_tape，可读写，双向移动）
- 多纸带调度为循环队列，s 指令切换到下一条程序纸带并丢失上一条的 PC；p 指令从数据纸带截断生成新的程序纸带插入队列
- l 指令在虚拟机中作为 PC 归零使用（模拟物理闭环）
- 汇编期支持 `>*5` 形式的重复语法展开，支持 `#0` 标签标注纸带序号

## Functional Requirements

### 汇编器 (Assembler)
- **FR-A1**: 扫描当前目录下所有 `.mmlang` 文件；若唯一则直接使用，若多个则列出让用户输入序号选择
- **FR-A2**: 按 `#num` 标签切分纸带，纸带编号必须从 0 开始递增
- **FR-A3**: 丢弃换行和注释（不在指令集内的字符视为注释），但保留 `#num` 标签
- **FR-A4**: 先展开 `*N` 重复语法（如 `>*1024` → 1024 个 `>`）
- **FR-A5**: 按汇编码表将每个助记符转为 4 bit 二进制
- **FR-A6**: 将结果写入同名 `.mmbin` 文件，格式为 `#num` 后跟 8 bit（两个指令一行）二进制表示
- **FR-A7**: 对非法助记符、纸带编号错误等情况给出清晰的错误提示

### 执行器 (Executor)
- **FR-E1**: 扫描当前目录下所有 `.mmbin` 文件；若唯一则直接使用，若多个则列出让用户选择
- **FR-E2**: 解析 `.mmbin` 文件，加载到 `cmd_tapes` 字典中（key 为 `#num`，value 为 bitarray）
- **FR-E3**: 维护程序状态：cmd_tapes 调度队列、当前纸带、pc（指令序数，1 pc = 4 bit）、data_tape（bitarray）、dp（读写头位置，1 dp = 1 bit）
- **FR-E4**: 当 dp 超出当前 data_tape 长度时，调用 `./data_tape_maker.py` 的 `make(dp)` 函数扩展 data_tape，直到 dp 处于有效范围
- **FR-E5**: 完整实现 10 条指令语义：
  - `>` (0000): dp++
  - `<` (0001): dp--
  - `x` (0010): 翻转 data_tape[dp]
  - `f` (0011): 若 data_tape[dp]==0 则 pc++，否则 pc+=2
  - `s` (0100): 切换到队列下一条程序纸带，新纸带从头执行（pc=0），data_tape 和 dp 不变
  - `b` (0101): 全局停机，输出 data_tape[0:dp] 作为最终结果
  - `p` (0110): 截断 data_tape[0:dp] 作为新程序纸带插入队列当前纸带之后，data_tape 截断为 [0:dp]，当前纸带继续运行；若截断后 data_tape 为空，dp 自动 +1
  - `n` (0111): 空操作，pc++
  - `l` (1000): pc=0（循环到纸带开头）
  - `r` (1001): dp=0（数据纸带回退到开头）
- **FR-E6**: 遇到无指令可执行（pc 越界且无 l 指令循环）时，行为与 l 一致（pc 归零），保证程序不会意外崩溃
- **FR-E7**: 执行完成后返回最终 data_tape[0:dp] 的二进制表示

### 单步调试器 (Debugger)
- **FR-D1**: 依赖执行器模块，复用其 .mmbin 文件发现/选择逻辑
- **FR-D2**: 每次执行一步指令，在控制台显示所有纸带的可视化状态
- **FR-D3**: 显示格式为：选中纸带用 `[` `]` 标记即将执行的指令；纸带以 4 bit 为单位反汇编，未知指令或位数不足显示为 `?`
- **FR-D4**: 根据指令位置显示不同长度：0-5 位显示包含在内的 10 条指令；>=6 位显示前后各 5 条；未选中纸带显示 10 条
- **FR-D5**: 显示 data_tape 的可视化（包含 dp 位置的左右各若干位）、pc、dp 当前值
- **FR-D6**: 交互支持：按 Enter 单步执行；按住 Enter 连续执行（快速运行）
- **FR-D7**: 完整调试外观遵循拓展设计.md 中的示例格式

### data_tape_maker.py
- **FR-M1**: 提供 `make(dp)` 函数接口，参数是需要生成的 bit 索引位置，返回该位置的值（0 或 1）
- **FR-M2**: 默认实现返回 0（全 0 纸带）
- **FR-M3**: 用户可自由修改此文件来改变数据纸带生成逻辑

## Non-Functional Requirements
- **NFR-1**: 汇编器和执行器应为独立的可执行脚本（如 `asm.py` 和 `run.py`），便于命令行调用
- **NFR-2**: 调试器应作为第三个独立脚本（如 `debug.py`），复用执行器的核心模块
- **NFR-3**: 代码组织采用模块化设计：核心逻辑（状态管理、指令分发）放入共享模块，汇编器/执行器/调试器作为薄壳调用
- **NFR-4**: bitarray 使用 `bitarray` 第三方库（需 `pip install bitarray`），以提高位操作效率
- **NFR-5**: 错误信息应中文友好（匹配项目文档语言）

## Constraints
- **Technical**: Python 3（项目无现存代码，选择最适合快速原型的语言）
- **Dependencies**: Python 标准库 + `bitarray`（`pip install bitarray`）
- **File naming**: 脚本命名遵循文档暗示（asm/run/debug + data_tape_maker.py）
- **File format**: .mmbin 文件格式遵循拓展设计.md（`#num` + 每行 8 bit）

## Assumptions
- 当前工作目录即项目根目录，汇编器/执行器/调试器均从 cwd 扫描文件
- 纸带编号 #0, #1, ... 必须连续递增，不允许跳号
- .mmbin 文件中每个纸带的二进制总位数必须是 4 的倍数（不足则报错或补 0）
- data_tape_maker.py 需要能被执行器 import，应放在同一目录或可导入路径
- 当没有任何 .mmlang / .mmbin 文件时，工具应打印友好提示并退出

## Acceptance Criteria

### AC-1: 汇编器 - 文件发现与选择
- **Given**: 当前目录存在且仅存在一个 .mmlang 文件
- **When**: 运行汇编器
- **Then**: 自动使用该文件进行汇编，无需交互
- **Verification**: `programmatic`

### AC-2: 汇编器 - 多文件交互选择
- **Given**: 当前目录存在多个 .mmlang 文件
- **When**: 运行汇编器
- **Then**: 打印文件列表让用户输入序号选择
- **Verification**: `programmatic`

### AC-3: 汇编器 - 完整汇编流程
- **Given**: 输入 .mmlang 文件包含纸带标签、指令、重复语法
- **When**: 汇编器执行
- **Then**: 展开重复语法 → 丢弃注释 → 按标签分纸带 → 转二进制 → 生成同名 .mmbin
- **Verification**: `programmatic`

### AC-4: 汇编器 - 重复语法展开
- **Given**: 源码中出现 `>*5`、`x*3`、`f*2` 等
- **When**: 汇编前预处理
- **Then**: 正确展开为对应数量的重复字符（如 `>*5` → `>>>>>`）
- **Verification**: `programmatic`

### AC-5: 汇编器 - 指令编码正确性
- **Given**: 任意合法指令字符
- **When**: 汇编转换
- **Then**: 严格按照 README_zh-cn.md 中的二进制映射表编码
- **Verification**: `programmatic`

### AC-6: 执行器 - .mmbin 加载
- **Given**: 合法的 .mmbin 文件
- **When**: 执行器启动
- **Then**: 正确解析为 cmd_tapes 字典
- **Verification**: `programmatic`

### AC-7: 执行器 - dp 扩展与 data_tape_maker 调用
- **Given**: 程序运行中 dp 超出当前 data_tape 长度
- **When**: 执行器判断 dp+5 > len(data_tape)
- **Then**: 循环调用 data_tape_maker.make(dp) 扩展 data_tape 直到满足条件
- **Verification**: `programmatic`

### AC-8: 执行器 - 10 条指令语义全部正确
- **Given**: 包含每条指令的测试程序
- **When**: 单步执行并跟踪状态变化
- **Then**: pc、dp、data_tape、cmd_tapes 队列的变化与文档描述一致
- **Verification**: `programmatic`

### AC-9: 执行器 - 示例程序可运行
- **Given**: README 中的三个演示程序（清零死循环、双纸带循环、Hello World）
- **When**: 经汇编并执行
- **Then**: 程序执行过程符合文档预期（清零程序可停机、双纸带程序 s 指令切换正常）
- **Verification**: `programmatic`

### AC-10: 调试器 - 显示格式正确性
- **Given**: 正在运行的执行器实例
- **When**: 执行一步后显示状态
- **Then**: 纸带反汇编正确、选中标记 `[]` 位置正确、`?` 标记正确处理未知指令
- **Verification**: `human-judgment`（对照拓展设计.md 的示例格式）

### AC-11: 调试器 - 交互功能
- **Given**: 调试器启动
- **When**: 按 Enter / 按住 Enter
- **Then**: 分别触发单步执行 / 快速连续执行
- **Verification**: `human-judgment`

### AC-12: data_tape_maker.py - 可替换接口
- **Given**: 默认 data_tape_maker.py 返回全 0
- **When**: 用户修改 make(dp) 返回自定义值
- **Then**: 执行器调用后 data_tape 按新逻辑扩展
- **Verification**: `programmatic`

### AC-13: 端到端 - 完整工具链跑通
- **Given**: README 中的 Hello World 示例程序源码
- **When**: 汇编器 → 执行器 → 查看输出
- **Then**: 最终输出的二进制序列与 ASCII 编码对应
- **Verification**: `programmatic`

## Open Questions
- [ ] Hello World 示例的输出是 bit 序列还是需要额外转为 ASCII 显示？文档没有明确输出格式
- [ ] 调试器的"按住 Enter 快速运行"在 Linux 终端中用什么机制检测？需要明确实现方式
- [ ] dp 是否允许为负数？初始状态 dp=0，data_tape 向左移动时应如何处理边界？
- [ ] 当 p 指令截断后 data_tape 变空，此时 dp 位置是否需要调整？
