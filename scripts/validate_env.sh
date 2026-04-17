#!/usr/bin/env bash
set -euo pipefail

python - <<'PY'
import torch
import ultralytics

print("torch:", torch.__version__)
print("torch cuda:", torch.version.cuda)
print("cuda available:", torch.cuda.is_available())
print("gpu count:", torch.cuda.device_count())
print("nccl available:", torch.distributed.is_nccl_available())
print("ultralytics:", ultralytics.__version__)
for index in range(torch.cuda.device_count()):
    print(index, torch.cuda.get_device_name(index))
PY

yolo checks
