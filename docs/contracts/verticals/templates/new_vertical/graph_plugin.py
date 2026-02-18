"""Domain graph plugin template."""

from contracts import GraphPlugin


class ExampleGraphPlugin(GraphPlugin):
    def get_domain_name(self) -> str:
        return "example"

    def get_state_extensions(self):
        return {}

    def get_nodes(self):
        return {}

    def get_route_map(self):
        return {}

    def get_intents(self):
        return []

    def get_entry_pipeline(self):
        return []

    def get_post_routing_edges(self):
        return []


def get_example_plugin() -> ExampleGraphPlugin:
    return ExampleGraphPlugin()

