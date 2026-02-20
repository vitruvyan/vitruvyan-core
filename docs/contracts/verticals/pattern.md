# Vertical Pattern (Contract-First)

This page defines the standard pattern for all new verticals.

## Core Rule

No vertical can bypass contracts. Domain logic must be attached through adapters implementing canonical interfaces.

## Mandatory Pieces

- `intent_config`
- `README`
- `manifest`

## Adapter Model

- LangGraph plugin adapter
- Optional LangGraph graph-nodes hook (`domains/<domain>/graph_nodes/registry.py`)
- Sacred Orders governance adapter
- Optional Neural Engine adapters (`IDataProvider`, `IScoringStrategy`)

## Canonical Contract Namespace

Use `contracts` as unique import surface:

- `contracts.GraphPlugin`
- `contracts.BaseParser`
- `contracts.IDataProvider`
- `contracts.IScoringStrategy`
- `contracts.ILLMProvider`

## Template

Use:

- `docs/contracts/verticals/templates/vertical_manifest.yaml`
