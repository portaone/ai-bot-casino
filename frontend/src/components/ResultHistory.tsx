import { useGameStore } from '@/store/gameStore';
import { getColor, tokens } from '@/tokens';

export function ResultHistory() {
  const resultHistory = useGameStore((s) => s.resultHistory);

  if (resultHistory.length === 0) {
    return (
      <div className="w-full">
        <div className="text-xs text-text-muted font-mono mb-2 tracking-wider">RECENT RESULTS</div>
        <div className="text-text-muted text-sm">No results yet</div>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="text-xs text-text-muted font-mono mb-2 tracking-wider">RECENT RESULTS</div>
      <div className="flex gap-1 flex-wrap">
        {resultHistory.map((n, i) => (
          <div
            key={`${i}-${n}`}
            className="w-[30px] h-[30px] rounded-md flex items-center justify-center text-xs font-bold text-white font-mono"
            style={{
              background: getColor(n),
              opacity: 1 - i * 0.04,
              border: i === 0 ? `1px solid ${tokens.accent.gold}` : '1px solid transparent',
            }}
          >
            {n}
          </div>
        ))}
      </div>
    </div>
  );
}
