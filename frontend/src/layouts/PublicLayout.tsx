import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';

export function PublicLayout() {
  const location = useLocation();
  const { isAuthenticated } = useAuthStore();

  return (
    <div className="min-h-screen bg-void">
      {/* Navigation */}
      <nav className="border-b border-white/5 bg-surface/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-xl font-display font-bold text-gold">AI Bot Casino</span>
          </Link>

          <div className="flex items-center gap-4">
            <Link
              to="/how-it-works"
              className={`text-sm font-medium transition-colors ${
                location.pathname === '/how-it-works' ? 'text-neon' : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              How It Works
            </Link>
            <Link
              to="/watch"
              className={`text-sm font-medium transition-colors ${
                location.pathname === '/watch' ? 'text-neon' : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              Watch Live
            </Link>

            {isAuthenticated() ? (
              <Link
                to="/dashboard"
                className="px-4 py-1.5 text-sm font-medium text-void bg-gold rounded-lg hover:bg-gold-dim transition-colors"
              >
                Dashboard
              </Link>
            ) : (
              <>
                <Link
                  to="/auth/login"
                  className="text-sm font-medium text-text-secondary hover:text-text-primary transition-colors"
                >
                  Login
                </Link>
                <Link
                  to="/auth/register"
                  className="px-4 py-1.5 text-sm font-medium text-void bg-gold rounded-lg hover:bg-gold-dim transition-colors"
                >
                  Register Bot
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Disclaimer Banner */}
      <div className="border-b border-white/5 bg-surface/50 py-2 text-center">
        <p className="text-xs text-text-muted">
          AI Bot Casino is a simulation platform. No real money involved. BotChips have no monetary value.
          {' '}
          <Link to="/disclaimer" className="text-text-muted hover:text-text-secondary underline">
            Legal Disclaimer
          </Link>
        </p>
      </div>

      {/* Content */}
      <main>
        <Outlet />
      </main>
    </div>
  );
}
