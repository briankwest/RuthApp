import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { lettersAPI } from '../services/api';
import {
  PencilSquareIcon,
  UsersIcon,
  MicrophoneIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline';

export default function DashboardPage() {
  const [recentLetters, setRecentLetters] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRecentLetters();
  }, []);

  const loadRecentLetters = async () => {
    try {
      const response = await lettersAPI.getLetters({ limit: 5 });
      setRecentLetters(response.data);
    } catch (error) {
      console.error('Failed to load letters:', error);
    } finally {
      setLoading(false);
    }
  };

  const quickActions = [
    {
      title: 'Write New Letter',
      description: 'Start a new letter to your representatives',
      icon: PencilSquareIcon,
      link: '/letters/new',
      color: 'bg-green-500 hover:bg-green-600',
    },
    {
      title: 'Find Representatives',
      description: 'Look up your state and federal representatives',
      icon: UsersIcon,
      link: '/representatives',
      color: 'bg-blue-500 hover:bg-blue-600',
    },
    {
      title: 'Writing Profiles',
      description: 'Manage your writing writing profiles',
      icon: MicrophoneIcon,
      link: '/writing-profiles',
      color: 'bg-purple-500 hover:bg-purple-600',
    },
    {
      title: 'My Letters',
      description: 'View and manage all your letters',
      icon: DocumentTextIcon,
      link: '/letters',
      color: 'bg-orange-500 hover:bg-orange-600',
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Welcome to Ruth</h1>
        <p className="mt-2 text-gray-600">
          Your civic empowerment platform for writing to representatives
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {quickActions.map((action) => (
          <Link
            key={action.title}
            to={action.link}
            className={`${action.color} text-white rounded-lg p-6 shadow-md transition-all hover:shadow-lg`}
          >
            <action.icon className="h-8 w-8 mb-3" />
            <h3 className="text-lg font-semibold mb-1">{action.title}</h3>
            <p className="text-sm opacity-90">{action.description}</p>
          </Link>
        ))}
      </div>

      {/* Recent Letters */}
      <div className="card">
        <h2 className="text-xl font-bold mb-4">Recent Letters</h2>

        {loading ? (
          <p className="text-gray-500">Loading...</p>
        ) : recentLetters.length === 0 ? (
          <div className="text-center py-8">
            <DocumentTextIcon className="h-12 w-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-500 mb-4">You haven't created any letters yet</p>
            <Link to="/letters/new" className="btn btn-primary">
              Write Your First Letter
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {recentLetters.map((letter) => (
              <div
                key={letter.id}
                className="border border-gray-200 rounded-lg p-5 hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-start mb-3">
                  <div className="flex-1">
                    <h3 className="font-bold text-gray-900 text-lg">
                      {letter.subject}
                    </h3>
                    <p className="text-sm text-gray-500 mt-1">
                      Created {new Date(letter.created_at).toLocaleDateString('en-US', {
                        month: 'long',
                        day: 'numeric',
                        year: 'numeric'
                      })}
                    </p>
                    <div className="mt-2 flex items-center gap-2 text-xs">
                      <span className={`px-2 py-1 rounded font-medium ${
                        letter.status === 'finalized' ? 'bg-green-100 text-green-700' :
                        letter.status === 'draft' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {letter.status}
                      </span>
                      {letter.category && (
                        <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded">
                          {letter.category}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Recipients */}
                {letter.recipients && letter.recipients.length > 0 && (
                  <div className="mt-3 p-3 bg-gray-50 rounded">
                    <p className="text-xs font-semibold text-gray-700 mb-2">
                      Recipients ({letter.recipients.length})
                    </p>
                    <div className="space-y-2">
                      {letter.recipients.map((recipient) => {
                        const wordCount = recipient.content ? recipient.content.split(/\s+/).filter(w => w).length : 0;
                        return (
                          <div
                            key={recipient.id}
                            className="px-3 py-2 bg-white border border-gray-200 rounded"
                          >
                            <div className="text-sm font-medium text-gray-900">{recipient.name}</div>
                            <div className="text-xs text-gray-600">{recipient.title}</div>
                            {recipient.subject && (
                              <div className="text-xs text-gray-700 mt-0.5 italic">
                                Subject: {recipient.subject}
                              </div>
                            )}
                            {wordCount > 0 && (
                              <div className="text-xs text-gray-500 mt-1">
                                {wordCount} words
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Action Link */}
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <Link
                    to="/letters"
                    className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                  >
                    View all letters →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
