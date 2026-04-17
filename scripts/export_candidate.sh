#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "usage: $0 <weights_path> [extra bootstrap_train.export args...]" >&2
  exit 1
fi

weights=$1
shift

PYTHONPATH=src python -m bootstrap_train.export \
  --config configs/export/onnx_fp32.yaml \
  --weights "$weights" \
  "$@"
