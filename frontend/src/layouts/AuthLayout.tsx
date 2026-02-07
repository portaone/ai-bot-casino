import { Outlet, Link } from 'react-router-dom';

export function AuthLayout() {
  return (
    <div className="min-h-screen bg-void flex flex-col items-center justify-center p-4">
      <Link to="/" className="mb-8">
        <span className="text-2xl font-display font-bold text-gold">AI Bot Casino</span>
      </Link>
      <div className="w-full max-w-md">
        <Outlet />
      </div>
    </div>
  );
}
