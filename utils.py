import math
import hashlib
import os
from enum import Enum
from config import FLOAT_REL_TOL, DIFF_LOG_FILE, FINGERPRINT_FILE, ENABLE_FEEDBACK_CORPUS, CORPUS_DIR, MAX_CORPUS_FILES

# ========== 差异类别枚举 ==========
class DiffCategory(Enum):
    EXCEPTION_TYPE = "exception_type"          # 异常类型不同
    EXCEPTION_MESSAGE = "exception_message"    # 异常信息不同
    VALUE_MISMATCH = "value_mismatch"          # 值不同（基本类型）
    TYPE_MISMATCH = "type_mismatch"            # 类型不同
    FLOAT_APPROX = "float_approx"              # 浮点数超出容差
    KEY_MISMATCH = "key_mismatch"              # 字典键集合不同
    LENGTH_MISMATCH = "length_mismatch"        # 列表/元组长度不同
    ORDER_MISMATCH = "order_mismatch"          # 顺序不同（有序容器）
    STRUCTURE_MISMATCH = "structure_mismatch"  # 复杂结构不一致
    ONE_FAILS = "one_fails"                    # 一个成功一个失败
    UNKNOWN = "unknown"

# ========== 增强深度比较（返回详细类别）==========
def deep_compare_with_details(obj1, obj2, path=""):
    """
    增强版深度比较，返回 (是否一致, 差异类别, 差异路径)
    如果一致，返回 (True, None, None)
    如果不一致，返回 (False, 类别, 路径)
    """
    # ----- 统一转换 NumPy 标量 -----
    if hasattr(obj1, 'dtype'):
        obj1 = obj1.item()
    if hasattr(obj2, 'dtype'):
        obj2 = obj2.item()
    # ------------------------------------

    # 类型不同
    if type(obj1) != type(obj2):
        return False, DiffCategory.TYPE_MISMATCH, path
    
    # 浮点数比较
    if isinstance(obj1, float):
        if math.isclose(obj1, obj2, rel_tol=FLOAT_REL_TOL):
            return True, None, None
        else:
            return False, DiffCategory.FLOAT_APPROX, path
    
    # 字典比较
    if isinstance(obj1, dict):
        if obj1.keys() != obj2.keys():
            return False, DiffCategory.KEY_MISMATCH, path
        for k in obj1:
            ok, cat, subpath = deep_compare_with_details(obj1[k], obj2[k], f"{path}.{k}")
            if not ok:
                return False, cat, subpath
        return True, None, None
    
    # 列表/元组比较
    if isinstance(obj1, (list, tuple)):
        if len(obj1) != len(obj2):
            return False, DiffCategory.LENGTH_MISMATCH, path
        for i, (a, b) in enumerate(zip(obj1, obj2)):
            ok, cat, subpath = deep_compare_with_details(a, b, f"{path}[{i}]")
            if not ok:
                return False, cat, subpath
        return True, None, None
    
    # 集合比较（无序）
    if isinstance(obj1, (set, frozenset)):
        if obj1 == obj2:
            return True, None, None
        else:
            # 可以进一步比较差异元素，但这里简化处理
            return False, DiffCategory.VALUE_MISMATCH, path
    
    # 字节串比较
    if isinstance(obj1, bytes):
        if obj1 == obj2:
            return True, None, None
        else:
            return False, DiffCategory.VALUE_MISMATCH, path
    
    # 其他类型直接等值比较
    if obj1 == obj2:
        return True, None, None
    else:
        return False, DiffCategory.VALUE_MISMATCH, path

# 兼容原有 deep_compare
def deep_compare(obj1, obj2):
    ok, _, _ = deep_compare_with_details(obj1, obj2)
    return ok

# ========== 指纹计算 ==========
def compute_fingerprint(text):
    return hashlib.md5(text.encode('utf-8', errors='ignore')).hexdigest()

# ========== 保存差异到日志（新增类别参数）==========
def save_difference(input_str, result_a, result_b, lib_a_name, lib_b_name, category="unknown", detail_path=""):
    fingerprint = compute_fingerprint(input_str)
    
    with open(DIFF_LOG_FILE, "a", encoding='utf-8') as f:
        f.write(f"=== 指纹: {fingerprint} ===\n")
        f.write(f"类别: {category}\n")
        if detail_path:
            f.write(f"差异路径: {detail_path}\n")
        f.write(f"输入: {repr(input_str)}\n")
        f.write(f"{lib_a_name} 结果: {result_a}\n")
        f.write(f"{lib_b_name} 结果: {result_b}\n")
        f.write("=" * 50 + "\n\n")
    
    with open(FINGERPRINT_FILE, "a", encoding='utf-8') as f:
        f.write(fingerprint + "\n")
    
    # 如果启用反馈式语料库，则添加到语料库
    if ENABLE_FEEDBACK_CORPUS:
        add_to_corpus(input_str, category)
    
    print(f"[差异] 已保存，指纹: {fingerprint}, 类别: {category}")

# ========== 确保目录存在 ==========
def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

# ========== 反馈式语料库增强 ==========
def add_to_corpus(input_str, category=""):
    """
    将输入字符串保存到语料库目录，文件名使用指纹。
    可选的 category 前缀用于分类存放（便于观察）。
    """
    if not ENABLE_FEEDBACK_CORPUS:
        return
    
    ensure_dir(CORPUS_DIR)
    fingerprint = compute_fingerprint(input_str)
    
    # 按类别分目录，便于管理
    if category:
        subdir = os.path.join(CORPUS_DIR, category)
        ensure_dir(subdir)
        filepath = os.path.join(subdir, fingerprint)
    else:
        filepath = os.path.join(CORPUS_DIR, fingerprint)
    
    # 如果文件已存在，不重复写入
    if not os.path.exists(filepath):
        with open(filepath, "w", encoding='utf-8') as f:
            f.write(input_str)
        
        # 限制文件数量（超过阈值时删除最早的文件）
        target_dir = subdir if category else CORPUS_DIR
        files = [os.path.join(target_dir, f) for f in os.listdir(target_dir) 
                 if os.path.isfile(os.path.join(target_dir, f))]
        if len(files) > MAX_CORPUS_FILES:
            files.sort(key=os.path.getmtime)
            os.remove(files[0])
