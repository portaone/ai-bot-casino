"""
Betting strategies for the AI Bot Casino test bot.
Each strategy implements decide() to choose a bet and optionally on_result() to adapt.
"""
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Tuple, List


RED_NUMBERS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
BLACK_NUMBERS = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}


@dataclass
class BotState:
    """Current bot state exposed to strategies."""
    balance: int = 1000
    rounds_played: int = 0
    total_wagered: int = 0
    total_won: int = 0
    wins: int = 0
    losses: int = 0
    consecutive_losses: int = 0
    consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    max_consecutive_wins: int = 0
    last_result: Optional[int] = None
    last_color: Optional[str] = None
    history: List[int] = field(default_factory=list)

    @property
    def win_rate(self) -> float:
        if self.rounds_played == 0:
            return 0.0
        return (self.wins / self.rounds_played) * 100

    @property
    def net_profit(self) -> int:
        return self.total_won - self.total_wagered

    def update_after_round(self, result_number: int, result_color: str, won: bool, payout: int, wagered: int):
        """Update state after a round completes."""
        self.rounds_played += 1
        self.total_wagered += wagered
        self.last_result = result_number
        self.last_color = result_color
        self.history.append(result_number)
        if len(self.history) > 100:
            self.history = self.history[-100:]

        if won:
            self.total_won += payout
            self.wins += 1
            self.consecutive_wins += 1
            self.consecutive_losses = 0
            if self.consecutive_wins > self.max_consecutive_wins:
                self.max_consecutive_wins = self.consecutive_wins
        else:
            self.losses += 1
            self.consecutive_losses += 1
            self.consecutive_wins = 0
            if self.consecutive_losses > self.max_consecutive_losses:
                self.max_consecutive_losses = self.consecutive_losses


class BaseStrategy(ABC):
    """Abstract base class for betting strategies."""

    name: str = "base"
    description: str = ""

    @abstractmethod
    def decide(self, state: BotState) -> Optional[Tuple[str, Optional[int], int]]:
        """
        Decide what bet to place.

        Returns:
            Tuple of (bet_type, bet_value, amount) or None to skip this round.
            bet_type: "straight", "red", "black", "even", "odd", "dozen_1", "dozen_2", "dozen_3"
            bet_value: number 0-36 for straight bets, None for others
            amount: bet amount in BotChips
        """
        pass

    def on_result(self, number: int, color: str, won: bool, state: BotState):
        """Called after each round. Override for stateful strategies."""
        pass


class FlatRedStrategy(BaseStrategy):
    name = "flat-red"
    description = "Always bet on red with fixed amount"

    def __init__(self, bet_size: int = 10):
        self.bet_size = bet_size

    def decide(self, state: BotState) -> Optional[Tuple[str, Optional[int], int]]:
        if state.balance < self.bet_size:
            return None
        return ("red", None, self.bet_size)


class FlatBlackStrategy(BaseStrategy):
    name = "flat-black"
    description = "Always bet on black with fixed amount"

    def __init__(self, bet_size: int = 10):
        self.bet_size = bet_size

    def decide(self, state: BotState) -> Optional[Tuple[str, Optional[int], int]]:
        if state.balance < self.bet_size:
            return None
        return ("black", None, self.bet_size)


class FlatEvenStrategy(BaseStrategy):
    name = "flat-even"
    description = "Always bet on even with fixed amount"

    def __init__(self, bet_size: int = 10):
        self.bet_size = bet_size

    def decide(self, state: BotState) -> Optional[Tuple[str, Optional[int], int]]:
        if state.balance < self.bet_size:
            return None
        return ("even", None, self.bet_size)


class FlatOddStrategy(BaseStrategy):
    name = "flat-odd"
    description = "Always bet on odd with fixed amount"

    def __init__(self, bet_size: int = 10):
        self.bet_size = bet_size

    def decide(self, state: BotState) -> Optional[Tuple[str, Optional[int], int]]:
        if state.balance < self.bet_size:
            return None
        return ("odd", None, self.bet_size)


class FlatDozenStrategy(BaseStrategy):
    name = "flat-dozen"
    description = "Rotate through 1st, 2nd, 3rd dozen"

    def __init__(self, bet_size: int = 10):
        self.bet_size = bet_size
        self._round = 0

    def decide(self, state: BotState) -> Optional[Tuple[str, Optional[int], int]]:
        if state.balance < self.bet_size:
            return None
        dozens = ["dozen_1", "dozen_2", "dozen_3"]
        bet_type = dozens[self._round % 3]
        self._round += 1
        return (bet_type, None, self.bet_size)


class FlatNumberStrategy(BaseStrategy):
    name = "flat-number"
    description = "Always bet on a single lucky number"

    def __init__(self, bet_size: int = 10, lucky_number: int = None):
        self.bet_size = bet_size
        self.lucky_number = lucky_number if lucky_number is not None else random.randint(0, 36)

    def decide(self, state: BotState) -> Optional[Tuple[str, Optional[int], int]]:
        if state.balance < self.bet_size:
            return None
        return ("straight", self.lucky_number, self.bet_size)


class MartingaleStrategy(BaseStrategy):
    name = "martingale"
    description = "Double bet after loss, reset after win (red/black)"

    def __init__(self, bet_size: int = 10, max_bet: int = 500, color: str = "red"):
        self.base_bet = bet_size
        self.max_bet = max_bet
        self.current_bet = bet_size
        self.color = color

    def decide(self, state: BotState) -> Optional[Tuple[str, Optional[int], int]]:
        bet = min(self.current_bet, state.balance, self.max_bet)
        if bet < 1:
            return None
        return (self.color, None, bet)

    def on_result(self, number: int, color: str, won: bool, state: BotState):
        if won:
            self.current_bet = self.base_bet
        else:
            self.current_bet = min(self.current_bet * 2, self.max_bet)


class ReverseColorStrategy(BaseStrategy):
    name = "reverse-color"
    description = "Bet opposite of last winning color"

    def __init__(self, bet_size: int = 10):
        self.bet_size = bet_size
        self.next_color = "red"  # start with red

    def decide(self, state: BotState) -> Optional[Tuple[str, Optional[int], int]]:
        if state.balance < self.bet_size:
            return None
        return (self.next_color, None, self.bet_size)

    def on_result(self, number: int, color: str, won: bool, state: BotState):
        if color == "red":
            self.next_color = "black"
        elif color == "black":
            self.next_color = "red"
        # On green, keep current bet


class ZeroHunterStrategy(BaseStrategy):
    name = "zero-hunter"
    description = "Always bet on zero (35:1 payout)"

    def __init__(self, bet_size: int = 10):
        self.bet_size = bet_size

    def decide(self, state: BotState) -> Optional[Tuple[str, Optional[int], int]]:
        if state.balance < self.bet_size:
            return None
        return ("straight", 0, self.bet_size)


class JamesBondStrategy(BaseStrategy):
    name = "james-bond"
    description = "Rotate: 50% 3rd dozen, 35% 2nd dozen, 15% zero"

    def __init__(self, bet_size: int = 10):
        self.bet_size = bet_size
        self._round = 0

    def decide(self, state: BotState) -> Optional[Tuple[str, Optional[int], int]]:
        if state.balance < self.bet_size:
            return None

        phase = self._round % 3
        self._round += 1

        if phase == 0:
            # 50% on 3rd dozen
            amount = max(1, int(self.bet_size * 1.5))
            if amount > state.balance:
                amount = state.balance
            return ("dozen_3", None, amount)
        elif phase == 1:
            # 35% on 2nd dozen
            amount = max(1, int(self.bet_size * 1.0))
            if amount > state.balance:
                amount = state.balance
            return ("dozen_2", None, amount)
        else:
            # 15% on zero
            amount = max(1, int(self.bet_size * 0.5))
            if amount > state.balance:
                amount = state.balance
            return ("straight", 0, amount)


class RandomStrategy(BaseStrategy):
    name = "random"
    description = "Randomly pick a different strategy each round"

    def __init__(self, bet_size: int = 10, lucky_number: int = None):
        self.bet_size = bet_size
        self.sub_strategies = [
            FlatRedStrategy(bet_size),
            FlatBlackStrategy(bet_size),
            FlatEvenStrategy(bet_size),
            FlatOddStrategy(bet_size),
            FlatDozenStrategy(bet_size),
            FlatNumberStrategy(bet_size, lucky_number),
            MartingaleStrategy(bet_size),
            ReverseColorStrategy(bet_size),
            ZeroHunterStrategy(bet_size),
            JamesBondStrategy(bet_size),
        ]

    def decide(self, state: BotState) -> Optional[Tuple[str, Optional[int], int]]:
        strategy = random.choice(self.sub_strategies)
        return strategy.decide(state)

    def on_result(self, number: int, color: str, won: bool, state: BotState):
        # Notify all sub-strategies so stateful ones stay updated
        for s in self.sub_strategies:
            s.on_result(number, color, won, state)


# Strategy registry
STRATEGIES = {
    "flat-red": FlatRedStrategy,
    "flat-black": FlatBlackStrategy,
    "flat-even": FlatEvenStrategy,
    "flat-odd": FlatOddStrategy,
    "flat-dozen": FlatDozenStrategy,
    "flat-number": FlatNumberStrategy,
    "martingale": MartingaleStrategy,
    "reverse-color": ReverseColorStrategy,
    "zero-hunter": ZeroHunterStrategy,
    "james-bond": JamesBondStrategy,
    "random": RandomStrategy,
}


def get_strategy(name: str, bet_size: int = 10, lucky_number: int = None) -> BaseStrategy:
    """Create a strategy instance by name."""
    if name not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {name}. Available: {', '.join(STRATEGIES.keys())}")

    cls = STRATEGIES[name]

    # Pass appropriate kwargs based on strategy
    if name == "flat-number":
        return cls(bet_size=bet_size, lucky_number=lucky_number)
    elif name == "martingale":
        return cls(bet_size=bet_size)
    elif name == "random":
        return cls(bet_size=bet_size, lucky_number=lucky_number)
    elif name == "james-bond":
        return cls(bet_size=bet_size)
    else:
        return cls(bet_size=bet_size)
