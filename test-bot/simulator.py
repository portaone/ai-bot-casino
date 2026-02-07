"""
AI Bot Casino - Offline Strategy Simulator

Evaluates betting strategies locally without a running server.
Supports single strategy runs and comparison mode (--all).

Usage:
    python simulator.py --strategy flat-red --rounds 1000
    python simulator.py --all --rounds 10000 --seed 42
"""
import argparse
import random
import sys
from typing import Optional, List, Tuple

from strategies import (
    get_strategy, BotState, STRATEGIES,
    RED_NUMBERS, BLACK_NUMBERS, BaseStrategy,
)


def get_color(number: int) -> str:
    """Get the color of a roulette number."""
    if number == 0:
        return "green"
    return "red" if number in RED_NUMBERS else "black"


def check_win(bet_type: str, bet_value: Optional[int], result: int, color: str) -> bool:
    """Check if a bet wins."""
    if bet_type == "straight":
        return bet_value == result
    elif bet_type == "red":
        return color == "red"
    elif bet_type == "black":
        return color == "black"
    elif bet_type == "even":
        return result != 0 and result % 2 == 0
    elif bet_type == "odd":
        return result != 0 and result % 2 == 1
    elif bet_type == "dozen_1":
        return 1 <= result <= 12
    elif bet_type == "dozen_2":
        return 13 <= result <= 24
    elif bet_type == "dozen_3":
        return 25 <= result <= 36
    return False


PAYOUT_MAP = {
    "straight": 35,
    "red": 1,
    "black": 1,
    "even": 1,
    "odd": 1,
    "dozen_1": 2,
    "dozen_2": 2,
    "dozen_3": 2,
}


def simulate_strategy(
    strategy: BaseStrategy,
    rounds: int,
    starting_balance: int,
    rng: random.Random,
    no_refill: bool = False,
    verbose: bool = False,
) -> dict:
    """Run a simulation for a single strategy."""
    state = BotState(balance=starting_balance)
    peak_balance = starting_balance
    lowest_balance = starting_balance
    refills = 0
    skipped = 0

    for i in range(rounds):
        # Check balance
        if state.balance <= 0:
            if no_refill:
                if verbose:
                    print(f"  Round {i+1}: BANKRUPT - stopping")
                break
            else:
                state.balance = 1000
                refills += 1
                if verbose:
                    print(f"  Round {i+1}: REFILL -> {state.balance} BC")

        # Get strategy decision
        decision = strategy.decide(state)
        if decision is None:
            skipped += 1
            # Still spin the wheel
            result = rng.randint(0, 36)
            color = get_color(result)
            state.update_after_round(result, color, False, 0, 0)
            strategy.on_result(result, color, False, state)
            continue

        bet_type, bet_value, amount = decision

        # Clamp amount to balance
        amount = min(amount, state.balance)
        if amount <= 0:
            skipped += 1
            result = rng.randint(0, 36)
            color = get_color(result)
            state.update_after_round(result, color, False, 0, 0)
            strategy.on_result(result, color, False, state)
            continue

        # Spin the wheel
        result = rng.randint(0, 36)
        color = get_color(result)

        # Check win
        won = check_win(bet_type, bet_value, result, color)

        if won:
            payout_multiplier = PAYOUT_MAP.get(bet_type, 0)
            payout = amount * payout_multiplier + amount  # winnings + original bet back
            state.balance += amount * payout_multiplier  # net gain
        else:
            payout = 0
            state.balance -= amount

        # Track peaks
        if state.balance > peak_balance:
            peak_balance = state.balance
        if state.balance < lowest_balance:
            lowest_balance = state.balance

        state.update_after_round(result, color, won, payout, amount)
        strategy.on_result(result, color, won, state)

        if verbose:
            marker = "WIN" if won else "LOSE"
            net = (payout - amount) if won else -amount
            print(
                f"  Round {i+1}: {result:2d} ({color:5s}) | "
                f"Bet: {amount:4d} on {bet_type:8s}"
                + (f"({bet_value})" if bet_value is not None else "       ")
                + f" | {marker:4s} {net:+5d} | Balance: {state.balance}"
            )

    return {
        "strategy": strategy.name,
        "rounds_played": state.rounds_played,
        "final_balance": state.balance,
        "net_profit": state.net_profit,
        "total_wagered": state.total_wagered,
        "total_won": state.total_won,
        "win_rate": state.win_rate,
        "peak_balance": peak_balance,
        "lowest_balance": lowest_balance,
        "max_win_streak": state.max_consecutive_wins,
        "max_loss_streak": state.max_consecutive_losses,
        "refills": refills,
        "skipped": skipped,
        "roi": (state.net_profit / state.total_wagered * 100) if state.total_wagered > 0 else 0,
    }


def print_result(result: dict):
    """Print formatted simulation result."""
    print(f"\n{'=' * 50}")
    print(f"Strategy: {result['strategy']}")
    print(f"{'=' * 50}")
    print(f"Rounds played:      {result['rounds_played']}")
    print(f"Final balance:      {result['final_balance']} BC")
    print(f"Net profit:         {result['net_profit']:+d} BC")
    print(f"Total wagered:      {result['total_wagered']} BC")
    print(f"Total won:          {result['total_won']} BC")
    print(f"Win rate:           {result['win_rate']:.1f}%")
    print(f"ROI:                {result['roi']:+.2f}%")
    print(f"Peak balance:       {result['peak_balance']} BC")
    print(f"Lowest balance:     {result['lowest_balance']} BC")
    print(f"Max win streak:     {result['max_win_streak']}")
    print(f"Max loss streak:    {result['max_loss_streak']}")
    print(f"Refills:            {result['refills']}")


def print_comparison(results: List[dict]):
    """Print formatted comparison table."""
    print(f"\n{'=' * 100}")
    print("STRATEGY COMPARISON")
    print(f"{'=' * 100}")

    header = f"{'Strategy':<16} {'Rounds':>7} {'Balance':>9} {'Profit':>9} {'Wagered':>9} {'Win%':>6} {'ROI%':>8} {'Peak':>8} {'Low':>8} {'WStrk':>6} {'LStrk':>6}"
    print(header)
    print("-" * 100)

    # Sort by final balance descending
    sorted_results = sorted(results, key=lambda x: x['final_balance'], reverse=True)

    for r in sorted_results:
        print(
            f"{r['strategy']:<16} "
            f"{r['rounds_played']:>7} "
            f"{r['final_balance']:>9} "
            f"{r['net_profit']:>+9} "
            f"{r['total_wagered']:>9} "
            f"{r['win_rate']:>5.1f}% "
            f"{r['roi']:>+7.2f}% "
            f"{r['peak_balance']:>8} "
            f"{r['lowest_balance']:>8} "
            f"{r['max_win_streak']:>6} "
            f"{r['max_loss_streak']:>6}"
        )

    print(f"{'=' * 100}")

    best = sorted_results[0]
    worst = sorted_results[-1]
    print(f"\nBest performer:  {best['strategy']} ({best['net_profit']:+d} BC, {best['roi']:+.2f}% ROI)")
    print(f"Worst performer: {worst['strategy']} ({worst['net_profit']:+d} BC, {worst['roi']:+.2f}% ROI)")

    # Calculate average house edge
    total_wagered = sum(r['total_wagered'] for r in results)
    total_profit = sum(r['net_profit'] for r in results)
    if total_wagered > 0:
        avg_edge = (total_profit / total_wagered) * -100
        print(f"\nAverage house edge: {avg_edge:.2f}% (theoretical: 2.70%)")


def main():
    parser = argparse.ArgumentParser(description="AI Bot Casino - Offline Strategy Simulator")
    parser.add_argument("--strategy", default="random", help="Strategy to simulate (default: random)")
    parser.add_argument("--rounds", type=int, default=100, help="Number of rounds (default: 100)")
    parser.add_argument("--balance", type=int, default=1000, help="Starting balance (default: 1000)")
    parser.add_argument("--bet-size", type=int, default=10, help="Base bet size (default: 10)")
    parser.add_argument("--lucky-number", type=int, default=None, help="Lucky number for flat-number")
    parser.add_argument("--all", action="store_true", help="Compare all strategies")
    parser.add_argument("--no-refill", action="store_true", help="Stop on bankruptcy")
    parser.add_argument("--verbose", action="store_true", help="Print every round")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")

    args = parser.parse_args()

    seed = args.seed if args.seed is not None else random.randint(0, 2**32 - 1)
    print(f"Random seed: {seed}")

    if args.all:
        # Comparison mode - all strategies with shared seed
        results = []
        for name in STRATEGIES:
            rng = random.Random(seed)
            strategy = get_strategy(name, bet_size=args.bet_size, lucky_number=args.lucky_number)
            result = simulate_strategy(
                strategy, args.rounds, args.balance, rng,
                no_refill=args.no_refill, verbose=False,
            )
            results.append(result)

        print_comparison(results)
    else:
        # Single strategy mode
        rng = random.Random(seed)
        strategy = get_strategy(args.strategy, bet_size=args.bet_size, lucky_number=args.lucky_number)
        result = simulate_strategy(
            strategy, args.rounds, args.balance, rng,
            no_refill=args.no_refill, verbose=args.verbose,
        )
        print_result(result)


if __name__ == "__main__":
    main()
