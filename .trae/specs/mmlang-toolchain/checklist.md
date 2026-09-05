# MMLang 工具链 - 验证清单

## 汇编器

- [x] CHK-A1: asm.py 能发现当前目录 .mmlang 文件，单文件自动使用
- [x] CHK-A2: asm.py 遇到多文件时列出编号让用户选择
- [x] CHK-A3: `>*5` 等重复语法正确展开
- [x] CHK-A4: 非指令字符被正确忽略为注释；有效指令字符仍被收集
- [x] CHK-A5: 纸带 `#N` 标签被保留并用于切分
- [x] CHK-A6: 汇编后生成的 .mmbin 文件格式正确（#N 标签 + 每行 8 bit）
- [x] CHK-A7: README 中"双纸带循环"示例汇编后正确生成两个纸带
- [x] CHK-A8: README 中"清零程序"示例汇编后正确生成
- [x] CHK-A9: README 中"Hello World"示例汇编后正确生成
- [x] CHK-A10: 指令编码表与 README_zh-cn.md 完全一致（10 条指令，4 bit）

## 执行器

- [x] CHK-E1: run.py 能发现 .mmbin 文件并加载到 cmd_tapes
- [x] CHK-E2: > 指令使 dp++
- [x] CHK-E3: < 指令使 dp--；若 dp 变为负数则报错退出
- [x] CHK-E3a: < 指令使 dp 变为负数时打印中文错误信息并退出
- [x] CHK-E4: x 指令翻转 data_tape[dp]
- [x] CHK-E5: f 指令条件跳转（data_tape[dp]==0 → 下一条；==1 → 跳过下一条）
- [x] CHK-E6: s 指令切换到队列下一条程序纸带（pc=0，data_tape/dp 保留）
- [x] CHK-E7: b 指令全局停机，输出 data_tape[0:dp]
- [x] CHK-E8: p 指令截断 data_tape 左侧为新纸带插入队列当前位置之后，当前纸带继续；若截断后 data_tape 为空，dp 自动 +1
- [x] CHK-E8a: p 指令截断后 data_tape 为空时，dp 自动 +1
- [x] CHK-E9: n 指令空操作
- [x] CHK-E10: l 指令使 pc=0
- [x] CHK-E11: r 指令使 dp=0
- [x] CHK-E12: dp 超出 data_tape 时调用 data_tape_maker 扩展
- [x] CHK-E13: 双纸带循环示例（ns/ns）可持续切换纸带不少于 100 次
- [x] CHK-E14: 清零程序示例可正确运行
- [x] CHK-E15: Hello World 示例汇编并执行后 b 指令输出正确二进制序列

## 调试器

- [x] CHK-D1: debug.py 正确加载 .mmbin 并初始化状态
- [x] CHK-D2: 选中纸带即将执行的指令用 `[...]` 标记
- [x] CHK-D3: 纸带以 4 bit 为单位反汇编，非法指令显示 `?`
- [x] CHK-D4: 指令位置 0-5 时显示含自身在内的 10 条
- [x] CHK-D5: 指令位置 >=6 时显示前后各 5 条（含省略号）
- [x] CHK-D6: 未选中纸带显示 10 条指令
- [x] CHK-D7: data_tape 显示包含 dp 位置的左右位
- [x] CHK-D8: pc 和 dp 当前值正确显示
- [x] CHK-D9: 按 Enter 单步执行
- [x] CHK-D10: 连续快速按 Enter（或长按）触发快速连续执行（用户可手动 Enter 连续调用）

## data_tape_maker

- [x] CHK-M1: 默认 make(dp) 返回 0
- [x] CHK-M2: 修改 make(dp) 返回自定义值后，执行器 data_tape 按新逻辑扩展

## 代码质量

- [x] CHK-Q1: 外部依赖仅为 `bitarray`（需 `pip install bitarray`），不引入其他第三方库
- [x] CHK-Q2: 错误信息使用中文
- [x] CHK-Q3: 空目录（无 .mmlang / .mmbin）时输出友好提示后退出
- [x] CHK-Q4: 共享模块 common.py 包含指令编码表/解码表
- [x] CHK-Q5: 汇编器、执行器、调试器脚本命名遵循 asm.py / run.py / debug.py
