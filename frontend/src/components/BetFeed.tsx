import { useGameStore } from '@/store/gameStore';
import { BotAvatar } from './BotAvatar';
import { Trophy } from 'lucide-react';

export function BetFeed() {
  const phase = useGameStore((s) => s.phase);
  const currentBets = useGameStore((s) => s.currentBets);
  const latestResult = useGameStore((s) => s.latestResult);

  const showResults = (phase === 'settlement' || phase === 'pause') && latestResult && latestResult.bets.length > 0;

  // During settlement/pause, show round results; otherwise show live bets
  if (showResults) {
    const bets = latestResult.bets;
    const winners = bets.filter((b) => b.is_winner);
    const losers = bets.filter((b) => !b.is_winner);

    return (
      <div className="bg-card rounded-xl border border-white/5 p-4 h-full">
        <div className="text-xs text-text-muted font-mono tracking-wider mb-3">
          ROUND #{latestResult.round_number} RESULTS
        </div>
        <div className="space-y-2 overflow-y-auto max-h-[400px]">
          {winners.length > 0 && (
            <>
              {winners.map((bet, i) => {
                const net = bet.payout - bet.amount;
                return (
                  <div key={`w-${i}`} className="flex items-center gap-3 bg-neon/5 border border-neon/20 rounded-lg px-3 py-2">
                    <BotAvatar seed={bet.bot_avatar_seed} size={28} />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm text-text-primary truncate flex items-center gap-1.5">
                        {bet.bot_name}
                        <Trophy className="w-3.5 h-3.5 text-gold" />
                      </div>
                    </div>
                    <div className="text-right flex items-baseline gap-2">
                      <span className={`text-xs font-medium ${getBetColor(bet.bet_type)}`}>
                        {formatBetType(bet.bet_type, bet.bet_value)}
                      </span>
                      <span className="text-sm font-bold text-neon font-mono">
                        +{net} BC
                      </span>
                    </div>
                  </div>
                );
              })}
            </>
          )}
          {losers.length > 0 && (
            <>
              {losers.map((bet, i) => (
                <div key={`l-${i}`} className="flex items-center gap-3 bg-surface/50 rounded-lg px-3 py-2 opacity-70">
                  <BotAvatar seed={bet.bot_avatar_seed} size={28} />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-text-secondary truncate">{bet.bot_name}</div>
                  </div>
                  <div className="text-right flex items-baseline gap-2">
                    <span className={`text-xs font-medium ${getBetColor(bet.bet_type)}`}>
                      {formatBetType(bet.bet_type, bet.bet_value)}
                    </span>
                    <span className="text-sm font-bold text-accent-red font-mono">
                      -{bet.amount} BC
                    </span>
                  </div>
                </div>
              ))}
            </>
          )}
          {/* Summary line */}
          <div className="pt-2 mt-2 border-t border-white/5 flex justify-between text-xs font-mono text-text-muted">
            <span>Wagered: {latestResult.total_wagered} BC</span>
            <span>Paid out: {latestResult.total_payout} BC</span>
          </div>
        </div>
      </div>
    );
  }

  // Live bets view (during betting/spinning)
  const displayBets = [...currentBets].reverse().slice(0, 10);

  const emptyMessage = phase === 'betting'
    ? 'Waiting for bets...'
    : phase === 'spinning'
      ? 'No bets this round'
      : 'Waiting for next round...';

  return (
    <div className="bg-card rounded-xl border border-white/5 p-4 h-full">
      <div className="text-xs text-text-muted font-mono tracking-wider mb-3">LIVE BETS</div>
      <div className="space-y-2 overflow-y-auto max-h-[400px]">
        {displayBets.length === 0 ? (
          <div className="text-text-muted text-sm py-4 text-center">
            {emptyMessage}
          </div>
        ) : (
          displayBets.map((bet, i) => (
            <div key={i} className="flex items-center gap-3 bg-surface/50 rounded-lg px-3 py-2 animate-slide-in">
              <BotAvatar seed={bet.bot_avatar_seed} size={28} />
              <div className="flex-1 min-w-0">
                <div className="text-sm text-text-primary truncate">{bet.bot_name}</div>
              </div>
              <div className="text-right flex items-baseline gap-2">
                <span className={`text-xs font-medium ${getBetColor(bet.bet_type)}`}>
                  {formatBetType(bet.bet_type, bet.bet_value)}
                </span>
                <span className="text-sm font-bold text-gold font-mono">
                  {bet.amount} BC
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function formatBetType(type: string, value?: number): string {
  if (type === 'straight' && value !== undefined) return `Straight ${value}`;
  return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function getBetColor(type: string): string {
  switch (type) {
    case 'red': return 'text-roulette-red';
    case 'black': return 'text-text-primary';
    case 'even':
    case 'odd': return 'text-accent-blue';
    case 'dozen_1':
    case 'dozen_2':
    case 'dozen_3': return 'text-neon';
    case 'straight': return 'text-gold';
    default: return 'text-text-muted';
  }
}
