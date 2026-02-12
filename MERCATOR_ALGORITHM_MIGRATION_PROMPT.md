# Prompt per Agente su Mercator VPS — Migrazione Algoritmi Proprietari

**Data**: 12 Febbraio 2026  
**Contesto**: Vitruvyan-core ha una nuova struttura in `vitruvyan_core/core/cognitive/vitruvyan_proprietary/` con cartelle pronte per ricevere gli algoritmi proprietari. Devi trovare i file sorgente e copiarli nelle cartelle giuste.

---

## PREREQUISITO: Fai pull prima di tutto

```bash
cd /path/to/vitruvyan-core   # o vitruvyan, dipende dal nome del repo su mercator
git pull origin main
```

Verifica che le cartelle esistano:
```bash
ls vitruvyan_core/core/cognitive/vitruvyan_proprietary/
# Deve mostrare: __init__.py  _legacy/  vare/  vee/  vmfl/  vsgs/  vwre/
```

---

## TASK: Trovare e copiare gli algoritmi nelle cartelle corrette

### Cosa cercare

Su questa VPS (mercator) dovrebbero esistere i file sorgente degli algoritmi proprietari che sono stati eliminati dal repo `vitruvyan-core` da uno script di cleanup (`scripts/cleanup/03_delete_financial_specific.py`).

I file originali erano alla root di `vitruvyan_core/core/cognitive/vitruvyan_proprietary/` con questi nomi:

| File originale | Linee stimate | Algoritmo |
|---------------|---------------|-----------|
| `vwre_engine.py` | ~612 | VWRE — Vitruvyan Weighted Reverse Engineering |
| `vare_engine.py` | ~752 | VARE — Vitruvyan Adaptive Risk Engine |
| `vhsw_engine.py` | sconosciuto | VHSW — Vitruvyan Human Sentiment Weighting |
| `vmfl_engine.py` | sconosciuto | VMFL — Vitruvyan Memory Feedback Loop |

### Dove cercare

1. **Nel repo stesso** — potrebbe esserci una versione non-pullata:
   ```bash
   find . -name "vwre_engine.py" -o -name "vare_engine.py" -o -name "vhsw_engine.py" -o -name "vmfl_engine.py" 2>/dev/null
   ```

2. **Nella git history** — i file esistevano prima del cleanup:
   ```bash
   # Trova il commit dove sono stati eliminati
   git log --all --diff-filter=D -- "vitruvyan_core/core/cognitive/vitruvyan_proprietary/vwre_engine.py" | head -5
   
   # Recupera il file dall'ultimo commit dove esisteva
   git show HEAD~N:vitruvyan_core/core/cognitive/vitruvyan_proprietary/vwre_engine.py > /tmp/vwre_engine.py
   ```

3. **Alternativa con git log per trovare il commit esatto**:
   ```bash
   git log --all --oneline -- "vitruvyan_core/core/cognitive/vitruvyan_proprietary/vare_engine.py"
   git log --all --oneline -- "vitruvyan_core/core/cognitive/vitruvyan_proprietary/vwre_engine.py"
   git log --all --oneline -- "vitruvyan_core/core/cognitive/vitruvyan_proprietary/vmfl_engine.py"
   git log --all --oneline -- "vitruvyan_core/core/cognitive/vitruvyan_proprietary/vhsw_engine.py"
   ```

4. **Recupero da commit specifico**:
   ```bash
   # Una volta trovato il commit PRIMA della deletion (es. abc1234):
   git show abc1234:vitruvyan_core/core/cognitive/vitruvyan_proprietary/vwre_engine.py > vwre_engine_recovered.py
   git show abc1234:vitruvyan_core/core/cognitive/vitruvyan_proprietary/vare_engine.py > vare_engine_recovered.py
   git show abc1234:vitruvyan_core/core/cognitive/vitruvyan_proprietary/vhsw_engine.py > vhsw_engine_recovered.py
   git show abc1234:vitruvyan_core/core/cognitive/vitruvyan_proprietary/vmfl_engine.py > vmfl_engine_recovered.py
   ```

---

## DOVE PIAZZARE I FILE (destinazione finale)

### VWRE → `vitruvyan_core/core/cognitive/vitruvyan_proprietary/vwre/`
```bash
cp vwre_engine_recovered.py vitruvyan_core/core/cognitive/vitruvyan_proprietary/vwre/vwre_engine.py
```
Il file `__init__.py` esiste già con la documentazione del modulo.

### VARE → `vitruvyan_core/core/cognitive/vitruvyan_proprietary/vare/`
```bash
cp vare_engine_recovered.py vitruvyan_core/core/cognitive/vitruvyan_proprietary/vare/vare_engine.py
```

### VHSW → ATTENZIONE: Non ha una cartella dedicata
VHSW è stato classificato come "Partial" e potrebbe non avere abbastanza codice per una cartella dedicata. 
- Se il file esiste ed è sostanziale (>100 linee): crea la cartella e piazzalo lì:
  ```bash
  mkdir -p vitruvyan_core/core/cognitive/vitruvyan_proprietary/vhsw/
  # Crea un __init__.py simile agli altri
  cp vhsw_engine_recovered.py vitruvyan_core/core/cognitive/vitruvyan_proprietary/vhsw/vhsw_engine.py
  ```
- Se il file è uno stub o non esiste: ignora VHSW per ora.

### VMFL → `vitruvyan_core/core/cognitive/vitruvyan_proprietary/vmfl/`
```bash
cp vmfl_engine_recovered.py vitruvyan_core/core/cognitive/vitruvyan_proprietary/vmfl/vmfl_engine.py
```

---

## VERIFICA DOPO LA COPIA

```bash
# 1. Verifica struttura
find vitruvyan_core/core/cognitive/vitruvyan_proprietary/ -name "*.py" | sort

# Output atteso:
# vitruvyan_core/core/cognitive/vitruvyan_proprietary/__init__.py
# vitruvyan_core/core/cognitive/vitruvyan_proprietary/_legacy/__init__.py
# vitruvyan_core/core/cognitive/vitruvyan_proprietary/_legacy/algorithm_memory_adapter.py
# vitruvyan_core/core/cognitive/vitruvyan_proprietary/_legacy/orchestrator.py
# vitruvyan_core/core/cognitive/vitruvyan_proprietary/vare/__init__.py
# vitruvyan_core/core/cognitive/vitruvyan_proprietary/vare/vare_engine.py     ← NEW
# vitruvyan_core/core/cognitive/vitruvyan_proprietary/vee/__init__.py
# vitruvyan_core/core/cognitive/vitruvyan_proprietary/vee/vee_analyzer.py
# vitruvyan_core/core/cognitive/vitruvyan_proprietary/vee/vee_engine.py
# vitruvyan_core/core/cognitive/vitruvyan_proprietary/vee/vee_generator.py
# vitruvyan_core/core/cognitive/vitruvyan_proprietary/vee/vee_memory_adapter.py
# vitruvyan_core/core/cognitive/vitruvyan_proprietary/vmfl/__init__.py
# vitruvyan_core/core/cognitive/vitruvyan_proprietary/vmfl/vmfl_engine.py     ← NEW
# vitruvyan_core/core/cognitive/vitruvyan_proprietary/vsgs/__init__.py
# vitruvyan_core/core/cognitive/vitruvyan_proprietary/vwre/__init__.py
# vitruvyan_core/core/cognitive/vitruvyan_proprietary/vwre/vwre_engine.py     ← NEW
# (opzionale) vitruvyan_core/core/cognitive/vitruvyan_proprietary/vhsw/__init__.py
# (opzionale) vitruvyan_core/core/cognitive/vitruvyan_proprietary/vhsw/vhsw_engine.py

# 2. Conta le linee per conferma
wc -l vitruvyan_core/core/cognitive/vitruvyan_proprietary/vwre/vwre_engine.py  # ~612
wc -l vitruvyan_core/core/cognitive/vitruvyan_proprietary/vare/vare_engine.py  # ~752
wc -l vitruvyan_core/core/cognitive/vitruvyan_proprietary/vmfl/vmfl_engine.py  # sconosciuto
```

---

## COMMIT E PUSH

```bash
git add -A
git commit -m "feat(proprietary): migrate VWRE/VARE/VMFL engines from git history

Recovered from pre-cleanup commit:
- vwre/vwre_engine.py: VWRE attribution analysis (~612 lines)
- vare/vare_engine.py: VARE adaptive risk engine (~752 lines)
- vmfl/vmfl_engine.py: VMFL memory feedback loop
- vhsw/vhsw_engine.py: VHSW sentiment weighting (if found)

Files recovered from git history after deletion by cleanup script
(scripts/cleanup/03_delete_financial_specific.py).
No code modifications — original code preserved for refactoring phase."

git push origin main
```

---

## NOTE IMPORTANTI

1. **NON modificare il codice** — copia as-is. Il refactoring avviene nella fase successiva.
2. **NON toccare i file in `vee/`** — VEE è già al suo posto e funzionante.
3. **NON toccare `_legacy/`** — contiene file archiviati (orchestrator.py, algorithm_memory_adapter.py).
4. **NON toccare `vsgs/`** — VSGS verrà popolato separatamente con codice estratto da `semantic_grounding_node.py`.
5. Se trovi altri file collegati (analyzer, memory_adapter, etc.) per VWRE/VARE/VMFL, copiali nella cartella corrispondente.

---

## DOPO IL PUSH

Comunicare all'operatore su vitruvyan-core VPS che il push è stato fatto. 
Lui farà `git pull` e procederà con il refactoring degli algoritmi per renderli domain-agnostic.
