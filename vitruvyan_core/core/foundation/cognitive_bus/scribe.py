"""
    Chronicle The Scribe of the Synaptic Conclave
Centralized logging and event chronicling

The Scribe records all sacred communications and maintains
the historical record of the cognitive organism.
"""
    
import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import structlog

logger = structlog.get_logger("conclave.scribe")


class EventRecord:
    """
    A single event record in the Scribe's chronicles.
    """
    def __init__(self, domain: str, intent: str, payload: Dict[str, Any], timestamp: str, source: str):
        self.domain = domain
        self.intent = intent
        self.payload = payload
        self.timestamp = timestamp
        self.source = source
        self.event_id = f"{domain}_{intent}_{timestamp.replace(':', '').replace('-', '')}"


class ConclaveScribe:
    """
    The Scribe maintains chronicles of all semantic events.
    """
    
    def __init__(self, log_directory: str = "logs/conclave"):
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        # In-memory recent events (last 1000)
        self.recent_events: List[EventRecord] = []
        self.max_recent_events = 1000
        
        # Daily chronicles
        self.current_date = datetime.utcnow().date()
        self.daily_events = 0
        
        # Event statistics
        self.event_counts: Dict[str, int] = {}
        self.domain_counts: Dict[str, int] = {}
    
    async def chronicle_event(self, domain: str, intent: str, payload: Dict[str, Any], 
                            timestamp: str, source: str):
        """
        Chronicle a semantic event in the sacred records.
        """
        try:
            # Create event record
            event_record = EventRecord(domain, intent, payload, timestamp, source)
            
            # Add to recent events
            self.recent_events.append(event_record)
            if len(self.recent_events) > self.max_recent_events:
                self.recent_events.pop(0)  # Remove oldest
            
            # Update statistics
            event_key = f"{domain}.{intent}"
            self.event_counts[event_key] = self.event_counts.get(event_key, 0) + 1
            self.domain_counts[domain] = self.domain_counts.get(domain, 0) + 1
            self.daily_events += 1
            
            # Write to daily chronicle
            await self._write_to_daily_chronicle(event_record)
            
            # Check if we need to roll over to new day
            current_date = datetime.utcnow().date()
            if current_date != self.current_date:
                await self._roll_over_daily_chronicle()
                self.current_date = current_date
                self.daily_events = 1
            
            logger.debug(
                "Chronicle Event chronicled",
                domain=domain,
                intent=intent,
                event_id=event_record.event_id,
                daily_count=self.daily_events
            )
            
        except Exception as e:
            logger.error(
                "Chronicle Failed to chronicle event",
                domain=domain,
                intent=intent,
                error=str(e)
            )
    
    async def _write_to_daily_chronicle(self, event_record: EventRecord):
        """
        Write event to today's chronicle file.
        """
        try:
            date_str = datetime.utcnow().strftime("%Y-%m-%d")
            chronicle_file = self.log_directory / f"chronicle_{date_str}.jsonl"
            
            # Prepare chronicle entry
            chronicle_entry = {
                "timestamp": event_record.timestamp,
                "event_id": event_record.event_id,
                "domain": event_record.domain,
                "intent": event_record.intent,
                "source": event_record.source,
                "payload": event_record.payload,
                "chronicled_at": datetime.utcnow().isoformat()
            }
            
            # Append to JSONL file
            with open(chronicle_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(chronicle_entry) + '\n')
                
        except Exception as e:
            logger.error("Chronicle Failed to write to daily chronicle", error=str(e))
    
    async def _roll_over_daily_chronicle(self):
        """
        Roll over to a new daily chronicle and archive the previous.
        """
        try:
            yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
            yesterday_file = self.log_directory / f"chronicle_{yesterday}.jsonl"
            
            if yesterday_file.exists():
                # Create daily summary
                summary = await self._create_daily_summary(yesterday_file)
                
                # Write summary
                summary_file = self.log_directory / f"summary_{yesterday}.json"
                with open(summary_file, 'w', encoding='utf-8') as f:
                    json.dump(summary, f, indent=2)
                
                logger.info(
                    "Chronicle Daily chronicle rolled over",
                    date=yesterday,
                    total_events=summary.get("total_events", 0)
                )
            
            # Reset daily counters
            self.daily_events = 0
            
        except Exception as e:
            logger.error("Chronicle Failed to roll over daily chronicle", error=str(e))
    
    async def _create_daily_summary(self, chronicle_file: Path) -> Dict[str, Any]:
        """
        Create a daily summary from the chronicle file.
        """
        summary = {
            "date": chronicle_file.stem.replace("chronicle_", ""),
            "total_events": 0,
            "domain_breakdown": {},
            "intent_breakdown": {},
            "hourly_distribution": {},
            "top_sources": {},
            "created_at": datetime.utcnow().isoformat()
        }
        
        try:
            with open(chronicle_file, 'r', encoding='utf-8') as f:
                for line in f:
                    event = json.loads(line.strip())
                    summary["total_events"] += 1
                    
                    # Domain breakdown
                    domain = event.get("domain", "unknown")
                    summary["domain_breakdown"][domain] = summary["domain_breakdown"].get(domain, 0) + 1
                    
                    # Intent breakdown
                    intent = event.get("intent", "unknown")
                    summary["intent_breakdown"][intent] = summary["intent_breakdown"].get(intent, 0) + 1
                    
                    # Hourly distribution
                    timestamp = event.get("timestamp", "")
                    if timestamp:
                        hour = timestamp.split("T")[1][:2] if "T" in timestamp else "00"
                        summary["hourly_distribution"][hour] = summary["hourly_distribution"].get(hour, 0) + 1
                    
                    # Source tracking
                    source = event.get("source", "unknown")
                    summary["top_sources"][source] = summary["top_sources"].get(source, 0) + 1
                        
        except Exception as e:
            logger.error("Chronicle Failed to create daily summary", error=str(e))
        
        return summary
    
    def get_recent_events(self, limit: int = 100, domain_filter: str = None) -> List[Dict[str, Any]]:
        """
        Get recent events from memory.
        """
        events = self.recent_events
        
        # Apply domain filter if specified
        if domain_filter:
            events = [e for e in events if e.domain == domain_filter]
        
        # Limit results
        events = events[-limit:] if len(events) > limit else events
        
        # Convert to dict format
        return [
            {
                "timestamp": event.timestamp,
                "event_id": event.event_id,
                "domain": event.domain,
                "intent": event.intent,
                "source": event.source,
                "payload": event.payload
            }
            for event in events
        ]
    
    def get_event_statistics(self) -> Dict[str, Any]:
        """
        Get current event statistics.
        """
        return {
            "recent_events_count": len(self.recent_events),
            "daily_events_count": self.daily_events,
            "current_date": self.current_date.isoformat(),
            "top_events": dict(sorted(self.event_counts.items(), 
                                    key=lambda x: x[1], reverse=True)[:10]),
            "domain_distribution": dict(sorted(self.domain_counts.items(), 
                                             key=lambda x: x[1], reverse=True)),
            "total_unique_events": len(self.event_counts),
            "total_domains": len(self.domain_counts)
        }
    
    async def search_chronicles(self, date: str, domain: str = None, 
                              intent: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search historical chronicles for specific events.
        """
        results = []
        
        try:
            chronicle_file = self.log_directory / f"chronicle_{date}.jsonl"
            
            if not chronicle_file.exists():
                return results
            
            with open(chronicle_file, 'r', encoding='utf-8') as f:
                for line in f:
                    event = json.loads(line.strip())
                    
                    # Apply filters
                    if domain and event.get("domain") != domain:
                        continue
                    if intent and event.get("intent") != intent:
                        continue
                    
                    results.append(event)
                    
                    if len(results) >= limit:
                        break
                        
        except Exception as e:
            logger.error("Chronicle Failed to search chronicles", date=date, error=str(e))
        
        return results
    
    async def get_chronicle_health(self) -> Dict[str, Any]:
        """
        Get health status of chronicle system.
        """
        return {
            "log_directory": str(self.log_directory),
            "log_directory_exists": self.log_directory.exists(),
            "recent_events_count": len(self.recent_events),
            "daily_events_count": self.daily_events,
            "current_date": self.current_date.isoformat(),
            "chronicle_files": len(list(self.log_directory.glob("chronicle_*.jsonl"))),
            "summary_files": len(list(self.log_directory.glob("summary_*.json"))),
            "total_tracked_events": len(self.event_counts),
            "total_tracked_domains": len(self.domain_counts),
            "last_event_time": self.recent_events[-1].timestamp if self.recent_events else None
        }


# Global Scribe instance
_scribe: Optional[ConclaveScribe] = None

async def get_scribe() -> ConclaveScribe:
    """
    Get the global Scribe instance.
    """
    global _scribe
    if _scribe is None:
        _scribe = ConclaveScribe()
    return _scribe