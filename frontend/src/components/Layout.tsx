import { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Sparkles, Home, Building2, LogIn, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const { currentBusiness, clearBusiness } = useAuth();

  const isActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center space-x-2">
              <Sparkles className="h-8 w-8 text-primary-600" />
              <span className="text-2xl font-bold text-gray-900">BizGenie</span>
            </Link>
            <nav className="flex items-center space-x-4">
              <Link
                to="/"
                className={`flex items-center space-x-1 px-3 py-2 rounded-lg transition-colors ${
                  isActive('/') && location.pathname === '/'
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                <Home className="h-4 w-4" />
                <span>Home</span>
              </Link>
              <Link
                to="/register"
                className={`flex items-center space-x-1 px-3 py-2 rounded-lg transition-colors ${
                  isActive('/register')
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                <Building2 className="h-4 w-4" />
                <span>Register Business</span>
              </Link>
              {currentBusiness ? (
                <>
                  <Link
                    to={`/business/${currentBusiness.id}`}
                    className="hidden md:flex items-center space-x-1 px-3 py-2 rounded-lg bg-primary-50 text-primary-700"
                  >
                    <span className="text-sm font-semibold truncate max-w-[140px]">
                      {currentBusiness.name}
                    </span>
                  </Link>
                  <button
                    onClick={clearBusiness}
                    className="flex items-center space-x-1 px-3 py-2 rounded-lg text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                  >
                    <LogOut className="h-4 w-4" />
                    <span>Logout</span>
                  </button>
                </>
              ) : (
                <Link
                  to="/login"
                  className={`flex items-center space-x-1 px-3 py-2 rounded-lg transition-colors ${
                    isActive('/login')
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                >
                  <LogIn className="h-4 w-4" />
                  <span>Login</span>
                </Link>
              )}
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-gray-600">
            <p>© 2024 BizGenie. Built with FastAPI, LangGraph, and React.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

