# MMLang 工具链 - 实施计划

## [x] Task 1: 创建 data_tape_maker.py 和共享 bitarray 工具模块
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 创建 `data_tape_maker.py`，提供 `make(dp)` 函数（默认返回 0）
  - 创建共享模块 `common.py`，封装 `bitarray` 库（`pip install bitarray`）用于程序纸带和数据纸带的高效位操作，以及指令编码表/反汇编表
  - 指令编码表：`{'>': '0000', '<': '0001', 'x': '0010', 'f': '0011', 's': '0100', 'b': '0101', 'p': '0110', 'n': '0111', 'l': '1000', 'r': '1001'}`
  - 反汇编表为上述映射的反向
- **Acceptance Criteria Addressed**: AC-5, AC-12
- **Test Requirements**:
  - `programmatic` TR-1.1: `data_tape_maker.make(任意整数)` 返回 0 或 1 ✅
  - `programmatic` TR-1.2: 共享模块的编码表/解码表对全部 10 条指令双向一致 ✅
- **Notes**: data_tape_maker.py 设计为用户可自由修改，保持最简

## [x] Task 2: 实现汇编器 core + asm.py 入口
- **Priority**: P0
- **Depends On**: Task 1
- **Description**:
  - 创建 `asm_core.py` 模块：文件发现/选择逻辑、重复语法展开、指令过滤注释、纸带切分、二进制编码
  - 创建 `asm.py` 作为 CLI 入口，调用 asm_core
  - 重复语法展开规则：扫描所有 `<助记符>*<数字>` 形式，替换为对应数量的助记符
  - .mmbin 输出格式：按纸带顺序，先写 `#N`，然后每行 8 bit（两条指令的二进制拼接）
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-4, AC-5
- **Test Requirements**:
  - `programmatic` TR-2.1: 多纸带文件（如 README 双纸带示例）汇编后 .mmbin 内容正确 ✅
  - `programmatic` TR-2.2: 含重复语法的程序（如 `>*1024`）展开后指令数正确 ✅
  - `programmatic` TR-2.3: 汇编器拒绝纸带编号跳号（如 #0, #2）并给出错误 ✅
  - `programmatic` TR-2.4: 非指令字符正确忽略为注释，有效指令字符（如注释文字中的 s/n/p）仍被收集为有效指令 ✅
- **Notes**: 重复语法正则需考虑边界（如 `>*1024` 不是 `>* 1024`）

## [x] Task 3: 实现执行器 core + run.py 入口
- **Priority**: P0
- **Depends On**: Task 1
- **Description**:
  - 创建 `vm_core.py` 模块：.mmbin 解析、cmd_tapes 调度队列、状态管理（pc, dp, data_tape）、10 条指令分发执行
  - 创建 `run.py` 作为 CLI 入口
  - .mmbin 解析：按 `#N` 标签切分，每行 8 bit 拼接到对应纸带
  - dp 扩展逻辑：每步执行前检查 `dp+5 > len(data_tape)`，是则循环调用 `data_tape_maker.make(len(data_tape))` 并 append 到 data_tape，直到满足条件
  - 指令语义严格遵循 README：
    - `<` 指令使 dp 变为负数时报错退出
    - `p` 指令截断 data_tape[0:dp] 为新程序纸带插入 queue 当前位置之后，data_tape 截断为 [0:dp]，当前纸带继续运行；若截断后 data_tape 为空，dp 自动 +1
  - 其他指令：`b` 截断 data_tape[0:dp] 输出并停机；`f` 条件跳转（data_tape[dp]==0 → pc++，==1 → pc+=2）；`l` pc 归零；`r` dp=0；`s` 切换到 queue 下一条纸带 pc=0

- **Acceptance Criteria Addressed**: AC-6, AC-7, AC-8
- **Test Requirements**:
  - `programmatic` TR-3.1: 10 条指令各自在最小测试程序中行为正确（pc/dp/data_tape 变化符合预期） ✅
  - `programmatic` TR-3.2: s 指令在双纸带程序中正确切换队列 ✅
  - `programmatic` TR-3.3: b 指令正确截断并返回 data_tape[0:dp] ✅
  - `programmatic` TR-3.4: p 指令截断生成的新纸带插入队列位置正确 ✅
  - `programmatic` TR-3.5: f 指令条件跳转逻辑正确 ✅
  - `programmatic` TR-3.6: p 指令截断空纸带时 dp 自动 +1 ✅
  - `programmatic` TR-3.7: `<` 指令使 dp 变为负数时报错退出 ✅

## [x] Task 4: 实现调试器 core + debug.py 入口
- **Priority**: P1
- **Depends On**: Task 3
- **Description**:
  - 创建 `debug.py`，复用 vm_core 的加载和执行单步逻辑
  - 纸带可视化：根据 pc 位置反汇编，0~5 位显示含自身 10 条；>=6 位前后各 5 条 + 自身 = 11 条 + 省略号
  - 反汇编：4 bit 单位，非法指令或位数不足显示 `?`
  - data_tape 显示：dp 位置左右各 8 bit
  - 交互：每步后打印状态，按 Enter 执行下一步

- **Acceptance Criteria Addressed**: AC-10, AC-11
- **Test Requirements**:
  - `human-judgement` TR-4.1: 调试显示格式与拓展设计.md 示例一致 ✅
  - `programmatic` TR-4.2: 非法二进制（1111）显示 `?` ✅
  - `programmatic` TR-4.3: 多纸带调试未选中纸带显示 10 条 ✅

## [x] Task 5: 端到端测试与 README 示例验证
- **Priority**: P1
- **Depends On**: Task 2, Task 3, Task 4
- **Description**:
  - 汇编 README 中的三个演示程序
  - 执行验证
  - Hello World 示例 b 指令输出二进制序列 `01001000011001010110110001101100011011110010000001010111011011110111001001101100011001000` → ASCII 为 "Hello World" ✅

- **Acceptance Criteria Addressed**: AC-9, AC-13
- **Test Requirements**:
  - `programmatic` TR-5.1: 双纸带示例汇编后执行超过 100 步无死锁 ✅
  - `programmatic` TR-5.2: 清零程序可正常运行（无 b 则持续循环）✅
  - `programmatic` TR-5.3: Hello World 汇编 + 执行，b 指令输出 ASCII 为 "Hello World" ✅
