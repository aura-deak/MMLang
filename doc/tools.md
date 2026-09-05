# 工具链用法

## 依赖安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

仅需 `bitarray` 一个第三方库。

### 文件说明

| 文件                       | 用途                                       |
| :----------------------- | :--------------------------------------- |
| `asm.py` / `asm_core.py` | 汇编器：将 `.mmlang` 源码转换为 `.mmbin`           |
| `run.py` / `vm_core.py`  | 执行器：加载 `.mmbin` 并模拟运行                    |
| `debug.py`               | 单步调试器：可视化纸带状态，Enter 键逐步执行                |
| `common.py`              | 共享模块：指令编码表、反汇编表、bitarray 工具函数            |
| `data_tape_maker.py`     | 数据纸带生成器：用户可自定义初始纸带逻辑                     |
| `test/`                  | 单元测试：使用 Python 标准 `unittest`，覆盖全部 10 条指令 |

## 汇编 `.mmlang` → `.mmbin`

```bash
python3 asm.py
```

扫描当前目录下所有 `.mmlang` 文件；若唯一则直接汇编，若多个则提示输入序号选择。输出同名 `.mmbin` 文件。


## 执行 `.mmbin`

```bash
python3 run.py
```

扫描当前目录下 `.mmbin` 文件并执行。遇到 `b` 指令停机时，输出截断后的二进制结果序列。

## 单步调试

```bash
python3 debug.py
```

每次按 Enter 执行一条指令，打印所有程序纸带的反汇编状态、数据纸带、当前 PC 和 DP。