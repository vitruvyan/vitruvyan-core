#!/bin/bash
# LangGraph Orchestration Contract v1.0 - Enforcement Script
# This script runs in CI/CD to block merges violating the architectural contract.

set -e

echo "🔍 Enforcing LangGraph Orchestration Contract v1.0..."
echo "📜 See .github/LANGGRAPH_ORCHESTRATION_CONTRACT_v1.md"
echo ""

VIOLATIONS=0
NODE_DIR="vitruvyan_core/core/orchestration/langgraph/node"

# Check if directory exists
if [ ! -d "$NODE_DIR" ]; then
  echo "⚠️  Directory $NODE_DIR not found, skipping check"
  exit 0
fi

echo "Checking graph nodes in $NODE_DIR..."
echo ""

# Pattern 1: Domain arithmetic (sum, min, max, avg)
echo "🔎 Checking for forbidden domain arithmetic..."
for FILE in "$NODE_DIR"/*.py; do
  if [ "$(basename "$FILE")" = "__init__.py" ]; then
    continue
  fi
  
  # Skip _legacy and _archived files
  if [[ "$(basename "$FILE")" == _legacy* ]] || [[ "$(basename "$FILE")" == _archived* ]]; then
    continue
  fi
  
  # Filter out comments, docstrings, and markdown bullets, then check for violations
  if grep -E "sum\(|min\(|max\(|\.mean\(\)|\.median\(\)" "$FILE" | \
     grep -v "^#" | \
     grep -v "^\s*#" | \
     grep -v '"""' | \
     grep -v "'''" | \
     grep -v "^\s*-" | \
     grep -v "Contract Compliance" | \
     grep -q . ; then
    echo "❌ VIOLATION: Domain arithmetic in $(basename "$FILE")"
    echo "   Found: sum(), min(), max(), .mean(), or .median()"
    echo "   Rule: Calculations must be in Sacred Order services"
    echo "   File: $FILE"
    echo ""
    VIOLATIONS=$((VIOLATIONS + 1))
  fi
done

# Pattern 2: Average calculations (/ len)
echo "🔎 Checking for average calculations..."
for FILE in "$NODE_DIR"/*.py; do
  if [ "$(basename "$FILE")" = "__init__.py" ]; then
    continue
  fi
  
  # Skip _legacy and _archived files
  if [[ "$(basename "$FILE")" == _legacy* ]] || [[ "$(basename "$FILE")" == _archived* ]]; then
    continue
  fi
  
  if grep -E "/ len\(|/len\(" "$FILE" | \
     grep -v "^#" | \
     grep -v "^\s*#" | \
     grep -v '"""' | \
     grep -v "'''" | \
     grep -q . ; then
    echo "❌ VIOLATION: Average calculation in $(basename "$FILE")"
    echo "   Found: division by len() (average calculation)"
    echo "   Rule: Services must return pre-calculated averages"
    echo "   File: $FILE"
    echo ""
    VIOLATIONS=$((VIOLATIONS + 1))
  fi
done

# Pattern 3: Threshold comparisons on domain terms
echo "🔎 Checking for semantic threshold comparisons..."
for FILE in "$NODE_DIR"/*.py; do
  if [ "$(basename "$FILE")" = "__init__.py" ]; then
    continue
  fi
  
  # Skip _legacy and _archived files
  if [[ "$(basename "$FILE")" == _legacy* ]] || [[ "$(basename "$FILE")" == _archived* ]]; then
    continue
  fi
  
  if grep -E "(confidence|score|quality|rating|priority)\s*[<>]=?\s*[0-9.]+" "$FILE" | \
     grep -v "^#" | \
     grep -v "^\s*#" | \
     grep -v '"""' | \
     grep -v "'''" | \
     grep -q . ; then
    echo "❌ VIOLATION: Threshold logic in $(basename "$FILE")"
    echo "   Found: comparison of domain metric to hardcoded value"
    echo "   Rule: Services must return semantic status (quality: 'high'/'low')"
    echo "   File: $FILE"
    echo ""
    VIOLATIONS=$((VIOLATIONS + 1))
  fi
done

# Pattern 4: Semantic filtering in list comprehensions
echo "🔎 Checking for semantic filtering..."
for FILE in "$NODE_DIR"/*.py; do
  if [ "$(basename "$FILE")" = "__init__.py" ]; then
    continue
  fi
  
  # Skip _legacy and _archived files
  if [[ "$(basename "$FILE")" == _legacy* ]] || [[ "$(basename "$FILE")" == _archived* ]]; then
    continue
  fi
  
  if grep -E "\[.*for.*if.*(quality|confidence|score|rating).*[<>]" "$FILE" | \
     grep -v "^#" | \
     grep -v "^\s*#" | \
     grep -v '"""' | \
     grep -v "'''" | \
     grep -q . ; then
    echo "❌ VIOLATION: Semantic filtering in $(basename "$FILE")"
    echo "   Found: list comprehension filtering by domain metric"
    echo "   Rule: Services must return pre-filtered results"
    echo "   File: $FILE"
    echo ""
    VIOLATIONS=$((VIOLATIONS + 1))
  fi
done

# Pattern 5: Sorting by domain criteria
echo "🔎 Checking for domain-based sorting..."
for FILE in "$NODE_DIR"/*.py; do
  if [ "$(basename "$FILE")" = "__init__.py" ]; then
    continue
  fi
  
  # Skip _legacy and _archived files
  if [[ "$(basename "$FILE")" == _legacy* ]] || [[ "$(basename "$FILE")" == _archived* ]]; then
    continue
  fi
  
  if grep -E "sorted\(.*key=lambda.*(score|confidence|priority|quality)" "$FILE" | \
     grep -v "^#" | \
     grep -v "^\s*#" | \
     grep -v '"""' | \
     grep -v "'''" | \
     grep -v "^\s*-" | \
     grep -v "Contract Compliance" | \
     grep -q . ; then
    echo "❌ VIOLATION: Domain sorting in $(basename "$FILE")"
    echo "   Found: sorted() with domain key"
    echo "   Rule: Services must return pre-sorted results"
    echo "   File: $FILE"
    echo ""
    VIOLATIONS=$((VIOLATIONS + 1))
  fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $VIOLATIONS -gt 0 ]; then
  echo ""
  echo "❌ CONTRACT VIOLATIONS DETECTED: $VIOLATIONS"
  echo ""
  echo "📖 LangGraph Orchestration Contract v1.0"
  echo "   Location: .github/LANGGRAPH_ORCHESTRATION_CONTRACT_v1.md"
  echo ""
  echo "Key Rules:"
  echo "  • Graph nodes MUST NOT perform domain calculations"
  echo "  • Graph nodes MUST NOT apply semantic thresholds"
  echo "  • Graph nodes MUST extract pre-calculated metrics from services"
  echo ""
  echo "Required Actions:"
  echo "  1. Move calculations to Sacred Order services"
  echo "  2. Update service APIs to return pre-calculated metrics"
  echo "  3. Update graph nodes to extract (not calculate) values"
  echo ""
  echo "See contract section 6 (Migration Path) for guidance."
  echo ""
  exit 1
else
  echo ""
  echo "✅ All graph nodes comply with Orchestration Contract v1.0"
  echo ""
  exit 0
fi
