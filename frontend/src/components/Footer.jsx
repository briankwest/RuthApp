import { Link } from 'react-router-dom';

export default function Footer() {
  const version = '1.0.0';
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-white border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex flex-col sm:flex-row justify-between items-center gap-4 text-sm text-gray-600">
          {/* Version */}
          <div>
            <span className="font-medium">Ruth</span> v{version}
          </div>

          {/* Links */}
          <div className="flex gap-6">
            <Link
              to="/terms"
              className="hover:text-ruth-blue transition-colors"
            >
              Terms of Service
            </Link>
            <Link
              to="/privacy"
              className="hover:text-ruth-blue transition-colors"
            >
              Privacy Policy
            </Link>
          </div>

          {/* Copyright */}
          <div className="text-gray-500">
            © {currentYear} Brian West. All rights reserved.
          </div>
        </div>
      </div>
    </footer>
  );
}
