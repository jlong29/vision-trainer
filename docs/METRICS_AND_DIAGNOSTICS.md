# Metrics And Diagnostics

## Early-stage metrics

During bootstrap, prioritize operational sanity before deep metric optimization:

- successful package validation
- successful Ultralytics startup
- stable epoch throughput
- no GPU OOM failures
- acceptable temperature behavior on the 1080 Ti cards

## Model metrics to watch

- precision
- recall
- mAP50
- mAP50-95

Track these alongside:

- dataset `package_id`
- model family (`yolo11n`, `yolo11s`, `yolo11m`)
- image size
- batch size
- device layout

## Debugging guidance

- Use phase 2 inspection when frame-only labels need temporal context.
- Treat manifest provenance as part of the diagnostic trail.
- If training becomes unstable, reduce `batch`, then `workers`, then `imgsz`.
