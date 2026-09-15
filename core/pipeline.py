from .domain import Offer, Signal, Opportunity, SimulationResult
from .scoring import score_offer
from .simulation import simulate


def evaluate(offers: list[Offer], signals: list[Signal], country: str = "DZ") -> list[tuple[Opportunity, SimulationResult]]:
    """Evaluate matching offer/signal pairs without external side effects."""
    results = []
    for signal in signals:
        for offer in offers:
            opportunity = score_offer(offer, signal, country)
            results.append((opportunity, simulate(opportunity, offer)))
    return sorted(results, key=lambda item: item[0].score, reverse=True)
