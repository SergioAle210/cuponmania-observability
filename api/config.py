"""Configuración validada y perfiles probabilísticos de simulación."""

from dataclasses import dataclass
import math
import os
from pathlib import Path
import random
from typing import Mapping


@dataclass(frozen=True)
class Profile:
    success_rate: float
    client_error_rate: float
    server_error_rate: float
    latency_min_ms: float
    latency_max_ms: float

    def __post_init__(self) -> None:
        rates = (self.success_rate, self.client_error_rate, self.server_error_rate)
        if not all(math.isfinite(value) and 0 <= value <= 1 for value in rates):
            raise ValueError("Las probabilidades deben ser finitas y estar entre 0 y 1")
        if not math.isclose(sum(rates), 1, rel_tol=0, abs_tol=1e-9):
            raise ValueError("Las tres probabilidades deben sumar 1")
        if not (math.isfinite(self.latency_min_ms) and math.isfinite(self.latency_max_ms)
                and 0 <= self.latency_min_ms <= self.latency_max_ms <= 10000):
            raise ValueError("Latencias inválidas: se requiere 0 <= min <= max <= 10000 ms")

    def sample(self, rng: random.Random) -> tuple[str, float]:
        choice = rng.random()
        if choice < self.success_rate:
            outcome = "success"
        elif choice < self.success_rate + self.client_error_rate:
            outcome = "client_error"
        else:
            outcome = "server_error"
        return outcome, rng.uniform(self.latency_min_ms, self.latency_max_ms) / 1000


@dataclass(frozen=True)
class Settings:
    log_path: Path
    seed: int | None
    scenario: str
    normal: Profile
    qr: Profile

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        values = os.environ if env is None else env

        def profile(prefix: str, defaults: tuple[float, ...]) -> Profile:
            names = ("SUCCESS_RATE", "CLIENT_ERROR_RATE", "SERVER_ERROR_RATE",
                     "LATENCY_MIN_MS", "LATENCY_MAX_MS")
            try:
                return Profile(*(float(values.get(f"{prefix}_{name}", str(default)))
                                 for name, default in zip(names, defaults)))
            except ValueError as exc:
                raise ValueError(f"Perfil {prefix} inválido: revisar probabilidades y latencias") from exc

        scenario = values.get("API_SCENARIO", "normal")
        if scenario not in ("normal", "qr-degraded"):
            raise ValueError("API_SCENARIO debe ser normal o qr-degraded")
        seed_text = values.get("API_SEED")
        try:
            seed = int(seed_text) if seed_text is not None else None
        except ValueError:
            raise ValueError("API_SEED debe ser un entero") from None
        log_path = values.get("API_LOG_PATH", "logs/api.log")
        if not log_path.strip():
            raise ValueError("API_LOG_PATH no puede estar vacío")
        return cls(Path(log_path), seed, scenario,
                   profile("API", (.90, .05, .05, 80, 350)),
                   profile("QR", (.60, .10, .30, 300, 900)))
