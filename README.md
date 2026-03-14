# NumPy 模糊测试项目（Atheris）

本项目使用 Google 的 [Atheris](https://github.com/google/atheris) 对 NumPy 库进行覆盖率引导的模糊测试。
本项目创新实现了：
- **智能差分比较器**：对结果进行细粒度分类（异常类型、浮点容差、结构差异等）。
- **反馈式语料库增强**：将触发差异的输入自动加入语料库，引导模糊测试高效探索“有争议”区域。

## 使用方法

1. 安装依赖
   pip install -r requirements.txt

2. 运行模糊测试
   python fuzzer.py corpus/ -runs=10000
   按 Ctrl+C 停止。

3. 分析结果
   python analyzer.py

4. 最小化差异输入（可选）
   python minimizer.py --file input.txt
