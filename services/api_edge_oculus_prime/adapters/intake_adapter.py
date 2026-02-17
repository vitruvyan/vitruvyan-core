"""Compatibility shim for legacy intake adapter imports."""

from .oculus_prime_adapter import IntakeAdapter, OculusPrimeAdapter

__all__ = ["OculusPrimeAdapter", "IntakeAdapter"]
