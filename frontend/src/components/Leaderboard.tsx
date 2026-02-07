import { useGameStore } from '@/store/gameStore';
import { BotAvatar } from './BotAvatar';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export function Leaderboard() {
  const leaderboard = useGameStore((s) => s.leaderboard);

  const medals = ['🥇', '🥈', '🥉'];

  return (
    <div className="bg-card rounded-xl border border-white/5 p-4 h-full">
      <div className="text-xs text-text-muted font-mono tracking-wider mb-3">LEADERBOARD</div>
      <div className="space-y-2 overflow-y-auto max-h-[400px]">
        {leaderboard.length === 0 ? (
          <div className="text-text-muted text-sm py-4 text-center">
            No bots registered yet
          </div>
        ) : (
          leaderboard.map((bot, i) => (
            <div key={bot.bot_id} className="flex items-center gap-3 bg-surface/50 rounded-lg px-3 py-2">
              <span className="text-sm w-6 text-center">
                {i < 3 ? medals[i] : <span className="text-text-muted">#{i + 1}</span>}
              </span>
              <BotAvatar seed={bot.avatar_seed} size={28} />
              <div className="flex-1 min-w-0">
                <div className="text-sm text-text-primary truncate">{bot.name}</div>
                <div className="text-xs text-text-muted">
                  {bot.rounds_played} rounds
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-gold font-mono">
                  {bot.balance.toLocaleString()}
                </span>
                {bot.trend === 'up' && <TrendingUp size={14} className="text-neon" />}
                {bot.trend === 'down' && <TrendingDown size={14} className="text-accent-red" />}
                {bot.trend === 'neutral' && <Minus size={14} className="text-text-muted" />}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
