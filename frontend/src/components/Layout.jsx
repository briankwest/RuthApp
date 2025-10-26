import { useState } from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import useAuthStore from '../stores/authStore';
import Footer from './Footer';
import {
  HomeIcon,
  UsersIcon,
  UserCircleIcon,
  PencilSquareIcon,
  DocumentTextIcon,
  PaperAirplaneIcon,
  ArrowRightOnRectangleIcon,
  Bars3Icon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

export default function Layout() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/', label: 'Dashboard', icon: HomeIcon },
    { path: '/representatives', label: 'Representatives', icon: UsersIcon },
    { path: '/writing-profiles', label: 'Writing Profiles', icon: PencilSquareIcon },
    { path: '/letters', label: 'My Letters', icon: DocumentTextIcon },
  ];

  const isActive = (path) => {
    return location.pathname === path;
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Mobile menu button and logo */}
            <div className="flex items-center gap-4 md:hidden">
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="p-2 rounded-md text-gray-700 hover:bg-gray-100"
              >
                {mobileMenuOpen ? (
                  <XMarkIcon className="h-6 w-6" />
                ) : (
                  <Bars3Icon className="h-6 w-6" />
                )}
              </button>
              <img src="/ruth_logo.png" alt="Ruth" className="h-10 w-auto" />
            </div>

            {/* Spacer for desktop to push user menu to right */}
            <div className="hidden md:block flex-1"></div>

            {/* User Menu - Always right aligned */}
            <div className="flex items-center gap-2 sm:gap-4 ml-auto">
              <Link
                to="/profile"
                className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900"
              >
                <UserCircleIcon className="h-5 w-5" />
                <span className="hidden sm:inline">{user?.first_name} {user?.last_name}</span>
              </Link>
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900"
              >
                <ArrowRightOnRectangleIcon className="h-5 w-5" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile menu overlay */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setMobileMenuOpen(false)} />
          <aside className="fixed inset-y-0 left-0 w-64 bg-white shadow-xl z-50 overflow-y-auto">
            <nav className="space-y-2 p-4">
              {/* Logo */}
              <div className="flex justify-center pb-6">
                <img
                  src="/ruth_logo.png"
                  alt="Ruth Logo"
                  className="h-40 w-auto"
                />
              </div>

              <div className="pt-2 space-y-2">
                {navItems.map((item) => (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-3 px-4 py-3 rounded-md transition-colors ${
                      isActive(item.path)
                        ? 'bg-ruth-blue text-white'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    <item.icon className="h-5 w-5" />
                    {item.label}
                  </Link>
                ))}

                {/* New Letter Button */}
                <Link
                  to="/letters/new"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center gap-3 px-4 py-3 rounded-md bg-green-600 text-white hover:bg-green-700 transition-colors mt-4"
                >
                  <PaperAirplaneIcon className="h-5 w-5" />
                  Write New Letter
                </Link>
              </div>
            </nav>
          </aside>
        </div>
      )}

      <div className="flex flex-1">
        {/* Desktop Sidebar */}
        <aside className="hidden md:block w-64 bg-white shadow-sm">
          <nav className="space-y-2">
            {/* Logo */}
            <div className="flex justify-center -mt-[35px] pb-6">
              <img
                src="/ruth_logo.png"
                alt="Ruth Logo"
                className="h-60 w-auto"
              />
            </div>

            <div className="px-4 pt-2 space-y-2">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-4 py-3 rounded-md transition-colors ${
                    isActive(item.path)
                      ? 'bg-ruth-blue text-white'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <item.icon className="h-5 w-5" />
                  {item.label}
                </Link>
              ))}

              {/* New Letter Button */}
              <Link
                to="/letters/new"
                className="flex items-center gap-3 px-4 py-3 rounded-md bg-green-600 text-white hover:bg-green-700 transition-colors mt-4"
              >
                <PaperAirplaneIcon className="h-5 w-5" />
                Write New Letter
              </Link>
            </div>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-4 sm:p-6 md:p-8">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Footer */}
      <Footer />
    </div>
  );
}
