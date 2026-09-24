# 工具链用法

## 安装

全局安装为命令行工具（推荐）：

```bash
uv tool install --python-preference only-system .
```

或直接使用 Arch 包管理器：`yay -S mmlang`

### 开发模式

在仓库内直接运行源码，适合开发调试：

```bash
uv sync
uv run python3 asm.py
```


### 文件说明

| 文件                       | 用途                                       |
| :----------------------- | :--------------------------------------- |
| `asm.py` / `asm_core.py` | 汇编器：将 `.mmlang` 源码转换为 `.mmbin`           |
| `run.py` / `vm_core.py`  | 执行器：加载 `.mmbin` 并模拟运行                    |
| `debug.py`               | 单步调试器：可视化程序纸带状态，Enter 键逐步执行                |
| `common.py`              | 共享模块：指令编码表、反汇编表、bitarray 工具函数            |
| `data_tape_maker.py`     | 数据纸带生成器：用户可自定义初始数据纸带逻辑                     |
| `test/`                  | 单元测试：使用 Python 标准 `unittest`，覆盖全部 10 条指令 |

## 文本 → MMLang 源码

```bash
mmlang-text2mm
```

输入一段文本，自动生成对应的 MMLang 源文件。开发模式下使用 `uv run python3 text2mm.py`。

## 汇编 `.mmlang` → `.mmbin`

```bash
mmlang-asm
```

扫描当前目录下所有 `.mmlang` 文件；若唯一则直接汇编，若多个则提示输入序号选择。输出同名 `.mmbin` 文件。开发模式下使用 `uv run python3 asm.py`。

## 执行 `.mmbin`

```bash
mmlang-run
```

扫描当前目录下 `.mmbin` 文件并执行。遇到 `b` 指令停机时，输出截断后的二进制结果序列。开发模式下使用 `uv run python3 run.py`。

## 单步调试

```bash
mmlang-debug
```

每次按 Enter 执行一条指令，打印所有程序纸带的反汇编状态、数据纸带、当前 PC 和 DP。开发模式下使用 `uv run python3 debug.py`。