# Deprecated Components

These components are deprecated and will be removed in v2.0.

## composites/
- `FundamentalsDisplay.jsx` → Use `analytics/panels/FundamentalsPanel`
- `MetricDisplay.jsx` → Use `cards/MetricCard`
- `RiskDisplay.jsx` → Use `analytics/panels/RiskPanel`

## comparison/
- `ComparisonNeuralEngineCard.jsx` → Use `cards/ZScoreCardMulti`

## Migration Guide
1. Update imports to new locations
2. Verify component API compatibility
3. Remove deprecated imports