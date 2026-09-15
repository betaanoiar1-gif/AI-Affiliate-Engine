from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import random
from typing import Iterable


@dataclass(frozen=True)
class StrategyGene:
    hook: str
    angle: str
    format: str
    audience: str
    cta: str

    @property
    def fingerprint(self) -> str:
        raw = "|".join((self.hook, self.angle, self.format, self.audience, self.cta)).encode()
        return hashlib.sha256(raw).hexdigest()[:16]


@dataclass
class StrategyRecord:
    gene: StrategyGene
    exposures: int = 0
    clicks: int = 0
    conversions: int = 0
    revenue: float = 0.0
    failures: int = 0
    parents: tuple[str, ...] = field(default_factory=tuple)

    @property
    def value(self) -> float:
        if self.exposures <= 0:
            return 0.0
        # Revenue per exposure with a small-sample shrinkage prior.
        return (self.revenue + 1.0) / (self.exposures + 100.0)


@dataclass(frozen=True)
class EvolutionDecision:
    selected: str
    exploration: bool
    rationale: str
    candidates: tuple[str, ...]


class StrategyEvolutionEngine:
    """Evidence-driven strategy evolution.

    It creates controlled variants from observed strategies, preserves lineage,
    and uses uncertainty-aware selection so one lucky result cannot take over.
    """

    def __init__(self, seed: int = 17, exploration_rate: float = 0.20) -> None:
        self.rng = random.Random(seed)
        self.exploration_rate = max(0.0, min(1.0, exploration_rate))
        self.records: dict[str, StrategyRecord] = {}

    def register(self, gene: StrategyGene, parents: Iterable[str] = ()) -> StrategyRecord:
        record = self.records.get(gene.fingerprint)
        if record is None:
            record = StrategyRecord(gene=gene, parents=tuple(parents))
            self.records[gene.fingerprint] = record
        return record

    def observe(self, fingerprint: str, *, exposures: int = 0, clicks: int = 0,
                conversions: int = 0, revenue: float = 0.0, failure: bool = False) -> None:
        if fingerprint not in self.records:
            raise KeyError(f"unknown strategy: {fingerprint}")
        if min(exposures, clicks, conversions, revenue) < 0 or clicks > exposures or conversions > clicks:
            raise ValueError("invalid strategy observation")
        r = self.records[fingerprint]
        r.exposures += exposures
        r.clicks += clicks
        r.conversions += conversions
        r.revenue += revenue
        r.failures += int(failure)

    def select(self, *, min_exposures: int = 50) -> EvolutionDecision:
        candidates = [r for r in self.records.values() if r.exposures >= min_exposures]
        if not candidates:
            candidates = list(self.records.values())
        if not candidates:
            raise ValueError("no strategies registered")
        exploration = self.rng.random() < self.exploration_rate
        if exploration:
            selected = self.rng.choice(candidates)
            rationale = "controlled exploration"
        else:
            # Upper-confidence-like bonus rewards promising but uncertain arms.
            total = max(1, sum(r.exposures for r in candidates))
            def rank(r: StrategyRecord) -> float:
                bonus = (2.0 * (max(1, total).bit_length()) / max(1, r.exposures)) ** 0.5
                failure_penalty = min(0.5, r.failures / max(1, r.exposures))
                return r.value + bonus - failure_penalty
            selected = max(candidates, key=rank)
            rationale = "evidence-weighted exploitation with uncertainty bonus"
        return EvolutionDecision(selected.gene.fingerprint, exploration, rationale,
                                 tuple(r.gene.fingerprint for r in candidates))

    def mutate(self, parent_id: str, *, hooks: list[str], angles: list[str], formats: list[str],
               audiences: list[str], ctas: list[str], count: int = 4) -> list[StrategyRecord]:
        if parent_id not in self.records:
            raise KeyError(parent_id)
        if count < 1:
            raise ValueError("count must be positive")
        parent = self.records[parent_id]
        pools = [hooks, angles, formats, audiences, ctas]
        if any(not pool for pool in pools):
            raise ValueError("mutation pools cannot be empty")
        children: list[StrategyRecord] = []
        seen = set(self.records)
        attempts = 0
        while len(children) < count and attempts < count * 20:
            attempts += 1
            gene = StrategyGene(*(self.rng.choice(pool) for pool in pools))
            if gene.fingerprint in seen:
                continue
            seen.add(gene.fingerprint)
            children.append(self.register(gene, parents=(parent_id,)))
        return children

    def lineage(self, fingerprint: str) -> list[str]:
        if fingerprint not in self.records:
            raise KeyError(fingerprint)
        result: list[str] = []
        stack = [fingerprint]
        seen: set[str] = set()
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            result.append(current)
            stack.extend(self.records[current].parents)
        return result
