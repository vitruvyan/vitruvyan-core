# Verticals Directory

This directory is intentionally empty in vitruvyan-core.

Verticals are implemented in separate repositories:
- `mercator/` — Financial analysis (trading signals, collection management)
- `aegis/` — Emergency response (disaster management, resource allocation)
- `[your-vertical]/` — Your domain

## Creating a New Vertical

See [Vitruvyan Vertical Specification](../../docs/foundational/Vitruvyan_Vertical_Specification.md) for:
- Required interfaces (`VerticalInterface`)
- Domain ontology definition
- Data connectors pattern
- Uncertainty model implementation
- Threshold configuration
- VEE template customization

## Directory Structure for Verticals

```
your-vertical/
├── domain/
│   ├── ontology.yaml      # Domain concepts and relationships
│   ├── lexicon.py         # Domain-specific vocabulary
│   └── thresholds.yaml    # Confidence thresholds
├── connectors/
│   └── data_sources.py    # External data integration
├── agents/
│   └── domain_agents.py   # Specialized cognitive agents
├── vee/
│   └── templates.py       # Explainability templates
└── config.yaml            # Vertical configuration
```
