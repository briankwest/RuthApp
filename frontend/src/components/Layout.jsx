import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import useAuthStore from '../stores/authStore';
import {
  HomeIcon,
  UsersIcon,
  UserCircleIcon,
  PencilSquareIcon,
  DocumentTextIcon,
  PaperAirplaneIcon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/react/24/outline';

export default function Layout() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

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
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-end items-center h-16">
            {/* User Menu */}
            <div className="flex items-center gap-4">
              <Link
                to="/profile"
                className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900"
              >
                <UserCircleIcon className="h-5 w-5" />
                <span>{user?.first_name} {user?.last_name}</span>
              </Link>
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900"
              >
                <ArrowRightOnRectangleIcon className="h-5 w-5" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-white shadow-sm min-h-[calc(100vh-4rem)]">
          <nav className="space-y-2">
            {/* Logo */}
            <div className="flex justify-center -mt-[35px] pb-6 border-b border-gray-200">
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
        <main className="flex-1 p-8">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
