import { useGameStore } from '@/store/gameStore';
import { BotAvatar } from './BotAvatar';

export function BetFeed() {
  const currentBets = useGameStore((s) => s.currentBets);

  const displayBets = [...currentBets].reverse().slice(0, 10);

  return (
    <div className="bg-card rounded-xl border border-white/5 p-4 h-full">
      <div className="text-xs text-text-muted font-mono tracking-wider mb-3">LIVE BETS</div>
      <div className="space-y-2 overflow-y-auto max-h-[400px]">
        {displayBets.length === 0 ? (
          <div className="text-text-muted text-sm py-4 text-center">
            Waiting for bets...
          </div>
        ) : (
          displayBets.map((bet, i) => (
            <div key={i} className="flex items-center gap-3 bg-surface/50 rounded-lg px-3 py-2 animate-slide-in">
              <BotAvatar seed={bet.bot_avatar_seed} size={28} />
              <div className="flex-1 min-w-0">
                <div className="text-sm text-text-primary truncate">{bet.bot_name}</div>
                <div className="text-xs text-text-muted">
                  {formatBetType(bet.bet_type, bet.bet_value)}
                </div>
              </div>
              <div className="text-sm font-bold text-gold font-mono">
                {bet.amount} BC
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function formatBetType(type: string, value?: number): string {
  if (type === 'straight' && value !== undefined) return `#${value}`;
  return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}
