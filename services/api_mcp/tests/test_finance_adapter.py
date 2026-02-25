import importlib


def _reset_mcp_config():
    config_module = importlib.import_module("config")
    config_module._config = None


def test_finance_adapter_enabled(monkeypatch):
    monkeypatch.setenv("MCP_DOMAIN", "finance")
    _reset_mcp_config()

    adapter_module = importlib.import_module("adapters.finance_adapter")
    assert adapter_module.is_finance_enabled() is True

    adapter = adapter_module.get_finance_adapter()
    assert adapter is not None
    assert adapter.resolve_tool_name("screen_tickers") == "screen_entities"


def test_normalize_finance_tool_request(monkeypatch):
    monkeypatch.setenv("MCP_DOMAIN", "finance")
    _reset_mcp_config()

    tools_module = importlib.import_module("tools")
    tool_name, args = tools_module.normalize_tool_request(
        "query_sentiment",
        {"ticker": "AAPL", "days": 12, "include_phrases": True},
    )

    assert tool_name == "query_signals"
    assert args["entity_id"] == "AAPL"
    assert args["time_window"] == 12
    assert args["include_context"] is True


def test_finance_aliases_registered_in_executor_registry(monkeypatch):
    monkeypatch.setenv("MCP_DOMAIN", "finance")
    _reset_mcp_config()

    tools_module = importlib.import_module("tools")
    executors = tools_module.get_tool_executors()

    assert "screen_tickers" in executors
    assert "compare_tickers" in executors
    assert "query_sentiment" in executors


def test_finance_tool_schemas_exposed(monkeypatch):
    monkeypatch.setenv("MCP_DOMAIN", "finance")
    monkeypatch.setenv("MCP_FINANCE_EXPOSE_LEGACY_TOOLS", "true")
    _reset_mcp_config()

    schemas_module = importlib.import_module("schemas.tools")
    schemas = schemas_module.get_tool_schemas()
    names = {item["function"]["name"] for item in schemas}

    assert "screen_entities" in names
    assert "screen_tickers" in names
    assert "query_signals" in names
    assert "query_sentiment" in names


def test_generic_mode_does_not_expose_finance_alias_tools(monkeypatch):
    monkeypatch.setenv("MCP_DOMAIN", "generic")
    _reset_mcp_config()

    schemas_module = importlib.import_module("schemas.tools")
    schemas = schemas_module.get_tool_schemas()
    names = {item["function"]["name"] for item in schemas}

    assert "screen_entities" in names
    assert "query_signals" in names
    assert "screen_tickers" not in names
    assert "query_sentiment" not in names
