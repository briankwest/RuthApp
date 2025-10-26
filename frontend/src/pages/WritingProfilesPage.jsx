import { useState, useEffect } from 'react';
import { lettersAPI } from '../services/api';
import useAuthStore from '../stores/authStore';
import WritingProfileWizard from '../components/WritingProfileWizard';
import WritingProfileDetailsModal from '../components/WritingProfileDetailsModal';
import Toast from '../components/Toast';

export default function WritingProfilesPage() {
  const { user } = useAuthStore();
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showCreateWizard, setShowCreateWizard] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedProfile, setSelectedProfile] = useState(null);
  const [showEditWizard, setShowEditWizard] = useState(false);
  const [editingProfile, setEditingProfile] = useState(null);
  const [confirmDeleteProfile, setConfirmDeleteProfile] = useState(null);

  useEffect(() => {
    loadProfiles();
  }, []);

  const loadProfiles = async () => {
    try {
      setLoading(true);
      const response = await lettersAPI.getWritingProfiles();
      setProfiles(response.data || []);
    } catch (err) {
      setError('Failed to load writing profiles');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = (profileId) => {
    setConfirmDeleteProfile(profileId);
  };

  const confirmDeleteAction = async () => {
    try {
      await lettersAPI.deleteWritingProfile(confirmDeleteProfile);
      setSuccess('Writing profile deleted successfully');
      setTimeout(() => setSuccess(''), 3000);
      loadProfiles();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete profile');
      setTimeout(() => setError(''), 3000);
    } finally {
      setConfirmDeleteProfile(null);
    }
  };

  const handleSetDefault = async (profileId) => {
    try {
      // Update this profile to be default
      await lettersAPI.updateWritingProfile(profileId, { is_default: true });
      setSuccess('Default profile updated');
      setTimeout(() => setSuccess(''), 3000);
      loadProfiles();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to set default');
      setTimeout(() => setError(''), 3000);
    }
  };

  const handleViewDetails = (profile) => {
    setSelectedProfile(profile);
    setShowDetailsModal(true);
  };

  const handleEditFromDetails = () => {
    setEditingProfile(selectedProfile);
    setShowDetailsModal(false);
    setShowEditWizard(true);
  };

  const handleEditSuccess = () => {
    setSuccess('Writing profile updated successfully!');
    setTimeout(() => setSuccess(''), 3000);
    loadProfiles();
    setShowEditWizard(false);
    setEditingProfile(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-600 dark:text-gray-400">Loading writing profiles...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {success && <Toast message={success} type="success" onClose={() => setSuccess('')} />}
      {error && <Toast message={error} type="error" onClose={() => setError('')} />}

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Writing Profiles</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Create personalized writing styles for your advocacy letters
          </p>
        </div>
        <button
          onClick={() => setShowCreateWizard(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium w-full sm:w-auto"
        >
          Create New Profile
        </button>
      </div>

      {profiles.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg p-12 text-center">
          <div className="max-w-md mx-auto">
            <svg
              className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"
              />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">
              No writing profiles yet
            </h3>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              Get started by creating your first writing profile. This will help personalize your letters to representatives.
            </p>
            <button
              onClick={() => setShowCreateWizard(true)}
              className="mt-6 px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
            >
              Create Your First Profile
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {profiles.map((profile) => (
            <div
              key={profile.id}
              className="bg-white dark:bg-gray-800 shadow-sm rounded-lg p-6 hover:shadow-md transition-shadow relative"
            >
              {profile.is_default && (
                <span className="absolute top-4 right-4 px-2 py-1 text-xs font-semibold text-blue-700 dark:text-blue-300 bg-blue-100 dark:bg-blue-900/50 rounded">
                  Default
                </span>
              )}

              <h3 className="text-lg font-bold text-gray-900 dark:text-white pr-16">{profile.name}</h3>

              {profile.description && (
                <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 line-clamp-3">
                  {profile.description}
                </p>
              )}

              <div className="mt-4 space-y-2 text-sm">
                {profile.political_leaning && (
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-700 dark:text-gray-300">Leaning:</span>
                    <span className="capitalize text-gray-600 dark:text-gray-400">{profile.political_leaning}</span>
                  </div>
                )}

                {profile.key_issues && profile.key_issues.length > 0 && (
                  <div>
                    <span className="font-medium text-gray-700 dark:text-gray-300">Key Issues:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {profile.key_issues.slice(0, 3).map((issue, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded"
                        >
                          {issue}
                        </span>
                      ))}
                      {profile.key_issues.length > 3 && (
                        <span className="px-2 py-1 text-xs text-gray-500 dark:text-gray-500">
                          +{profile.key_issues.length - 3} more
                        </span>
                      )}
                    </div>
                  </div>
                )}

                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-700 dark:text-gray-300">Tone:</span>
                  <span className="capitalize text-gray-600 dark:text-gray-400">{profile.preferred_tone}</span>
                </div>

                {profile.last_used_at && (
                  <div className="text-xs text-gray-500">
                    Last used: {new Date(profile.last_used_at).toLocaleDateString()}
                  </div>
                )}
              </div>

              <div className="mt-6 space-y-2">
                <button
                  onClick={() => handleViewDetails(profile)}
                  className="w-full px-3 py-2 text-sm border border-blue-300 dark:border-blue-700 text-blue-700 dark:text-blue-400 rounded-md hover:bg-blue-50 dark:hover:bg-blue-900/30 font-medium"
                >
                  View Details
                </button>
                <div className="flex items-center gap-2">
                  {!profile.is_default && (
                    <button
                      onClick={() => handleSetDefault(profile.id)}
                      className="flex-1 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
                    >
                      Set Default
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(profile.id)}
                    className="flex-1 px-3 py-2 text-sm border border-red-300 dark:border-red-700 text-red-700 dark:text-red-400 rounded-md hover:bg-red-50 dark:hover:bg-red-900/30"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {showCreateWizard && (
        <WritingProfileWizard
          onClose={() => setShowCreateWizard(false)}
          onSuccess={() => {
            setSuccess('Writing profile created successfully!');
            setTimeout(() => setSuccess(''), 3000);
            loadProfiles();
          }}
        />
      )}

      {showDetailsModal && selectedProfile && (
        <WritingProfileDetailsModal
          profile={selectedProfile}
          onClose={() => {
            setShowDetailsModal(false);
            setSelectedProfile(null);
          }}
          onEdit={handleEditFromDetails}
        />
      )}

      {showEditWizard && editingProfile && (
        <WritingProfileWizard
          editMode={true}
          existingProfile={editingProfile}
          onClose={() => {
            setShowEditWizard(false);
            setEditingProfile(null);
          }}
          onSuccess={handleEditSuccess}
        />
      )}

      {/* Delete Confirmation Modal */}
      {confirmDeleteProfile && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              Delete Writing Profile?
            </h2>
            <p className="text-gray-700 dark:text-gray-300 mb-6">
              Are you sure you want to delete this writing profile? This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setConfirmDeleteProfile(null)}
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Cancel
              </button>
              <button
                onClick={confirmDeleteAction}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 font-semibold"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
