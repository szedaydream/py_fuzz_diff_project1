# NumPy 模糊测试项目（Atheris）

本项目使用 Google 的 [Atheris](https://github.com/google/atheris) 对 NumPy 库进行覆盖率引导的模糊测试。

## 使用方法

1.  安装依赖：
    pip install -r requirements.txt

2.  运行模糊测试：
    python fuzz_numpy.py

3.  可选参数（如指定语料库目录）：
    python fuzz_numpy.py -runs=1000000 -dict=dict.txt
