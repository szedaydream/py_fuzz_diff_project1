# Python库函数差分模糊测试项目（Atheris）

本项目使用 Google 的 [Atheris](https://github.com/google/atheris) 对 NumPy 库进行覆盖率引导的模糊测试。
本项目创新实现了：
- **智能差分比较器**：对结果进行细粒度分类（异常类型、浮点容差、结构差异等）。
- **反馈式语料库增强**：将触发差异的输入自动加入语料库，引导模糊测试高效探索“有争议”区域。

## 使用方法

1. 安装依赖
   pip install -r requirements.txt

2. 运行模糊测试
   python fuzzer_numpy_vs_math.py corpus/ -runs=100000
   按 Ctrl+C 停止。

3. 分析结果
   python analyzer_numpy_vs_math.py

4. 最小化差异输入（本项目未选用）
   python minimizer.py --file input.txt

5. 可用 make clean 语句清除当前运行出的数据
