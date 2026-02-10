import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-[#1e3a5f] text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo + Brand */}
          <Link to="/" className="flex items-center gap-3 no-underline">
            <img
              src="/phoenix-logo.png"
              alt="DJ AI Business Consultant"
              className="h-10 w-10 object-contain brightness-0 invert"
            />
            <div className="hidden sm:block">
              <div className="text-lg font-bold tracking-tight">SyrHousing</div>
              <div className="text-xs text-blue-200 -mt-1">DJ AI Business Consultant</div>
            </div>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center gap-1 sm:gap-2">
            {user ? (
              <>
                <Link
                  to="/dashboard"
                  className="px-3 py-2 rounded-md text-sm font-medium text-blue-100 hover:bg-[#2d6a9f] hover:text-white transition-colors no-underline"
                >
                  Dashboard
                </Link>
                <Link
                  to="/programs"
                  className="px-3 py-2 rounded-md text-sm font-medium text-blue-100 hover:bg-[#2d6a9f] hover:text-white transition-colors no-underline"
                >
                  Programs
                </Link>
                <Link
                  to="/chat"
                  className="px-3 py-2 rounded-md text-sm font-medium text-blue-100 hover:bg-[#2d6a9f] hover:text-white transition-colors no-underline"
                >
                  AI Chat
                </Link>
                <Link
                  to="/applications"
                  className="px-3 py-2 rounded-md text-sm font-medium text-blue-100 hover:bg-[#2d6a9f] hover:text-white transition-colors no-underline"
                >
                  My Apps
                </Link>
                {user.role === 'admin' && (
                  <Link
                    to="/admin"
                    className="px-3 py-2 rounded-md text-sm font-medium text-[#c9a84c] hover:bg-[#2d6a9f] hover:text-white transition-colors no-underline"
                  >
                    Admin
                  </Link>
                )}
                <div className="ml-2 sm:ml-4 flex items-center gap-2">
                  <span className="hidden md:inline text-sm text-blue-200">
                    {user.full_name}
                  </span>
                  <button
                    onClick={handleLogout}
                    className="px-3 py-1.5 text-sm bg-[#2d6a9f] hover:bg-[#4a9eda] rounded-md transition-colors border-none text-white cursor-pointer"
                  >
                    Sign Out
                  </button>
                </div>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="px-4 py-2 rounded-md text-sm font-medium text-blue-100 hover:bg-[#2d6a9f] hover:text-white transition-colors no-underline"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-2 rounded-md text-sm font-medium bg-[#c9a84c] text-[#1e3a5f] hover:bg-[#d4b85d] transition-colors no-underline"
                >
                  Get Started
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
