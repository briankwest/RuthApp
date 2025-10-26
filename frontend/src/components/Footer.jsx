import { Link } from 'react-router-dom';

export default function Footer() {
  const version = import.meta.env.VITE_APP_VERSION || 'unknown';
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex flex-col sm:flex-row justify-between items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
          {/* Version */}
          <div>
            <span className="font-medium">Ruth</span> v{version}
          </div>

          {/* Links */}
          <div className="flex gap-6">
            <Link
              to="/terms"
              className="hover:text-ruth-blue dark:hover:text-blue-400 transition-colors"
            >
              Terms of Service
            </Link>
            <Link
              to="/privacy"
              className="hover:text-ruth-blue dark:hover:text-blue-400 transition-colors"
            >
              Privacy Policy
            </Link>
          </div>

          {/* Copyright */}
          <div className="text-gray-500 dark:text-gray-500">
            © {currentYear} Brian West. All rights reserved.
          </div>
        </div>
      </div>
    </footer>
  );
}
