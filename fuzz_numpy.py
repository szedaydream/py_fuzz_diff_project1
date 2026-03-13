import atheris
# import atheris_libprotobuf_mutator  # 可选，用于结构化变异，此处不使用
import sys
import numpy as np
import random

# 定义一个函数，用于根据输入字节生成随机的 NumPy 数组
def generate_random_array(data: atheris.FuzzedDataProvider, max_dims=3, max_size=32):
    """根据输入的随机字节生成一个 NumPy 数组"""
    dtype_choices = [np.int32, np.int64, np.float32, np.float64, np.bool_, np.complex64, np.complex128]
    dtype = data.PickValueInList(dtype_choices)

    # 随机生成形状，确保总元素数不超过 max_size^max_dims 以避免内存爆炸
    ndim = data.ConsumeIntInRange(0, max_dims)
    shape = []
    total_elements = 1
    for _ in range(ndim):
        dim = data.ConsumeIntInRange(0, max_size)
        shape.append(dim)
        total_elements *= max(dim, 1)  # 防止 0 导致乘积为 0
        if total_elements > 1024:  # 限制最大元素数
            # 若过大，提前结束并降级为较小形状
            shape = [min(s, 4) for s in shape]
            break

    # 生成数据
    if dtype == np.bool_:
        arr_data = [data.ConsumeBool() for _ in range(total_elements)]
    elif dtype in (np.int32, np.int64):
        arr_data = [data.ConsumeInt(4) for _ in range(total_elements)]  # 4 字节有符号
    elif dtype in (np.float32, np.float64):
        arr_data = [data.ConsumeFloat() for _ in range(total_elements)]
    elif dtype in (np.complex64, np.complex128):
        arr_data = [complex(data.ConsumeFloat(), data.ConsumeFloat()) for _ in range(total_elements)]
    else:
        arr_data = [0] * total_elements

    # 重塑为指定形状，如果 total_elements 与形状乘积不匹配则调整形状
    try:
        arr = np.array(arr_data, dtype=dtype).reshape(shape)
    except ValueError:
        # 如果 reshape 失败（例如元素数不匹配），返回一个标量或一维数组
        arr = np.array(arr_data[:1], dtype=dtype)
    return arr

# 模糊测试的入口函数
def TestOneInput(data):
    fdp = atheris.FuzzedDataProvider(data)

    # 随机选择要测试的 NumPy 函数或方法
    operations = [
        ("np.sum", lambda x: np.sum(x)),
        ("np.mean", lambda x: np.mean(x)),
        ("np.max", lambda x: np.max(x)),
        ("np.min", lambda x: np.min(x)),
        ("np.argmax", lambda x: np.argmax(x)),
        ("np.argmin", lambda x: np.argmin(x)),
        ("np.sqrt", lambda x: np.sqrt(np.abs(x))),  # 避免负数开方，但允许异常
        ("np.square", lambda x: np.square(x)),
        ("np.log", lambda x: np.log(np.abs(x) + 1e-10)),
        ("np.exp", lambda x: np.exp(x)),
        ("np.dot", lambda x: np.dot(x, x.T) if x.ndim >= 1 and x.size > 0 else None),
        ("np.reshape", lambda x: x.reshape((-1,)) if x.size > 0 else x),
        ("np.transpose", lambda x: np.transpose(x)),
        ("np.concatenate", lambda x: np.concatenate([x, x]) if x.size > 0 else x),
        ("np.linalg.inv", lambda x: np.linalg.inv(x) if x.ndim == 2 and x.shape[0] == x.shape[1] and x.size > 0 else None),
    ]
    op_name, op_func = fdp.PickValueInList(operations)

    # 生成输入数组（可能多个）
    arr = generate_random_array(fdp)
    if arr.size == 0:
        return  # 跳过空数组，但也可以测试

    # 调用操作并捕获异常
    try:
        result = op_func(arr)
        # 可以添加一些简单断言，例如确保结果不是 NaN（如果应该不是）
        if op_name in ("np.sum", "np.mean", "np.max", "np.min") and np.issubdtype(arr.dtype, np.floating):
            if np.isnan(result):
                # 不是错误，但可以记录覆盖率信息
                pass
    except (ValueError, TypeError, np.linalg.LinAlgError, ZeroDivisionError) as e:
        # 这些是预期的异常，不是崩溃，可以忽略
        pass
    except Exception as e:
        # 其他未预料到的异常，触发崩溃报告
        raise e

# 初始化 Atheris
def main():
    # 设置覆盖率跟踪（针对 Python 代码）
    atheris.Setup(sys.argv, TestOneInput)
    # 启用 Python 覆盖跟踪（C 扩展的覆盖需要编译时插桩，此处仅跟踪 Python 级代码）
    atheris.instrument_all()
    atheris.Fuzz()

if __name__ == "__main__":
    main()
