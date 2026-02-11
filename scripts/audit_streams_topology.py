#!/usr/bin/env python3
"""
Synaptic Bus Topology Auditor

Discovers all Redis Streams, consumer groups, and Sacred Order connectivity.
"""

import redis
import sys
import os
from typing import Dict, List, Any
from collections import defaultdict

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

def audit_streams():
    """Audit all streams and consumer groups"""
    
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    
    print("=" * 80)
    print("SYNAPTIC BUS TOPOLOGY AUDIT")
    print("=" * 80)
    print()
    
    # Get all streams
    streams = r.keys("vitruvyan:*")
    print(f"📊 Total Streams: {len(streams)}")
    print()
    
    # Stream topology map
    topology = {}
    
    for stream in sorted(streams):
        stream_name = stream.replace("vitruvyan:", "")
        
        # Get consumer groups
        try:
            groups_info = r.execute_command("XINFO", "GROUPS", stream)
            
            # Parse groups info (flat list format from Redis)
            groups = []
            i = 0
            while i < len(groups_info):
                if groups_info[i] == b'name' or groups_info[i] == 'name':
                    group_name = groups_info[i+1]
                    if isinstance(group_name, bytes):
                        group_name = group_name.decode('utf-8')
                    
                    # Get consumers count
                    consumers_idx = i + 2
                    if consumers_idx < len(groups_info) and groups_info[consumers_idx] in [b'consumers', 'consumers']:
                        consumers_count = groups_info[consumers_idx + 1]
                    else:
                        consumers_count = 0
                    
                    # Get pending count
                    pending_idx = i + 4
                    if pending_idx < len(groups_info) and groups_info[pending_idx] in [b'pending', 'pending']:
                        pending_count = groups_info[pending_idx + 1]
                    else:
                        pending_count = 0
                    
                    # Get lag
                    lag_idx = i + 10
                    if lag_idx < len(groups_info) and groups_info[lag_idx] in [b'lag', 'lag']:
                        lag = groups_info[lag_idx + 1]
                    else:
                        lag = 0
                    
                    groups.append({
                        'name': group_name,
                        'consumers': consumers_count,
                        'pending': pending_count,
                        'lag': lag
                    })
                    
                    i += 12  # Move to next group
                else:
                    i += 1
                    
        except redis.ResponseError as e:
            groups = []
        
        # Get stream info
        try:
            stream_info = r.execute_command("XINFO", "STREAM", stream)
            length = stream_info[1] if len(stream_info) > 1 else 0
        except:
            length = 0
        
        topology[stream_name] = {
            'groups': groups,
            'length': length
        }
    
    # Print topology
    print("📡 STREAM TOPOLOGY MAP")
    print("=" * 80)
    
    # Group by Sacred Order
    sacred_orders = defaultdict(list)
    for stream_name in sorted(topology.keys()):
        order = stream_name.split('.')[0]
        sacred_orders[order].append(stream_name)
    
    for order in sorted(sacred_orders.keys()):
        print(f"\n🔮 {order.upper()}")
        print("-" * 80)
        
        for stream_name in sorted(sacred_orders[order]):
            info = topology[stream_name]
            print(f"\n  Stream: {stream_name}")
            print(f"  Length: {info['length']} events")
            
            if info['groups']:
                print(f"  Consumer Groups ({len(info['groups'])}):")
                for group in info['groups']:
                    print(f"    - {group['name']}")
                    print(f"      Consumers: {group['consumers']}")
                    print(f"      Pending: {group['pending']}")
                    print(f"      Lag: {group['lag']}")
            else:
                print(f"  ⚠️  NO CONSUMER GROUPS")
    
    print("\n" + "=" * 80)
    print("📊 CONNECTIVITY MATRIX")
    print("=" * 80)
    
    # Sacred Orders matrix
    orders = ['memory', 'vault', 'orthodoxy', 'codex', 'babel', 'pattern_weavers', 'neural_engine', 'conclave', 'semantic', 'vee', 'langgraph', 'epistemic']
    
    print(f"\n{'Order':<20} {'Publishes To':<10} {'Consumes From':<10} {'Groups':<40}")
    print("-" * 80)
    
    for order in orders:
        publishes = sum(1 for s in sacred_orders.get(order, []))
        
        # Count how many streams this order consumes from
        consumes_from = 0
        group_names = []
        for stream_name, info in topology.items():
            for group in info['groups']:
                if order in group['name']:
                    consumes_from += 1
                    group_names.append(group['name'])
        
        if publishes > 0 or consumes_from > 0:
            unique_groups = list(set(group_names))
            groups_str = ', '.join(unique_groups[:2])
            if len(unique_groups) > 2:
                groups_str += f" (+{len(unique_groups)-2} more)"
            print(f"{order:<20} {publishes:<10} {consumes_from:<10} {groups_str:<40}")
    
    print("\n" + "=" * 80)
    print("🔍 HEALTH INDICATORS")
    print("=" * 80)
    
    # Find issues
    issues = []
    
    # Streams with no consumer groups
    no_consumers = [s for s, info in topology.items() if not info['groups']]
    if no_consumers:
        print(f"\n⚠️  Streams with NO consumer groups ({len(no_consumers)}):")
        for stream in no_consumers[:10]:
            print(f"    - {stream}")
        if len(no_consumers) > 10:
            print(f"    ... and {len(no_consumers) - 10} more")
    
    # Streams with high lag
    high_lag = []
    for stream, info in topology.items():
        for group in info['groups']:
            if group['lag'] and group['lag'] > 100:
                high_lag.append((stream, group['name'], group['lag']))
    
    if high_lag:
        print(f"\n⚠️  Consumer groups with HIGH LAG (>100):")
        for stream, group, lag in high_lag[:10]:
            print(f"    - {stream} / {group}: {lag} events")
    
    # Streams with pending messages
    pending_streams = []
    for stream, info in topology.items():
        for group in info['groups']:
            if group['pending'] > 0:
                pending_streams.append((stream, group['name'], group['pending']))
    
    if pending_streams:
        print(f"\n📬 Consumer groups with PENDING messages:")
        for stream, group, pending in pending_streams[:10]:
            print(f"    - {stream} / {group}: {pending} pending")
    else:
        print(f"\n✅ No pending messages (all consumers are caught up)")
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    
    total_groups = sum(len(info['groups']) for info in topology.values())
    total_events = sum(info['length'] for info in topology.values())
    
    print(f"\nTotal Streams: {len(streams)}")
    print(f"Total Consumer Groups: {total_groups}")
    print(f"Total Events (all streams): {total_events}")
    print(f"Streams without consumers: {len(no_consumers)}")
    print(f"Consumer groups with high lag (>100): {len(high_lag)}")
    print(f"Consumer groups with pending messages: {len(pending_streams)}")
    
    # Health score
    health_score = 100
    if no_consumers:
        health_score -= min(30, len(no_consumers) * 2)
    if high_lag:
        health_score -= min(30, len(high_lag) * 5)
    if pending_streams:
        health_score -= min(20, len(pending_streams))
    
    print(f"\n🏥 Bus Health Score: {health_score}/100")
    
    if health_score >= 90:
        print("✅ HEALTHY - Synaptic Bus is operating optimally")
    elif health_score >= 70:
        print("⚠️  WARNING - Minor issues detected")
    else:
        print("❌ CRITICAL - Significant issues require attention")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    try:
        audit_streams()
    except redis.ConnectionError:
        print("❌ Cannot connect to Redis at {}:{}".format(REDIS_HOST, REDIS_PORT))
        print("   Make sure Redis is running and accessible")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
