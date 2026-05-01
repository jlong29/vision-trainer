# Promotion Workflow

This repo does not deploy directly to the Xavier NX. It prepares candidate artifacts and records enough metadata for later deployment testing.

## Current promotion loop

1. Train and evaluate on a validated phase 1 package.
2. Export the chosen weights with `bootstrap_train.export`.
3. Write export metadata under `artifacts/exports/<name>/`.
4. Hand the artifact plus metadata back to the Xavier-side deployment workflow for runtime testing.

## Required metadata

- source weights path
- export config
- generated command
- timestamp
- optional notes about the dataset package and experiment name
- source dataset kind, such as `phase1` or `curated_release`
- source package `package_id` or curated release `release_id` when available

For curated-release candidates, validate and record the release at export time:

```bash
PYTHONPATH=src python -m bootstrap_train.export --config configs/export/onnx_fp32.yaml --weights /path/to/best.pt --release-root /path/to/curated_release
```

This records `source.kind`, `source.id`, release details, and the release validation report in `export_request.json`.

## Follow-on work

- Bundle export manifests with explicit target runtime expectations.
- Add artifact checksums and promotion sign-off once the deployment loop is defined.
