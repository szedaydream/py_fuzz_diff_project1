#!/usr/bin/env python3
# fuzzer_numpy.py
import atheris
import sys
import math
import numpy as np
from utils import deep_compare_with_details, save_difference
from config import LIB_A_NAME, LIB_B_NAME, CORPUS_DIR, FUZZ_RUNS

def compare_libraries(input_bytes):
    """
    使用 FuzzedDataProvider 生成随机浮点数，并比较 math.sin 和 numpy.sin 的结果。
    """
    fdp = atheris.FuzzedDataProvider(input_bytes)
    # 生成一个随机浮点数，包括特殊值（NaN, Inf, 0, 负数等）
    x = fdp.ConsumeFloat()  # 参数为字节数，16字节对应 double 范围
    # 可选：生成更多参数，但这里先测试一元函数

    # 调用 math.sin
    try:
        result_math = math.sin(x)
        res_math_str = repr(result_math)
        res_math_obj = result_math
    except Exception as e:
        res_math_obj = None
        res_math_str = f"EXCEPTION: {type(e).__name__}: {e}"

    # 调用 numpy.sin
    try:
        result_numpy = np.sin(x)
        res_numpy_str = repr(result_numpy)
        res_numpy_obj = result_numpy
    except Exception as e:
        res_numpy_obj = None
        res_numpy_str = f"EXCEPTION: {type(e).__name__}: {e}"

    # 差分比较
    # 情况1：一个成功，一个失败
    if (res_math_obj is None) != (res_numpy_obj is None):
        save_difference(str(x), res_math_str, res_numpy_str, LIB_A_NAME, LIB_B_NAME, category="one_fails")
        return

    # 情况2：都成功但结果不同
    if res_math_obj is not None and res_numpy_obj is not None:
        ok, cat, path = deep_compare_with_details(res_math_obj, res_numpy_obj)
        if not ok:
            category = cat.value if cat else "value_mismatch"
            save_difference(str(x), res_math_str, res_numpy_str, LIB_A_NAME, LIB_B_NAME, 
                           category=category, detail_path=path)
        return

    # 情况3：都失败但异常信息不同
    if res_math_obj is None and res_numpy_obj is None:
        if res_math_str != res_numpy_str:
            save_difference(str(x), res_math_str, res_numpy_str, LIB_A_NAME, LIB_B_NAME, category="exception_message")
        return

def TestOneInput(data):
    compare_libraries(data)

if __name__ == "__main__":
    print("=" * 60)
    print(f"差分模糊测试：{LIB_A_NAME} vs {LIB_B_NAME}")
    print("按 Ctrl+C 停止测试")
    print("=" * 60)

    from utils import ensure_dir
    ensure_dir(CORPUS_DIR)

    # 插桩库（注意 numpy 是 C 扩展，插桩可能只覆盖 Python 调用层，但仍可收集覆盖率）
    with atheris.instrument_imports():
        import math
        import numpy as np

    atheris.Setup(sys.argv, TestOneInput)
    if FUZZ_RUNS > 0:
        atheris.Fuzz()
    else:
        atheris.Fuzz()
