import { useState } from 'react';
import { authAPI } from '../services/api';

export default function DeleteAccountModal({ isOpen, onClose, onSuccess, deletionSummary }) {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [deleting, setDeleting] = useState(false);

  if (!isOpen) return null;

  const handleDelete = async () => {
    if (!password.trim()) {
      setError('Please enter your password');
      return;
    }

    setDeleting(true);
    setError('');

    try {
      await authAPI.deleteAccount(password);
      onSuccess();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete account');
    } finally {
      setDeleting(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !deleting) {
      handleDelete();
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          ⚠️ Delete Account?
        </h2>

        {error && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded-md">
            <p className="text-sm text-red-600 dark:text-red-300">{error}</p>
          </div>
        )}

        <div className="mb-6">
          <p className="text-gray-700 dark:text-gray-300 mb-4 font-semibold">
            This will permanently delete:
          </p>
          <ul className="space-y-2 text-gray-600 dark:text-gray-400 text-sm">
            <li className="flex items-start gap-2">
              <span className="text-red-500 font-bold">✓</span>
              <span>Your account ({deletionSummary.email})</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-red-500 font-bold">✓</span>
              <span>{deletionSummary.writing_profiles_count} writing profile{deletionSummary.writing_profiles_count !== 1 ? 's' : ''}</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-red-500 font-bold">✓</span>
              <span>{deletionSummary.letters_count} letter{deletionSummary.letters_count !== 1 ? 's' : ''} ({deletionSummary.draft_letters_count} draft{deletionSummary.draft_letters_count !== 1 ? 's' : ''}, {deletionSummary.finalized_letters_count} sent)</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-red-500 font-bold">✓</span>
              <span>{deletionSummary.representatives_count} saved representative{deletionSummary.representatives_count !== 1 ? 's' : ''}</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-red-500 font-bold">✓</span>
              <span>{deletionSummary.addresses_count} address{deletionSummary.addresses_count !== 1 ? 'es' : ''}</span>
            </li>
          </ul>
        </div>

        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded-md">
          <p className="text-red-800 dark:text-red-300 font-bold text-center">
            This action CANNOT be undone!
          </p>
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Enter your password to confirm:
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Your password"
            disabled={deleting}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 rounded-md focus:ring-2 focus:ring-red-500 focus:border-transparent"
            autoFocus
          />
        </div>

        <div className="flex gap-3">
          <button
            onClick={onClose}
            disabled={deleting}
            className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleDelete}
            disabled={deleting || !password.trim()}
            className="flex-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed font-bold"
          >
            {deleting ? 'Deleting...' : 'Delete Account Forever'}
          </button>
        </div>
      </div>
    </div>
  );
}
