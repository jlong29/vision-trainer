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

## Follow-on work

- Bundle export manifests with explicit target runtime expectations.
- Add artifact checksums and promotion sign-off once the deployment loop is defined.
