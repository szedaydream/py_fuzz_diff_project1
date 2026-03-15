#!/usr/bin/env python3
import os
import re
import pandas as pd
import matplotlib.pyplot as plt
from config import DIFF_LOG_FILE, FINGERPRINT_FILE, REPORT_DIR
from utils import ensure_dir

def load_fingerprints():
    """加载已记录的指纹，用于去重统计"""
    if not os.path.exists(FINGERPRINT_FILE):
        return set()
    with open(FINGERPRINT_FILE, 'r') as f:
        return set(line.strip() for line in f if line.strip())

def parse_log():
    """解析差异日志，返回DataFrame"""
    if not os.path.exists(DIFF_LOG_FILE):
        print("❌ 差异日志文件不存在，请先运行 fuzzer.py")
        return None

    with open(DIFF_LOG_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = content.split("=" * 50)
    records = []
    for block in blocks:
        if "指纹:" not in block:
            continue
        fingerprint = re.search(r"指纹: (\w+)", block)
        category = re.search(r"类别: (\w+)", block)
        detail_path = re.search(r"差异路径: (.+)", block)
        input_str = re.search(r"输入: (.+)", block)
        # 注意：库名可能在日志中是动态的，这里假设固定为 json 和 ujson
        a_res = re.search(r"math 结果: (.+)", block)
        b_res = re.search(r"numpy 结果: (.+)", block)
        if fingerprint and input_str and a_res and b_res:
            records.append({
                "fingerprint": fingerprint.group(1),
                "category": category.group(1) if category else "unknown",
                "input": input_str.group(1),
                "json_result": a_res.group(1),
                "ujson_result": b_res.group(1),
                "detail_path": detail_path.group(1) if detail_path else ""
            })
    df = pd.DataFrame(records)
    return df

def generate_report(df):
    """生成统计报告和图表"""
    ensure_dir(REPORT_DIR)
    
    # 去重统计
    unique_count = df["fingerprint"].nunique()
    total_count = len(df)
    
    # 分类统计
    cat_stats = df["category"].value_counts()
    
    # 输出文本报告
    report_path = os.path.join(REPORT_DIR, "analysis_report.txt")
    with open(report_path, "w", encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("差分模糊测试分析报告\n")
        f.write("=" * 60 + "\n")
        f.write(f"总差异条目（含重复）: {total_count}\n")
        f.write(f"唯一差异指纹数量: {unique_count}\n")
        f.write("\n分类统计:\n")
        for cat, count in cat_stats.items():
            f.write(f"  {cat}: {count}\n")
        f.write("=" * 60 + "\n")
    
    print(f"✅ 分析报告已生成: {report_path}")
    
    # 生成柱状图
    plt.figure(figsize=(12, 6))
    cat_stats.plot(kind='bar')
    plt.title("差异分类分布")
    plt.xlabel("类别")
    plt.ylabel("数量")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    chart_path = os.path.join(REPORT_DIR, "category_chart.png")
    plt.savefig(chart_path)
    print(f"✅ 分类图表已保存: {chart_path}")
    
    # 保存分类后的详细数据（CSV）
    csv_path = os.path.join(REPORT_DIR, "differences_with_category.csv")
    df.to_csv(csv_path, index=False, encoding='utf-8')
    print(f"✅ 详细数据已保存: {csv_path}")

if __name__ == "__main__":
    df = parse_log()
    if df is not None and not df.empty:
        generate_report(df)
    else:
        print("没有差异数据可分析。")
