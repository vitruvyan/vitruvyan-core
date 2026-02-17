"""Runtime dependency builders for Edge Oculus Prime API."""

from __future__ import annotations

import logging

from vitruvyan_core.core.agents.postgres_agent import PostgresAgent
from vitruvyan_core.core.synaptic_conclave.transport.streams import StreamBus
from infrastructure.edge.oculus_prime.core.event_emitter import OculusPrimeEventEmitter

from ..config import OculusPrimeSettings

logger = logging.getLogger(__name__)


def build_stream_bus(settings: OculusPrimeSettings) -> StreamBus | None:
    try:
        stream_bus = StreamBus(
            host=settings.redis_host,
            port=settings.redis_port,
        )
        logger.info("StreamBus connected: %s:%s", settings.redis_host, settings.redis_port)
        return stream_bus
    except Exception as exc:
        logger.warning("StreamBus unavailable: %s. Events will be persisted as failures.", exc)
        return None


def build_postgres_agent(settings: OculusPrimeSettings) -> PostgresAgent:
    return PostgresAgent(
        host=settings.postgres_host,
        port=settings.postgres_port,
        dbname=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
    )


def build_runtime_dependencies(
    settings: OculusPrimeSettings,
    stream_bus: StreamBus | None,
) -> tuple[PostgresAgent, OculusPrimeEventEmitter]:
    postgres = build_postgres_agent(settings)
    emitter = OculusPrimeEventEmitter(
        stream_bus=stream_bus,
        postgres_agent=postgres,
        migration_mode=settings.event_migration_mode,
    )
    return postgres, emitter


# Legacy alias kept to avoid breaking existing imports.
IntakeSettings = OculusPrimeSettings
