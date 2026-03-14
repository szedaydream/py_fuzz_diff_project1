#!/usr/bin/env python3
import sys
import json
import ujson
from utils import deep_compare

def still_causes_difference(original_input, lib_a_func, lib_b_func):
    """检查给定输入是否仍能触发差异（与原始比较逻辑一致）"""
    try:
        test_string = original_input.decode('utf-8')
    except UnicodeDecodeError:
        return False

    try:
        res_a = lib_a_func(test_string)
        res_a_str = repr(res_a)
        res_a_obj = res_a
    except Exception as e:
        res_a_obj = None
        res_a_str = f"EXCEPTION: {type(e).__name__}"

    try:
        res_b = lib_b_func(test_string)
        res_b_str = repr(res_b)
        res_b_obj = res_b
    except Exception as e:
        res_b_obj = None
        res_b_str = f"EXCEPTION: {type(e).__name__}"

    if (res_a_obj is None) != (res_b_obj is None):
        return True
    if res_a_obj is not None and res_b_obj is not None:
        if not deep_compare(res_a_obj, res_b_obj):
            return True
    if res_a_obj is None and res_b_obj is None:
        if res_a_str != res_b_str:
            return True
    return False

def minimize(original_bytes):
    """返回一个最小化后的字节串，仍能触发相同差异"""
    original = original_bytes
    minimal = original
    changed = True
    while changed:
        changed = False
        for i in range(len(minimal)):
            candidate = minimal[:i] + minimal[i+1:]
            if still_causes_difference(candidate, json.loads, ujson.loads):
                minimal = candidate
                changed = True
                break
    return minimal

def main():
    if len(sys.argv) < 2:
        print("用法: python minimizer.py <输入字符串>")
        print("或者: python minimizer.py --file <包含输入的文件>")
        return
    
    if sys.argv[1] == "--file" and len(sys.argv) > 2:
        with open(sys.argv[2], 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line:
                print(f"原始: {repr(line)}")
                minimized = minimize(line.encode('utf-8')).decode('utf-8', errors='ignore')
                print(f"最小化: {repr(minimized)}")
                print()
    else:
        input_str = sys.argv[1]
        print(f"原始: {repr(input_str)}")
        minimized = minimize(input_str.encode('utf-8')).decode('utf-8', errors='ignore')
        print(f"最小化: {repr(minimized)}")

if __name__ == "__main__":
    main()
