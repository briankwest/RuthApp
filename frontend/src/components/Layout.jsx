import { useState, useEffect } from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import useAuthStore from '../stores/authStore';
import useThemeStore from '../stores/themeStore';
import Footer from './Footer';
import InstallPrompt from './InstallPrompt';
import {
  HomeIcon,
  UsersIcon,
  UserCircleIcon,
  PencilSquareIcon,
  DocumentTextIcon,
  ArrowRightOnRectangleIcon,
  Bars3Icon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

export default function Layout() {
  const { user, logout } = useAuthStore();
  const { darkMode, toggleDarkMode } = useThemeStore((state) => ({
    darkMode: state.darkMode,
    toggleDarkMode: state.toggleDarkMode
  }));
  const initializeDarkMode = useThemeStore((state) => state.initializeDarkMode);
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    initializeDarkMode();
  }, [initializeDarkMode]);

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
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Mobile menu button and logo */}
            <div className="flex items-center gap-4 md:hidden">
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="p-2 rounded-md text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                {mobileMenuOpen ? (
                  <XMarkIcon className="h-6 w-6" />
                ) : (
                  <Bars3Icon className="h-6 w-6" />
                )}
              </button>
              <img src="/ruth_logo.png" alt="Ruth" className="h-10 w-auto dark:drop-shadow-[0_0_8px_rgba(147,197,253,0.5)]" />
            </div>

            {/* Spacer for desktop to push user menu to right */}
            <div className="hidden md:block flex-1"></div>

            {/* User Menu - Always right aligned */}
            <div className="flex items-center gap-2 sm:gap-4 ml-auto">
              <Link
                to="/profile"
                className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-200 hover:text-gray-900 dark:hover:text-white"
              >
                <UserCircleIcon className="h-5 w-5" />
                <span className="hidden sm:inline">{user?.first_name} {user?.last_name}</span>
              </Link>

              {/* iOS-style Dark Mode Toggle */}
              <button
                onClick={toggleDarkMode}
                className="relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                style={{
                  backgroundColor: darkMode ? '#3b82f6' : '#d1d5db'
                }}
                aria-label="Toggle dark mode"
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    darkMode ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>

              <button
                onClick={handleLogout}
                className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-200 hover:text-gray-900 dark:hover:text-white"
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
          <aside className="fixed inset-y-0 left-0 w-64 bg-white dark:bg-gray-800 shadow-xl z-50 overflow-y-auto">
            <nav className="space-y-2 p-4">
              {/* Logo */}
              <div className="flex justify-center pb-6">
                <img
                  src="/ruth_logo.png"
                  alt="Ruth Logo"
                  className="h-40 w-auto dark:drop-shadow-[0_0_12px_rgba(147,197,253,0.6)]"
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
                        : 'text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                  >
                    <item.icon className="h-5 w-5" />
                    {item.label}
                  </Link>
                ))}
              </div>
            </nav>
          </aside>
        </div>
      )}

      <div className="flex flex-1">
        {/* Desktop Sidebar */}
        <aside className="hidden md:block w-64 bg-white dark:bg-gray-800 shadow-sm">
          <nav className="space-y-2">
            {/* Logo */}
            <div className="flex justify-center -mt-[35px] pb-6">
              <img
                src="/ruth_logo.png"
                alt="Ruth Logo"
                className="h-60 w-auto dark:drop-shadow-[0_0_15px_rgba(147,197,253,0.7)]"
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
                      : 'text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <item.icon className="h-5 w-5" />
                  {item.label}
                </Link>
              ))}
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

      {/* Install Prompt */}
      <InstallPrompt />
    </div>
  );
}
