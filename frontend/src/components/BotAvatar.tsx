interface BotAvatarProps {
  seed: string;
  size?: number;
  className?: string;
}

export function BotAvatar({ seed, size = 32, className = '' }: BotAvatarProps) {
  return (
    <img
      src={`https://api.dicebear.com/7.x/bottts/svg?seed=${seed}&backgroundColor=transparent`}
      alt="Bot avatar"
      className={`rounded-full bg-elevated ${className}`}
      style={{ width: size, height: size }}
    />
  );
}
