import { useMemo } from 'react';
import { BotAvatar } from './BotAvatar';

interface AvatarPickerProps {
  onSelect: (seed: string) => void;
  selected?: string;
}

export function AvatarPicker({ onSelect, selected }: AvatarPickerProps) {
  const seeds = useMemo(() =>
    Array.from({ length: 10 }, () => Math.random().toString(36).substring(2, 8)),
    []
  );

  return (
    <div>
      <div className="text-sm text-text-secondary mb-2">Choose your bot's avatar</div>
      <div className="grid grid-cols-5 gap-3">
        {seeds.map((seed) => (
          <button
            key={seed}
            onClick={() => onSelect(seed)}
            className={`p-2 rounded-xl border-2 transition-all ${
              selected === seed
                ? 'border-gold bg-gold/10 scale-105'
                : 'border-white/10 hover:border-white/30 bg-surface'
            }`}
          >
            <BotAvatar seed={seed} size={48} />
          </button>
        ))}
      </div>
    </div>
  );
}
