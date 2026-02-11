#!/bin/bash
#
# Synaptic Bus Dashboard Simulator — Quick Start Script
# Runs the event simulator inside Docker to populate Grafana dashboard
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_COMPOSE_DIR="$REPO_ROOT/infrastructure/docker"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  🧠 Synaptic Bus Dashboard Simulator${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Parse arguments
DURATION=300  # Default 5 minutes
INTENSITY="medium"  # Default medium
CONTINUOUS=false

print_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    -d, --duration SECONDS    Run for specified duration (default: 300)
    -c, --continuous          Run continuously (Ctrl+C to stop)
    -i, --intensity LEVEL     Traffic intensity: low, medium, high, extreme (default: medium)
    -h, --help                Show this help message

Examples:
    # Run for 5 minutes with medium intensity
    $0 --duration 300 --intensity medium
    
    # Run continuously with high intensity
    $0 --continuous --intensity high
    
    # Quick test: 1 minute low intensity
    $0 -d 60 -i low
EOF
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--duration)
            DURATION="$2"
            shift 2
            ;;
        -c|--continuous)
            CONTINUOUS=true
            DURATION=0
            shift
            ;;
        -i|--intensity)
            INTENSITY="$2"
            shift 2
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            print_usage
            exit 1
            ;;
    esac
done

# Check if Redis is running
echo -e "${YELLOW}Checking Redis...${NC}"
if ! docker ps --filter "name=core_redis" --filter "status=running" | grep -q core_redis; then
    echo -e "${RED}❌ Redis container not running!${NC}"
    echo "Please start Redis first:"
    echo "  cd $DOCKER_COMPOSE_DIR && docker compose up -d redis"
    exit 1
fi
echo -e "${GREEN}✅ Redis is running${NC}"
echo ""

# Install dependencies if needed
echo -e "${YELLOW}Installing dependencies...${NC}"
pip3 install -q redis 2>/dev/null || {
    echo -e "${YELLOW}Installing redis package...${NC}"
    pip3 install redis
}
echo -e "${GREEN}✅ Dependencies ready${NC}"
echo ""

# Show configuration
echo -e "${BLUE}Configuration:${NC}"
if [ "$CONTINUOUS" = true ]; then
    echo "  Duration: CONTINUOUS (Ctrl+C to stop)"
else
    echo "  Duration: ${DURATION}s"
fi
echo "  Intensity: ${INTENSITY}"
echo "  Redis: localhost:6379"
echo ""

# Run simulator
echo -e "${GREEN}🚀 Starting simulator...${NC}"
echo ""

SIMULATOR_CMD="python3 $SCRIPT_DIR/synaptic_bus_simulator.py --redis-host localhost --redis-port 6379 --intensity $INTENSITY"
if [ "$CONTINUOUS" = true ]; then
    SIMULATOR_CMD="$SIMULATOR_CMD --continuous"
else
    SIMULATOR_CMD="$SIMULATOR_CMD --duration $DURATION"
fi

# Trap Ctrl+C to clean exit
trap 'echo -e "\n${YELLOW}⚠️  Stopping simulator...${NC}"; exit 0' INT

$SIMULATOR_CMD

echo ""
echo -e "${GREEN}✅ Simulation complete!${NC}"
echo ""
echo -e "${BLUE}📊 View dashboard at: ${NC}http://localhost:3000/d/synaptic-bus-eeg"
echo -e "${BLUE}👤 Login: ${NC}admin / vitruvyan_admin"
echo ""
