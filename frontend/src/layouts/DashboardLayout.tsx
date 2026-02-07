import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { LogOut, LayoutDashboard, Eye } from 'lucide-react';

export function DashboardLayout() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-void">
      <nav className="border-b border-white/5 bg-surface/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-xl font-display font-bold text-gold">AI Bot Casino</span>
          </Link>

          <div className="flex items-center gap-4">
            <Link
              to="/watch"
              className="flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary"
            >
              <Eye size={16} />
              Watch
            </Link>
            <Link
              to="/dashboard"
              className={`flex items-center gap-1.5 text-sm ${
                location.pathname === '/dashboard' ? 'text-gold' : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              <LayoutDashboard size={16} />
              Dashboard
            </Link>
            <span className="text-sm text-text-muted">{user?.first_name}</span>
            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 text-sm text-text-muted hover:text-accent-red transition-colors"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
