"""
Unit tests for BaseContract, ContractMeta, ContractRegistry, IContractPlugin.

Run: pytest tests/unit/contracts/test_base_contract.py -v
"""

from __future__ import annotations

import warnings
from typing import ClassVar, List

import pytest
from pydantic import ValidationError

from contracts.base import (
    BaseContract,
    ContractMeta,
    ContractRegistry,
    IContractPlugin,
)


# ─────────────────────────────────────────────────────────────
# Fixtures / helpers
# ─────────────────────────────────────────────────────────────

class _SimpleContract(BaseContract):
    CONTRACT_NAME: ClassVar[str]    = "test.simple"
    CONTRACT_VERSION: ClassVar[str] = "1.0.0"
    CONTRACT_OWNER: ClassVar[str]   = "test_order"

    value: str = "hello"


class _ContractWithInvariants(BaseContract):
    CONTRACT_NAME: ClassVar[str]    = "test.with_invariants"
    CONTRACT_VERSION: ClassVar[str] = "1.0.0"
    CONTRACT_OWNER: ClassVar[str]   = "test_order"

    positive: float = 1.0

    def validate_invariants(self) -> List[str]:
        violations: List[str] = []
        if self.positive <= 0:
            violations.append(f"positive must be > 0, got {self.positive}")
        return violations


class _ContractV2(_SimpleContract):
    CONTRACT_NAME: ClassVar[str]    = "test.simple"
    CONTRACT_VERSION: ClassVar[str] = "2.0.0"

    extra_field: str = "extra"


# ─────────────────────────────────────────────────────────────
# ContractMeta
# ─────────────────────────────────────────────────────────────

class TestContractMeta:
    def test_basic_creation(self) -> None:
        meta = ContractMeta(contract_name="foo", contract_version="1.2.3")
        assert meta.contract_name == "foo"
        assert meta.contract_version == "1.2.3"
        assert meta.owner == "core"
        assert meta.created_at is not None

    def test_custom_owner(self) -> None:
        meta = ContractMeta(
            contract_name="bar",
            contract_version="0.1.0",
            owner="pattern_weavers",
        )
        assert meta.owner == "pattern_weavers"

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            ContractMeta(
                contract_name="x",
                contract_version="1.0.0",
                unknown_field="oops",  # type: ignore[call-arg]
            )


# ─────────────────────────────────────────────────────────────
# BaseContract — identity
# ─────────────────────────────────────────────────────────────

class TestBaseContractIdentity:
    def test_contract_id(self) -> None:
        assert _SimpleContract.contract_id() == "test.simple@1.0.0"

    def test_contract_id_v2(self) -> None:
        assert _ContractV2.contract_id() == "test.simple@2.0.0"

    def test_class_vars_accessible_on_instance(self) -> None:
        c = _SimpleContract()
        assert c.CONTRACT_NAME == "test.simple"
        assert c.CONTRACT_VERSION == "1.0.0"
        assert c.CONTRACT_OWNER == "test_order"

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            _SimpleContract(value="hi", unknown="not_allowed")  # type: ignore[call-arg]


# ─────────────────────────────────────────────────────────────
# BaseContract — validate_invariants + enforce
# ─────────────────────────────────────────────────────────────

class TestBaseContractEnforce:
    def test_no_violations(self) -> None:
        c = _ContractWithInvariants(positive=5.0)
        returned = c.enforce(strict=True)
        assert returned is c  # chaining

    def test_violation_strict_raises(self) -> None:
        c = _ContractWithInvariants(positive=-1.0)
        with pytest.raises(ValueError, match="positive must be > 0"):
            c.enforce(strict=True)

    def test_violation_warn_mode(self) -> None:
        c = _ContractWithInvariants(positive=-1.0)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = c.enforce(strict=False)
        # Should not raise; should return self
        assert result is c

    def test_no_invariants_base_class(self) -> None:
        c = _SimpleContract()
        assert c.validate_invariants() == []

    def test_enforce_returns_self_for_chaining(self) -> None:
        c = _SimpleContract()
        assert c.enforce() is c

    def test_multiple_violations_all_reported(self) -> None:
        class _MultiViolation(BaseContract):
            CONTRACT_NAME: ClassVar[str] = "test.multi_v"
            CONTRACT_VERSION: ClassVar[str] = "1.0.0"
            CONTRACT_OWNER: ClassVar[str] = "test"

            a: int = 0
            b: int = 0

            def validate_invariants(self) -> List[str]:
                v: List[str] = []
                if self.a < 0:
                    v.append("a < 0")
                if self.b < 0:
                    v.append("b < 0")
                return v

        c = _MultiViolation(a=-1, b=-2)
        with pytest.raises(ValueError) as exc_info:
            c.enforce(strict=True)
        assert "a < 0" in str(exc_info.value)
        assert "b < 0" in str(exc_info.value)


# ─────────────────────────────────────────────────────────────
# BaseContract — get_meta
# ─────────────────────────────────────────────────────────────

class TestBaseContractMeta:
    def test_get_meta_fields(self) -> None:
        c = _SimpleContract()
        meta = c.get_meta()
        assert meta.contract_name == "test.simple"
        assert meta.contract_version == "1.0.0"
        assert meta.owner == "test_order"
        assert len(meta.schema_hash) == 16

    def test_get_meta_deterministic(self) -> None:
        c1 = _SimpleContract()
        c2 = _SimpleContract(value="world")
        # Schema hash depends on class schema, not instance values
        assert c1.get_meta().schema_hash == c2.get_meta().schema_hash


# ─────────────────────────────────────────────────────────────
# BaseContract — serialization
# ─────────────────────────────────────────────────────────────

class TestBaseContractSerialization:
    def test_to_dict_basic(self) -> None:
        c = _SimpleContract(value="test_val")
        d = c.to_dict()
        assert d["value"] == "test_val"
        assert "__contract_meta__" not in d

    def test_to_dict_with_meta(self) -> None:
        c = _SimpleContract(value="test_val")
        d = c.to_dict(include_meta=True)
        assert "__contract_meta__" in d
        assert d["__contract_meta__"]["contract_name"] == "test.simple"
        assert d["__contract_meta__"]["contract_version"] == "1.0.0"

    def test_from_dict_roundtrip(self) -> None:
        c1 = _SimpleContract(value="roundtrip")
        d = c1.to_dict()
        c2 = _SimpleContract.from_dict(d)
        assert c2.value == "roundtrip"

    def test_from_dict_strips_meta(self) -> None:
        c1 = _SimpleContract(value="strip_meta")
        d = c1.to_dict(include_meta=True)
        # Should not fail even though __contract_meta__ is present
        c2 = _SimpleContract.from_dict(d)
        assert c2.value == "strip_meta"

    def test_from_dict_version_check_warning(self) -> None:
        c = _SimpleContract(value="old")
        d = c.to_dict(include_meta=True)
        # Tamper with stored version
        d["__contract_meta__"]["contract_version"] = "0.1.0"
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _SimpleContract.from_dict(d, version_check=True)
        assert any("0.1.0" in str(w.message) for w in caught)

    def test_from_dict_no_version_check(self) -> None:
        c = _SimpleContract(value="no_warn")
        d = c.to_dict(include_meta=True)
        d["__contract_meta__"]["contract_version"] = "99.0.0"
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _SimpleContract.from_dict(d, version_check=False)
        assert not any("99.0.0" in str(w.message) for w in caught)


# ─────────────────────────────────────────────────────────────
# ContractRegistry
# ─────────────────────────────────────────────────────────────

class TestContractRegistry:
    def test_simple_registered(self) -> None:
        assert ContractRegistry.is_registered("test.simple")

    def test_with_invariants_registered(self) -> None:
        assert ContractRegistry.is_registered("test.with_invariants")

    def test_get_by_contract_id(self) -> None:
        cls = ContractRegistry.get("test.simple@1.0.0")
        assert cls is _SimpleContract

    def test_get_unknown_returns_none(self) -> None:
        assert ContractRegistry.get("no.such.contract@0.0.0") is None

    def test_list_all_returns_dict(self) -> None:
        all_contracts = ContractRegistry.list_all()
        assert isinstance(all_contracts, dict)
        assert "test.simple@1.0.0" in all_contracts

    def test_is_registered_false_for_unknown(self) -> None:
        assert not ContractRegistry.is_registered("totally.unknown.contract")

    def test_multiple_versions_coexist(self) -> None:
        assert ContractRegistry.get("test.simple@1.0.0") is _SimpleContract
        assert ContractRegistry.get("test.simple@2.0.0") is _ContractV2


# ─────────────────────────────────────────────────────────────
# IContractPlugin
# ─────────────────────────────────────────────────────────────

class TestIContractPlugin:
    def test_plugin_contract_id(self) -> None:
        class _TestPlugin(IContractPlugin):
            PLUGIN_CONTRACT_NAME: ClassVar[str]    = "my_plugin"
            PLUGIN_CONTRACT_VERSION: ClassVar[str] = "1.0.0"

        assert _TestPlugin.plugin_contract_id() == "my_plugin@1.0.0"

    def test_default_id_base(self) -> None:
        assert IContractPlugin.plugin_contract_id() == "base_plugin@0.0.0"

    def test_concrete_subclass_instantiates(self) -> None:
        """IContractPlugin has no abstract methods — concrete subclasses are fine."""
        class _ConcretePlugin(IContractPlugin):
            pass

        p = _ConcretePlugin()
        assert p.plugin_contract_id() == "base_plugin@0.0.0"
