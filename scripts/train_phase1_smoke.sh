#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "usage: $0 <phase1_package_root> [extra bootstrap_train.train args...]" >&2
  exit 1
fi

dataset_root=$1
shift

PYTHONPATH=src python -m bootstrap_train.train \
  --config configs/train/phase1_smoke.yaml \
  --dataset-root "$dataset_root" \
  "$@"
