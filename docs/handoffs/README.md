# Handoff Workflow

This directory is the tracked communication surface between the Xavier edge node and the desktop training node.

## Purpose

Use these files for durable status, contract coordination, and explicit requests that should survive beyond chat history and `.agent/` scratch state.

## Files

- `EDGE_TO_DESKTOP.md` — upstream producer notes, package changes, edge-side observations, and requests for the desktop consumer
- `DESKTOP_TO_EDGE.md` — desktop validation results, training findings, consumer-side integration issues, and requests back to the edge producer

## Update rules

- Keep entries append-only within each dated section unless correcting a factual error.
- Include absolute dates in `YYYY-MM-DD` format.
- Reference durable repo files when a note depends on a contract or code path.
- Keep temporary debugging artifacts in `.agent/logs/` during a task, then summarize the durable result here at closeout.
- If a note implies a contract change, update `docs/package_contracts.md`, the matching schema under `schemas/`, and the validator/tests in the same task.

## Required fields for each new entry

- Date
- Author / node (`edge` or `desktop`)
- Summary
- Evidence
- Requested action
- Contract impact (`none`, `clarification`, or `change`)
