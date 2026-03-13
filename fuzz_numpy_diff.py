#!/home/sze/numpy_fuzzing/venv/bin/python
import atheris
import sys
import numpy as np
import torch
import os

# -------------------- 辅助函数：生成随机数组 --------------------
def generate_random_array(data: atheris.FuzzedDataProvider, max_dims=3, max_size=32):
    """根据输入的随机字节生成一个 NumPy 数组，支持多种数据类型和形状"""
    dtype_choices = [np.int32, np.int64, np.float32, np.float64, np.bool_, np.complex64, np.complex128]
    dtype = data.PickValueInList(dtype_choices)

    # 随机生成形状，限制总元素数避免内存爆炸
    ndim = data.ConsumeIntInRange(0, max_dims)
    shape = []
    total_elements = 1
    for _ in range(ndim):
        dim = data.ConsumeIntInRange(0, max_size)
        shape.append(dim)
        total_elements *= max(dim, 1)
        if total_elements > 1024:
            shape = [min(s, 4) for s in shape]
            break

    # 生成数据
    if dtype == np.bool_:
        arr_data = [data.ConsumeBool() for _ in range(total_elements)]
    elif dtype in (np.int32, np.int64):
        arr_data = [data.ConsumeInt(4) for _ in range(total_elements)]
    elif dtype in (np.float32, np.float64):
        arr_data = [data.ConsumeFloat() for _ in range(total_elements)]
    elif dtype in (np.complex64, np.complex128):
        arr_data = [complex(data.ConsumeFloat(), data.ConsumeFloat()) for _ in range(total_elements)]
    else:
        arr_data = [0] * total_elements

    try:
        arr = np.array(arr_data, dtype=dtype).reshape(shape)
    except ValueError:
        # reshape 失败时退化为标量或一维数组
        arr = np.array(arr_data[:1], dtype=dtype)
    return arr


# -------------------- 辅助函数：将 NumPy 数组转为 PyTorch 张量 --------------------
def numpy_to_torch(arr):
    """安全地将 NumPy 数组转为 PyTorch 张量（处理不支持的类型）"""
    if arr.dtype == np.complex64:
        arr = arr.astype(np.complex128)  # PyTorch 不支持 complex64
    if arr.dtype == np.complex128:
        # PyTorch 支持 complex128，但需拆分为实部和虚部？这里直接转换
        return torch.from_numpy(arr)
    if arr.dtype == np.bool_:
        return torch.from_numpy(arr.astype(np.uint8))  # bool 转为 uint8
    # 其他数值类型直接转换
    return torch.from_numpy(arr)


# -------------------- 定义待测试的函数对 (NumPy 函数, PyTorch 函数) --------------------
operations = [
    # 基础聚合
    ("sum", 
     lambda x: np.sum(x), 
     lambda x: torch.sum(torch.from_numpy(x)).item()),

    ("mean", 
     lambda x: np.mean(x), 
     lambda x: torch.mean(torch.from_numpy(x).float()).item()),

    ("max", 
     lambda x: np.max(x), 
     lambda x: torch.max(torch.from_numpy(x)).item()),

    ("min", 
     lambda x: np.min(x), 
     lambda x: torch.min(torch.from_numpy(x)).item()),

    # 数学函数
    ("sqrt", 
     lambda x: np.sqrt(np.abs(x)), 
     lambda x: torch.sqrt(torch.abs(torch.from_numpy(x).float()))),

    ("square", 
     lambda x: np.square(x), 
     lambda x: torch.square(torch.from_numpy(x))),

    ("exp", 
     lambda x: np.exp(x), 
     lambda x: torch.exp(torch.from_numpy(x).float())),

    ("log", 
     lambda x: np.log(np.abs(x) + 1e-10), 
     lambda x: torch.log(torch.abs(torch.from_numpy(x).float()) + 1e-10)),

    # 线性代数（仅当输入为二维且可逆时尝试）
    ("dot", 
     lambda x: np.dot(x, x.T) if x.ndim >= 1 and x.size > 0 else None,
     lambda x: torch.mm(x, x.T) if x.ndim == 2 and x.shape[0] == x.shape[1] and x.size(0) > 0 else None),

    ("matmul", 
     lambda x: np.matmul(x, x.T) if x.ndim >= 1 and x.size > 0 else None,
     lambda x: torch.matmul(x, x.T) if x.ndim == 2 and x.size(0) > 0 else None),

    # 其他
    ("reshape", 
     lambda x: x.reshape((-1,)) if x.size > 0 else x,
     lambda x: x.view(-1) if x.numel() > 0 else x),

    ("transpose", 
     lambda x: np.transpose(x),
     lambda x: x.T),

    ("concatenate", 
     lambda x: np.concatenate([x, x]) if x.size > 0 else x,
     lambda x: torch.cat([x, x], dim=0) if x.numel() > 0 else x),
]


# -------------------- 模糊测试入口 --------------------
def TestOneInput(data):
    fdp = atheris.FuzzedDataProvider(data)

    # 随机选择一个操作
    op_name, np_func, torch_func = fdp.PickValueInList(operations)

    # 生成输入数组
    arr = generate_random_array(fdp)
    if arr.size == 0:
        return

    print("Input array:")
    print(arr)

    # 转换为 PyTorch 张量
    try:
        tensor = numpy_to_torch(arr)
    except Exception:
        # 如果转换失败（例如 complex 类型），跳过
        return

    # 调用两个库的函数，并比较结果
    try:
        res_np = np_func(arr)
        res_torch = torch_func(tensor)

        if res_np is None or res_torch is None:
            return

        # 将 PyTorch 结果转为 NumPy 数组以便比较
        if isinstance(res_torch, torch.Tensor):
            res_torch_np = res_torch.detach().cpu().numpy()
        else:
            res_torch_np = np.array(res_torch)

        # 比较两个结果，允许 NaN 相等（equal_nan=True）
        if not np.allclose(res_np, res_torch_np, rtol=1e-4, atol=1e-6, equal_nan=True):
            # 发现差异，保存输入到文件
            diff_dir = "differential_finds"
            os.makedirs(diff_dir, exist_ok=True)
            # 生成唯一文件名（使用操作名和随机数）
            filename = os.path.join(diff_dir, f"diff_{op_name}_{fdp.ConsumeInt(4)}.bin")
            with open(filename, "wb") as f:
                f.write(data)
            # 可选：打印差异信息以便调试
            print(f"\n[DIFF] Operation: {op_name}")
            print(f"NumPy result: {res_np}")
            print(f"PyTorch result: {res_torch_np}")
            print(f"Difference: {np.abs(np.asarray(res_np) - np.asarray(res_torch_np))}")

    except (ValueError, TypeError, np.linalg.LinAlgError, RuntimeError, IndexError, KeyError, ZeroDivisionError) as e:
        # 预期的异常，忽略
        pass
    except Exception as e:
        # 其他未捕获的异常，视为潜在问题，保存输入并继续
        crash_dir = "unexpected_exceptions"
        os.makedirs(crash_dir, exist_ok=True)
        filename = os.path.join(crash_dir, f"crash_{op_name}_{fdp.ConsumeInt(4)}.bin")
        with open(filename, "wb") as f:
            f.write(data)


# -------------------- 主函数 --------------------
def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.instrument_all()
    atheris.Fuzz()

if __name__ == "__main__":
    main()
