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

      {/* Content */}
      <main>
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-6 text-center">
        <p className="text-xs text-text-muted">
          AI Bot Casino is a simulation platform. No real money involved. BotChips have no monetary value.
        </p>
        <div className="mt-2 flex justify-center gap-4">
          <Link to="/disclaimer" className="text-xs text-text-muted hover:text-text-secondary">
            Legal Disclaimer
          </Link>
        </div>
      </footer>
    </div>
  );
}
