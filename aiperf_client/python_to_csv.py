#!/usr/bin/env python3
"""
从 AIPerf profile_export_aiperf.json 提取指标并输出 CSV（无需额外参数）
用法:
    python json_to_csv.py <profile_export_aiperf.json>
示例:
    python json_to_csv.py /path/to/profile_export_aiperf.json
"""

import json
import sys


def safe_metric(obj, key):
    """从指标对象中安全获取值，支持嵌套 dict 或直接值"""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(key)
    return obj


def main():
    if len(sys.argv) < 2:
        print("用法: python json_to_csv.py <profile_export_aiperf.json>", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]

    with open(filepath) as f:
        data = json.load(f)

    # ---------- 提取基本信息 ----------
    # 从 input_config.phases 中获取 profiling 阶段的并发数
    phases = data.get("input_config", {}).get("phases", [])
    concurrency = None
    for phase in phases:
        if phase.get("kind") == "profiling":
            concurrency = phase.get("concurrency", "?")
            break
    if concurrency is None:
        concurrency = "?"

    # 请求数
    req_count = safe_metric(data.get("request_count"), "avg")
    if req_count is None:
        req_count = 0

    # 成功请求数（取 time_to_first_token.count）
    ttft_obj = data.get("time_to_first_token", {})
    success_count = ttft_obj.get("count", 0)
    error_count = req_count - success_count if req_count else 0
    success_rate = (success_count / req_count * 100) if req_count else 0

    # Tokens
    total_output_tokens = safe_metric(data.get("total_output_tokens"), "avg") or 0
    total_input_tokens = safe_metric(data.get("total_isl"), "avg") or 0
    total_cache_tokens = safe_metric(data.get("total_usage_prompt_cache_read_tokens"), "avg") or 0
    non_cache_input = total_input_tokens - total_cache_tokens
    total_tokens = total_cache_tokens + non_cache_input + total_output_tokens

    # Profile 有效时间
    benchmark_duration = safe_metric(data.get("benchmark_duration"), "avg") or 0

    # TPS
    output_tps = safe_metric(data.get("output_token_throughput"), "avg") or 0
    input_tps = safe_metric(data.get("input_token_throughput"), "avg") or 0
    total_tps = safe_metric(data.get("total_token_throughput"), "avg") or 0
    cache_tps = total_cache_tokens / benchmark_duration if benchmark_duration else 0
    non_cache_tps = non_cache_input / benchmark_duration if benchmark_duration else 0

    # ---------- 延迟百分位 ----------
    def extract_percentiles(metric_obj, keys=None):
        """从指标对象中提取 p50, p90, p95, p99, avg"""
        if keys is None:
            keys = ["p50", "p90", "p95", "p99"]
        result = {}
        for k in keys:
            result[k] = safe_metric(metric_obj, k) or 0
        result["avg"] = safe_metric(metric_obj, "avg") or 0
        return result

    ttft = extract_percentiles(ttft_obj)
    itl = extract_percentiles(data.get("inter_token_latency", {}))

    # ---------- 按输入长度分桶（无法从聚合JSON获取）----------
    bucket_info = {
        "<32k": "N/A",
        "32k-128k": "N/A",
        "128k-256k": "N/A",
        ">256k": "N/A",
    }

    # ---------- 构建 CSV 输出 ----------
    header = f"指标,{concurrency}并发"
    lines = [header]

    # --- 基础指标 ---
    lines.append("【基础指标】,")
    basic_items = [
        ("总记录数（profiling 阶段）", int(req_count)),
        ("成功请求数（TTFT>0）", success_count),
        ("错误请求数", error_count),
        ("成功率", f"{success_rate:.2f}%"),
        ("缓存输入总tokens", int(total_cache_tokens)),
        ("非缓存输入总tokens", int(non_cache_input)),
        ("输出总tokens", int(total_output_tokens)),
        ("总tokens", int(total_tokens)),
        ("Profile有效时间 (s)", f"{benchmark_duration:.2f}"),
        ("缓存输入TPS", f"{cache_tps:.2f}"),
        ("非缓存输入TPS", f"{non_cache_tps:.2f}"),
        ("输出TPS", f"{output_tps:.2f}"),
        ("总TPS", f"{total_tps:.2f}"),
    ]
    for name, val in basic_items:
        lines.append(f"{name},{val}")

    # --- TTFT 百分位 ---
    lines.append("")
    lines.append("【延迟百分位数（TTFT，单位 ms）】,")
    order = ["p50", "p90", "p95", "p99"]
    for k in order:
        lines.append(f"{k.upper()},{ttft.get(k, 0):.2f}")
    lines.append(f"Avg,{ttft.get('avg', 0):.2f}")
    lines.append(f"样本数,{ttft_obj.get('count', 0)}")

    # --- ITL 百分位 ---
    lines.append("")
    lines.append("【延迟百分位数（ITL，单位 ms）】,")
    for k in order:
        lines.append(f"{k.upper()},{itl.get(k, 0):.2f}")
    lines.append(f"Avg,{itl.get('avg', 0):.2f}")
    lines.append(f"样本数,{data.get('inter_token_latency', {}).get('count', 0)}")

    # --- 按输入长度分桶的 TTFT P95（无法从聚合JSON获取）---
    lines.append("")
    lines.append("【按输入长度分桶的 TTFT P95（单位 ms）】,")
    for bucket_name, val in bucket_info.items():
        lines.append(f"{bucket_name},{val}")

    # 输出
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
