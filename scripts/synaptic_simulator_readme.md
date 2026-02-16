# Fermare il simulator
pkill -f synaptic_bus_simulator

# Visualizzare log in realtime
tail -f /tmp/simulator_api.log

# Avviare con altre intensità
python3 scripts/synaptic_bus_simulator.py --duration 3600 --intensity low
python3 scripts/synaptic_bus_simulator.py --continuous --intensity high

# Verificare metriche
curl -s http://localhost:9012/metrics | grep scribe_write_total

# Stato processo
ps aux | grep synaptic_bus_simulator