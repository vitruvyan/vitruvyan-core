"""
The Alchemist Agent: Metamorphosis Engine for Archivarium (PostgreSQL).

This agent is responsible for managing database schema migrations using Alembic.
It can:
- Detect inconsistencies between the current database schema and the latest migration.
- Apply migrations to bring the database up to date.
- Emit events to the Cognitive Bus to report its status.
"""

import os
import logging
import ast
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext

# Configure logger
logger = logging.getLogger(__name__)

class AlchemistAgent:
    def __init__(self, cognitive_bus):
        """
        Initializes the Alchemist Agent.

        Args:
            cognitive_bus: An instance of the Cognitive Bus client for event emission.
        """
        self.cognitive_bus = cognitive_bus
        self.alembic_cfg_path = os.getenv("ALEMBIC_CONFIG", "core/governance/memory_orders/migrations/alembic.ini")
        self.alembic_cfg = Config(self.alembic_cfg_path)
        self.script_directory = ScriptDirectory.from_config(self.alembic_cfg)

    def _get_migration_explanation(self, revision: str) -> str | None:
        """VEE Integration: Extracts the docstring from a migration script.
        Args:
            revision: The revision ID of the migration script.
        Returns:
            The docstring as a string, or None if not found.
        """
        try:
            script = self.script_directory.get_revision(revision)
            if not script or not script.path:
                return None
            with open(script.path, "r") as f:
                tree = ast.parse(f.read())
            return ast.get_docstring(tree)
        except Exception as e:
            logger.error(f"[AlchemistAgent] Could not get explanation for revision {revision}: {e}")
            return "Explanation not available due to an error."

    def check_schema_version(self) -> dict:
        """
        Compares the current database schema version with the latest migration version (head).
        Returns a structured dictionary with the status.
        """
        logger.info("Checking schema version...")
        try:
            head_rev = self.script_directory.get_current_head()
            current_rev = None
            with command.EnvironmentContext(self.alembic_cfg, self.script_directory) as context:
                 conn = context.get_context().connection
                 current_rev = context.get_context().get_current_revision()

            if current_rev == head_rev:
                logger.info(f"Schema is up to date at revision: {current_rev}")
                return {"status": "up_to_date", "db_revision": current_rev, "head_revision": head_rev}
            else:
                logger.warning(f"Inconsistency detected. DB: {current_rev}, Head: {head_rev}")
                self.cognitive_bus.publish(
                    "alchemy.inconsistency.detected",
                    {"current_revision": current_rev, "head_revision": head_rev}
                )
                return {"status": "inconsistent", "db_revision": current_rev, "head_revision": head_rev}

        except Exception as e:
            logger.error(f"[AlchemistAgent] Error checking schema version: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    def transmute_schema(self) -> dict:
        """
        Applies all pending migrations to the database to upgrade it to the 'head'.
        Returns a structured dictionary with the result.
        """
        logger.info("Starting schema transmutation...")
        self.cognitive_bus.publish("alchemy.transmutation.start", {})
        try:
            command.upgrade(self.alembic_cfg, "head")
            head_rev = self.script_directory.get_current_head()
            explanation = self._get_migration_explanation(head_rev)
            logger.info("Schema transmutation complete.")
            self.cognitive_bus.publish("alchemy.transmutation.done", {"result": "success", "new_revision": head_rev})
            return {"status": "success", "new_revision": head_rev, "explanation": explanation}
        except Exception as e:
            logger.error(f"[AlchemistAgent] Error during schema transmutation: {e}", exc_info=True)
            self.cognitive_bus.publish("alchemy.transmutation.done", {"result": "failure", "error": str(e)})
            return {"status": "failure", "error": str(e)}

# Example usage (to be integrated into the memory_orders service)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    class MockCognitiveBus:
        def publish(self, channel, data):
            logger.info(f"EVENT PUBLISHED on '{channel}': {data}")

    agent = AlchemistAgent(cognitive_bus=MockCognitiveBus())
    status = agent.check_schema_version()
    logger.info(f"Check status: {status}")

    # To test transmutation:
    # result = agent.transmute_schema()
    # logger.info(f"Transmutation result: {result}")
