import { useGameStore } from '@/store/gameStore';
import { BotAvatar } from './BotAvatar';
import { MessageCircle } from 'lucide-react';

export function ChatFeed() {
  const chatMessages = useGameStore((s) => s.chatMessages);

  const displayMessages = chatMessages.slice(-30);

  return (
    <div className="bg-card rounded-xl border border-white/5 p-4 h-full">
      <div className="flex items-center gap-1.5 mb-3">
        <MessageCircle className="w-3.5 h-3.5 text-text-muted" />
        <div className="text-xs text-text-muted font-mono tracking-wider">BOT CHAT</div>
      </div>
      <div className="space-y-1 overflow-y-auto max-h-[300px]">
        {displayMessages.length === 0 ? (
          <div className="text-text-muted text-sm py-4 text-center">
            No messages yet...
          </div>
        ) : (
          displayMessages.map((msg, i) => (
            <div key={`chat-${i}`} className="flex items-start gap-2.5 px-2 py-1.5 rounded-lg hover:bg-surface/30 transition-colors animate-slide-in">
              <BotAvatar seed={msg.bot_avatar_seed} size={22} />
              <div className="flex-1 min-w-0">
                <span className="text-xs text-gold font-mono">{msg.bot_name}</span>
                <p className="text-xs text-text-secondary leading-relaxed">{msg.message}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
