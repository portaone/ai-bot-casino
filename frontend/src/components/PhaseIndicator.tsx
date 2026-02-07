import { useGameStore } from '@/store/gameStore';
import { useEffect, useState } from 'react';

export function PhaseIndicator() {
  const { phase, timeRemaining } = useGameStore();
  const [countdown, setCountdown] = useState(timeRemaining);

  useEffect(() => {
    setCountdown(Math.ceil(timeRemaining));
    if (phase !== 'betting') return;
    const iv = setInterval(() => {
      setCountdown((c) => Math.max(0, c - 1));
    }, 1000);
    return () => clearInterval(iv);
  }, [timeRemaining, phase]);

  const phaseConfig = {
    idle: { label: 'WAITING FOR BOTS', color: 'text-text-muted', bg: 'bg-elevated/50', border: 'border-text-muted/30' },
    betting: { label: 'BETTING OPEN', color: 'text-neon', bg: 'bg-neon/10', border: 'border-neon/30' },
    spinning: { label: 'SPINNING...', color: 'text-gold', bg: 'bg-gold/10', border: 'border-gold/30' },
    settlement: { label: 'SETTLING', color: 'text-accent-red', bg: 'bg-accent-red/10', border: 'border-accent-red/30' },
    pause: { label: 'NEXT ROUND', color: 'text-text-secondary', bg: 'bg-elevated/50', border: 'border-text-muted/30' },
  };

  const config = phaseConfig[phase] || phaseConfig.idle;

  return (
    <div className={`${config.bg} border ${config.border} rounded-lg px-5 py-2 text-center w-full`}>
      <div className={`text-xs font-mono ${config.color} tracking-widest`}>
        {config.label}
      </div>
      {phase === 'betting' && (
        <div className="text-3xl font-extrabold font-display text-text-primary mt-0.5">
          {countdown}s
        </div>
      )}
    </div>
  );
}
