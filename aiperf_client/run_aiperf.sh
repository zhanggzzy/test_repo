#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 || -z "${1:-}" ]]; then
  echo "用法: bash $0 http://IP:PORT" >&2
  exit 1
fi

AIPERF_BASE_URL="${1%/}"

export PYTHONPATH=/home/aiperf/aiperf_client/aiperf_inferencex_754356e9/src:/home/aiperf/aiperf_client/aiperf-k3-c16-py
export HF_DATASETS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false

export AIPERF_DATASET_CONFIGURATION_TIMEOUT=1800
export AIPERF_SERVICE_PROFILE_CONFIGURE_TIMEOUT=2100

#--tokenizer /home/aiperf/aiperf_client/tokenizer/k3_tokenizer

python3 -m aiperf profile \
  --scenario inferencex-agentx-mvp \
  --url "${AIPERF_BASE_URL}" \
  --endpoint /v1/chat/completions \
  --endpoint-type chat \
  --streaming \
  --model moonshotai/Kimi-K3 \
  --tokenizer /home/aiperf/aiperf_client/tokenizer/k3_tokenizer \
  --tokenizer-trust-remote-code \
  --max-context-length 1048576 \
  --input-file /home/aiperf/aiperf_client/traces_json \
  --custom-dataset-type weka_trace \
  --unsafe-override \
  --num-dataset-entries 393 \
  --use-server-token-count \
  --extra-inputs ignore_eos:true \
  --cache-bust first_turn_prefix \
  --system-idle-gap-cap-seconds 10 \
  --trajectory-start-min-ratio 0.25 \
  --trajectory-start-max-ratio 0.75 \
  --trace-idle-gap-cap-seconds 300 \
  --concurrency 48 \
  --warmup-request-count 480 \
  --num-warmup-sessions 48 \
  --warmup-concurrency 48 \
  --agentic-warmup-grace-period 1800 \
  --benchmark-duration 3600 \
  --random-seed 42 \
  --stats-interval 30 \
  --failed-request-threshold 0.10 \
  --no-gpu-telemetry \
  --server-metrics "${AIPERF_BASE_URL}/metrics" \
  --server-metrics-formats json csv parquet jsonl \
  --slice-duration 1.0 \
  --export-level raw \
  --output-artifact-dir /home/aiperf/aiperf_client/output/aiperf_output \
  --ui simple
