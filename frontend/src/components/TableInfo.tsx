import { useGameStore } from '@/store/gameStore';

export function TableInfo() {
  const { seatedBots, roundNumber, phase } = useGameStore();
  const totalWageredToday = useGameStore((s) => s.currentBets.reduce((sum, b) => sum + b.amount, 0));

  return (
    <div className="w-full bg-card rounded-xl border border-white/5 p-3.5">
      <div className="flex justify-between items-center mb-1.5">
        <span className="text-xs text-text-muted font-mono">TABLE #1</span>
        <span className={`text-xs font-mono ${phase !== 'idle' ? 'text-neon' : 'text-text-muted'}`}>
          {phase !== 'idle' ? '● LIVE' : '○ IDLE'}
        </span>
      </div>
      <div className="flex justify-between">
        <div>
          <div className="text-xl font-bold text-text-primary font-display">{seatedBots.length}</div>
          <div className="text-[10px] text-text-muted">Bots Seated</div>
        </div>
        <div>
          <div className="text-xl font-bold text-gold font-display">{roundNumber}</div>
          <div className="text-[10px] text-text-muted">Round</div>
        </div>
        <div>
          <div className="text-xl font-bold text-text-primary font-display">{totalWageredToday}</div>
          <div className="text-[10px] text-text-muted">Wagered</div>
        </div>
      </div>
    </div>
  );
}
