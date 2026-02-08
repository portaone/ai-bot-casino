import { useGameStore } from '@/store/gameStore';
import { getColor, tokens } from '@/tokens';

export function ResultHistory() {
  const resultHistory = useGameStore((s) => s.resultHistory);
  const roundHistory = useGameStore((s) => s.roundHistory);
  const selectedRound = useGameStore((s) => s.selectedRound);
  const selectRound = useGameStore((s) => s.selectRound);

  if (resultHistory.length === 0) {
    return (
      <div className="w-full">
        <div className="text-xs text-text-muted font-mono mb-2 tracking-wider">RECENT RESULTS</div>
        <div className="text-text-muted text-sm">No results yet</div>
      </div>
    );
  }

  const handleClick = (index: number) => {
    const round = roundHistory[index];
    if (!round) return;
    // Toggle: click same round again to deselect
    if (selectedRound?.round_number === round.round_number) {
      selectRound(null);
    } else {
      selectRound(round);
    }
  };

  return (
    <div className="w-full">
      <div className="text-xs text-text-muted font-mono mb-2 tracking-wider">RECENT RESULTS</div>
      <div className="flex gap-1 flex-wrap">
        {resultHistory.map((n, i) => {
          const round = roundHistory[i];
          const isSelected = round && selectedRound?.round_number === round.round_number;
          const isClickable = !!round;
          return (
            <div
              key={`${i}-${n}`}
              onClick={() => isClickable && handleClick(i)}
              className={`w-[30px] h-[30px] rounded-md flex items-center justify-center text-xs font-bold text-white font-mono transition-all ${isClickable ? 'cursor-pointer hover:scale-110' : ''}`}
              style={{
                background: getColor(n),
                opacity: 1 - i * 0.04,
                border: isSelected
                  ? `2px solid ${tokens.accent.gold}`
                  : i === 0
                    ? `1px solid ${tokens.accent.gold}`
                    : '1px solid transparent',
                boxShadow: isSelected ? `0 0 8px ${tokens.accent.gold}40` : 'none',
              }}
              title={round ? `Round #${round.round_number} — Click to view details` : undefined}
            >
              {n}
            </div>
          );
        })}
      </div>
    </div>
  );
}
