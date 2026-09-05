# 运行测试

单元测试位于 `test/` 目录下，使用 Python 标准库 `unittest`，无需安装额外依赖。覆盖汇编器、执行器、全部 10 条指令及边界条件，共 60 个测试用例。

```bash
# 全部发现并运行（推荐）
python3 -m unittest discover -s test

# 分别运行汇编器 / 执行器测试
python3 test/test_asm.py
python3 test/test_vm.py

# 详细模式
python3 -m unittest discover -s test -v
```

如果全部通过，输出类似：

```
Ran 60 tests in 0.004s
OK
```