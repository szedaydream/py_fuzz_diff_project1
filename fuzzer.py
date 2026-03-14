#!/usr/bin/env python3
import atheris
import sys
import json
import ujson
from utils import deep_compare_with_details, save_difference, DiffCategory
from config import LIB_A_NAME, LIB_B_NAME, CORPUS_DIR, FUZZ_RUNS

def compare_libraries(input_bytes):
    """差分测试核心逻辑"""
    # 1. 解码为字符串
    try:
        test_string = input_bytes.decode('utf-8')
    except UnicodeDecodeError:
        return

    # 2. 分别调用两个库
    # 库 A (json)
    try:
        result_a = json.loads(test_string)
        res_a_str = repr(result_a)
    except Exception as e:
        result_a = None
        res_a_str = f"EXCEPTION: {type(e).__name__}: {e}"

    # 库 B (ujson)
    try:
        result_b = ujson.loads(test_string)
        res_b_str = repr(result_b)
    except Exception as e:
        result_b = None
        res_b_str = f"EXCEPTION: {type(e).__name__}: {e}"

    # 3. 差分比较
    # 情况1：一个成功，一个失败
    if (result_a is None) != (result_b is None):
        category = DiffCategory.ONE_FAILS.value
        save_difference(test_string, res_a_str, res_b_str, LIB_A_NAME, LIB_B_NAME, category=category)
        return

    # 情况2：都成功但结果不同
    if result_a is not None and result_b is not None:
        ok, cat, path = deep_compare_with_details(result_a, result_b)
        if not ok:
            category = cat.value if cat else DiffCategory.UNKNOWN.value
            save_difference(test_string, res_a_str, res_b_str, LIB_A_NAME, LIB_B_NAME, 
                           category=category, detail_path=path)
        return

    # 情况3：都失败但异常信息不同
    if result_a is None and result_b is None:
        if res_a_str != res_b_str:
            # 进一步判断异常类型是否相同（可选项）
            # 简单将两者都失败且异常信息不同归为 exception_message
            category = DiffCategory.EXCEPTION_MESSAGE.value
            save_difference(test_string, res_a_str, res_b_str, LIB_A_NAME, LIB_B_NAME, category=category)
        return

def TestOneInput(data):
    compare_libraries(data)

if __name__ == "__main__":
    print("=" * 60)
    print(f"差分模糊测试：{LIB_A_NAME} vs {LIB_B_NAME}")
    print("按 Ctrl+C 停止测试")
    print("=" * 60)

    # 确保语料库目录存在
    from utils import ensure_dir
    ensure_dir(CORPUS_DIR)

    # 插桩待测库
    with atheris.instrument_imports():
        import json
        import ujson

    # 设置模糊测试参数，支持语料库目录
    atheris.Setup(sys.argv, TestOneInput)
    if FUZZ_RUNS > 0:
        atheris.Fuzz()
    else:
        atheris.Fuzz()  # 无限运行
