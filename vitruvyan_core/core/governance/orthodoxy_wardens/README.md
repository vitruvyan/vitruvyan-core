# 🏛️ Orthodoxy Wardens

Questo modulo rappresenta l'Ordine degli "Orthodoxy Wardens", i guardiani della compliance, della salute e dell'architettura del sistema Vitruvyan. A differenza di altri ordini, questo è composto da una serie di agenti specializzati orchestrati da un agente di audit principale.

## Componenti Principali (Agenti)

Ecco una descrizione di ogni componente (file `.py`) in questa directory:

- **`confessor_agent.py`** (Precedentemente `audit_agent.py`): Il cuore pulsante dell'ordine. Questo file definisce l'`AutonomousAuditAgent`, un agente complesso basato su `LangGraph` che orchestra l'intero processo di audit. Serve da base per i ruoli di Confessor e Abbot.

- **`penitent_agent.py`** (Precedentemente `auto_corrector.py`): Definisce l'`AutoCorrector`. Questo agente è specializzato nell'applicare correzioni automatiche a problemi critici rilevati durante un audit. È il "Penitente" che esegue i rituali di purificazione.

- **`chronicler_agent.py`** (Precedentemente `system_monitor.py`): Definisce il `SystemMonitor`, che è responsabile del monitoraggio delle metriche di salute del sistema come l'uso di CPU, memoria e disco. È il "Cronista" che registra lo stato del reame.

- **`inquisitor_agent.py`** (Precedentemente `compliance_validator.py`): Definisce il `ComplianceValidator`. Questo agente utilizza un LLM per analizzare gli output del sistema e validare che siano conformi a regole finanziarie o normative predefinite. È l'"Inquisitor" che investiga le eresie.

- **`code_analyzer.py`**: Contiene il `CodeAnalyzer`, un componente responsabile dell'analisi statica del codice sorgente per identificare potenziali rischi, violazioni di stile o problemi di sicurezza.

- **`docker_manager.py`**: Fornisce una classe `DockerManager` per interagire con l'ambiente Docker, permettendo di controllare lo stato dei container, riavviarli e raccogliere metriche.

- **`git_monitor.py`**: Contiene il `GitMonitor`, utilizzato per analizzare la cronologia recente di `git` e identificare le modifiche al codice che devono essere auditate.

- **`schema_validator.py`**: Un componente per validare che gli schemi dei dati (es. payload degli eventi, tabelle del database) siano corretti e non corrotti.