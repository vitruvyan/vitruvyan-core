# Sacred Orders Pattern — Introduction

> **Public Documentation**  
> Last Updated: February 12, 2026

## 🎯 What are Sacred Orders?

**Sacred Orders** are the core **governance modules** of Vitruvyan Core, each responsible for a specific domain of the epistemic operating system.

## 📚 The Six Sacred Orders

### 1. **Memory Orders** — Coherence & RAG
Manage semantic memory, coherence analysis, and retrieval-augmented generation.

### 2. **Vault Keepers** — Archival & Persistence
Handle long-term storage, snapshots, and data archival strategies.

### 3. **Orthodoxy Wardens** — Truth & Validation
Enforce governance rules, validate outputs, and maintain system invariants.

### 4. **Babel Gardens** — Language Processing
Process multilingual text, detect language, and normalize linguistic inputs.

### 5. **Codex Hunters** — Code Discovery
Discover, map, and analyze codebases for structural understanding.

### 6. **Pattern Weavers** — Pattern Analysis
Extract recurring patterns, classify entities, and build taxonomies.

## 🏗️ Architecture Pattern

All Sacred Orders follow the **mandatory 10-directory structure**:

```
<order_name>/
├── domain/              # Immutable dataclasses
├── consumers/           # Pure processing functions
├── governance/          # Rules and classifiers
├── events/              # Event definitions
├── monitoring/          # Metrics constants
├── philosophy/          # Charter and mandate
├── docs/                # Implementation docs
├── examples/            # Usage examples
├── tests/               # Unit tests
└── _legacy/             # Archived code
```

## 🔐 Access Levels

- **✅ Public**: This overview, basic concepts
- **🔒 Full Access**: Detailed implementation, code examples, architectural decisions

[Sign in for full documentation →](/)

---

**Next Steps**: [View Charter](VITRUVYAN_CHARTER.md) | [Architecture Overview](VITRUVYAN_OVERVIEW.md)
