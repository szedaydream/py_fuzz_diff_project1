import os

# ========== 待测库 ==========
LIB_A_NAME = "json"
LIB_B_NAME = "ujson"

# ========== 路径配置 ==========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORPUS_DIR = os.path.join(BASE_DIR, "corpus")        # 种子语料库
DIFF_LOG_FILE = os.path.join(BASE_DIR, "differences.log")  # 原始差异日志
FINGERPRINT_FILE = os.path.join(BASE_DIR, "fingerprints.txt")  # 指纹去重文件
MINIMIZED_DIR = os.path.join(BASE_DIR, "minimized_cases")  # 最小化用例存放目录
REPORT_DIR = os.path.join(BASE_DIR, "reports")        # 分析报告目录

# ========== 模糊测试参数 ==========
FUZZ_RUNS = 0          # 0 表示无限运行，按 Ctrl+C 停止
TIMEOUT = 30           # 单个用例超时时间（秒）

# ========== 差分比较容差 ==========
FLOAT_REL_TOL = 1e-9   # 浮点数相对容差

# ========== 反馈式语料库增强 ==========
ENABLE_FEEDBACK_CORPUS = True   # 是否启用反馈式语料库增强
MAX_CORPUS_FILES = 1000         # 语料库最大文件数（防止无限膨胀）
