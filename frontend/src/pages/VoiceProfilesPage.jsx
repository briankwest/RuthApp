import { useState, useEffect } from 'react';
import { lettersAPI } from '../services/api';
import useAuthStore from '../stores/authStore';
import WritingProfileWizard from '../components/WritingProfileWizard';

export default function WritingProfilesPage() {
  const { user } = useAuthStore();
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showCreateWizard, setShowCreateWizard] = useState(false);

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

  const handleDelete = async (profileId) => {
    if (!window.confirm('Are you sure you want to delete this writing profile?')) {
      return;
    }

    try {
      await lettersAPI.deleteWritingProfile(profileId);
      setSuccess('Writing profile deleted successfully');
      setTimeout(() => setSuccess(''), 3000);
      loadProfiles();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete profile');
      setTimeout(() => setError(''), 3000);
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-600">Loading writing profiles...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Writing Profiles</h1>
          <p className="mt-2 text-gray-600">
            Create personalized writing styles for your advocacy letters
          </p>
        </div>
        <button
          onClick={() => setShowCreateWizard(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
        >
          Create New Profile
        </button>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {success && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-md">
          <p className="text-sm text-green-600">{success}</p>
        </div>
      )}

      {profiles.length === 0 ? (
        <div className="bg-white shadow-sm rounded-lg p-12 text-center">
          <div className="max-w-md mx-auto">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
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
            <h3 className="mt-4 text-lg font-medium text-gray-900">
              No writing profiles yet
            </h3>
            <p className="mt-2 text-sm text-gray-600">
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
              className="bg-white shadow-sm rounded-lg p-6 hover:shadow-md transition-shadow relative"
            >
              {profile.is_default && (
                <span className="absolute top-4 right-4 px-2 py-1 text-xs font-semibold text-blue-700 bg-blue-100 rounded">
                  Default
                </span>
              )}

              <h3 className="text-lg font-bold text-gray-900 pr-16">{profile.name}</h3>

              {profile.description && (
                <p className="mt-2 text-sm text-gray-600 line-clamp-3">
                  {profile.description}
                </p>
              )}

              <div className="mt-4 space-y-2 text-sm">
                {profile.political_leaning && (
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-700">Leaning:</span>
                    <span className="capitalize text-gray-600">{profile.political_leaning}</span>
                  </div>
                )}

                {profile.key_issues && profile.key_issues.length > 0 && (
                  <div>
                    <span className="font-medium text-gray-700">Key Issues:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {profile.key_issues.slice(0, 3).map((issue, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded"
                        >
                          {issue}
                        </span>
                      ))}
                      {profile.key_issues.length > 3 && (
                        <span className="px-2 py-1 text-xs text-gray-500">
                          +{profile.key_issues.length - 3} more
                        </span>
                      )}
                    </div>
                  </div>
                )}

                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-700">Tone:</span>
                  <span className="capitalize text-gray-600">{profile.preferred_tone}</span>
                </div>

                {profile.last_used_at && (
                  <div className="text-xs text-gray-500">
                    Last used: {new Date(profile.last_used_at).toLocaleDateString()}
                  </div>
                )}
              </div>

              <div className="mt-6 flex items-center gap-2">
                {!profile.is_default && (
                  <button
                    onClick={() => handleSetDefault(profile.id)}
                    className="flex-1 px-3 py-2 text-sm border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                  >
                    Set Default
                  </button>
                )}
                <button
                  onClick={() => handleDelete(profile.id)}
                  className="flex-1 px-3 py-2 text-sm border border-red-300 text-red-700 rounded-md hover:bg-red-50"
                >
                  Delete
                </button>
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
    </div>
  );
}
