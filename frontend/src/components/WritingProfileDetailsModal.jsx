import { useState } from 'react';

export default function WritingProfileDetailsModal({ profile, onClose, onEdit }) {
  const [expandedSections, setExpandedSections] = useState({
    issues: true,
    values: true,
    frameworks: true,
    engagement: true,
    regional: true,
    samples: false
  });

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // Helper to format field names
  const formatFieldName = (str) => {
    return str.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  // Helper to get priority badge color
  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 overflow-y-auto">
      <div className="bg-white rounded-lg max-w-4xl w-full my-8 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between z-10">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{profile.name}</h2>
            {profile.is_default && (
              <span className="inline-block mt-1 px-2 py-1 text-xs font-semibold text-blue-700 bg-blue-100 rounded">
                Default Profile
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-6 space-y-6">
          {/* Basic Information */}
          <section>
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
              📋 Basic Information
            </h3>
            <div className="bg-gray-50 rounded-lg p-4 space-y-2">
              {profile.description && (
                <div>
                  <span className="font-medium text-gray-700">Description:</span>
                  <p className="text-gray-600 mt-1">{profile.description}</p>
                </div>
              )}
              {profile.political_leaning && (
                <div>
                  <span className="font-medium text-gray-700">Political Perspective:</span>
                  <span className="ml-2 capitalize text-gray-600">{profile.political_leaning}</span>
                </div>
              )}
              <div>
                <span className="font-medium text-gray-700">Tone:</span>
                <span className="ml-2 capitalize text-gray-600">{profile.preferred_tone}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Length Preference:</span>
                <span className="ml-2 capitalize text-gray-600">{profile.preferred_length}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Vocabulary Level:</span>
                <span className="ml-2 capitalize text-gray-600">{profile.vocabulary_level}</span>
              </div>
            </div>
          </section>

          {/* Issue Positions */}
          {profile.issue_positions && Object.keys(profile.issue_positions).length > 0 && (
            <section>
              <button
                onClick={() => toggleSection('issues')}
                className="w-full text-left text-lg font-semibold text-gray-900 mb-3 flex items-center justify-between gap-2 hover:text-blue-600"
              >
                <span>🎯 Issue Positions ({Object.keys(profile.issue_positions).length})</span>
                <span>{expandedSections.issues ? '▼' : '▶'}</span>
              </button>
              {expandedSections.issues && (
                <div className="space-y-3">
                  {/* Group by priority */}
                  {['critical', 'high', 'medium', 'low'].map(priorityLevel => {
                    const issuesAtLevel = Object.entries(profile.issue_positions).filter(
                      ([_, data]) => data.priority === priorityLevel
                    );
                    if (issuesAtLevel.length === 0) return null;

                    return (
                      <div key={priorityLevel}>
                        <h4 className="text-sm font-semibold text-gray-700 mb-2 capitalize">
                          {priorityLevel} Priority:
                        </h4>
                        <div className="space-y-2">
                          {issuesAtLevel.map(([issueKey, issueData]) => (
                            <div key={issueKey} className="bg-gray-50 rounded-lg p-3 border-l-4 border-blue-400">
                              <div className="flex items-start justify-between gap-2">
                                <div className="flex-1">
                                  <h5 className="font-medium text-gray-900">{formatFieldName(issueKey)}</h5>
                                  <div className="mt-1 flex items-center gap-2 text-sm">
                                    <span className="text-gray-600">Position:</span>
                                    <span className="font-medium text-gray-900 capitalize">
                                      {issueData.position?.replace(/_/g, ' ')}
                                    </span>
                                  </div>
                                  {issueData.personal_connection && (
                                    <p className="mt-2 text-sm text-gray-600 italic">
                                      "{issueData.personal_connection}"
                                    </p>
                                  )}
                                </div>
                                <span className={`px-2 py-1 text-xs font-semibold rounded border ${getPriorityColor(issueData.priority)}`}>
                                  {issueData.priority}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </section>
          )}

          {/* Abortion Position */}
          {profile.abortion_position && (
            <section>
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                🏥 Abortion Rights Position
              </h3>
              <div className="bg-gray-50 rounded-lg p-4">
                <span className="text-gray-900 capitalize">
                  {profile.abortion_position.replace(/_/g, ' ')}
                </span>
              </div>
            </section>
          )}

          {/* Core Values */}
          {profile.core_values && profile.core_values.length > 0 && (
            <section>
              <button
                onClick={() => toggleSection('values')}
                className="w-full text-left text-lg font-semibold text-gray-900 mb-3 flex items-center justify-between gap-2 hover:text-blue-600"
              >
                <span>💎 Core Values ({profile.core_values.length})</span>
                <span>{expandedSections.values ? '▼' : '▶'}</span>
              </button>
              {expandedSections.values && (
                <div className="flex flex-wrap gap-2">
                  {profile.core_values.map((value, idx) => (
                    <span
                      key={idx}
                      className="px-4 py-2 bg-purple-100 text-purple-800 rounded-full text-sm font-medium border border-purple-200"
                    >
                      {formatFieldName(value)}
                    </span>
                  ))}
                </div>
              )}
            </section>
          )}

          {/* Content Preferences */}
          <section>
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
              📝 Content Preferences
            </h3>
            <div className="bg-gray-50 rounded-lg p-4 grid grid-cols-2 gap-3">
              <div className="flex items-center gap-2">
                <span className={`text-xl ${profile.include_personal_stories ? 'text-green-600' : 'text-gray-300'}`}>
                  {profile.include_personal_stories ? '✓' : '○'}
                </span>
                <span className="text-gray-700">Personal Stories</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-xl ${profile.include_data_statistics ? 'text-green-600' : 'text-gray-300'}`}>
                  {profile.include_data_statistics ? '✓' : '○'}
                </span>
                <span className="text-gray-700">Data & Statistics</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-xl ${profile.include_emotional_appeals ? 'text-green-600' : 'text-gray-300'}`}>
                  {profile.include_emotional_appeals ? '✓' : '○'}
                </span>
                <span className="text-gray-700">Emotional Appeals</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-xl ${profile.include_constitutional_arguments ? 'text-green-600' : 'text-gray-300'}`}>
                  {profile.include_constitutional_arguments ? '✓' : '○'}
                </span>
                <span className="text-gray-700">Constitutional Arguments</span>
              </div>
            </div>
          </section>

          {/* Argumentative Frameworks */}
          {profile.argumentative_frameworks && Object.keys(profile.argumentative_frameworks).length > 0 && (
            <section>
              <button
                onClick={() => toggleSection('frameworks')}
                className="w-full text-left text-lg font-semibold text-gray-900 mb-3 flex items-center justify-between gap-2 hover:text-blue-600"
              >
                <span>🎯 Argumentative Frameworks</span>
                <span>{expandedSections.frameworks ? '▼' : '▶'}</span>
              </button>
              {expandedSections.frameworks && (
                <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                  {Object.entries(profile.argumentative_frameworks).map(([framework, enabled]) => (
                    <div key={framework} className="flex items-center gap-2">
                      <span className={`text-xl ${enabled ? 'text-green-600' : 'text-gray-300'}`}>
                        {enabled ? '✓' : '○'}
                      </span>
                      <span className="text-gray-700">{formatFieldName(framework)}</span>
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}

          {/* Representative Engagement Strategy */}
          {profile.representative_engagement && Object.keys(profile.representative_engagement).length > 0 && (
            <section>
              <button
                onClick={() => toggleSection('engagement')}
                className="w-full text-left text-lg font-semibold text-gray-900 mb-3 flex items-center justify-between gap-2 hover:text-blue-600"
              >
                <span>🤝 Engagement Strategy</span>
                <span>{expandedSections.engagement ? '▼' : '▶'}</span>
              </button>
              {expandedSections.engagement && (
                <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                  {profile.representative_engagement.aligned_approach && (
                    <div>
                      <span className="font-medium text-gray-700">Aligned Representatives:</span>
                      <span className="ml-2 capitalize text-gray-600">
                        {profile.representative_engagement.aligned_approach.replace(/_/g, ' ')}
                      </span>
                    </div>
                  )}
                  {profile.representative_engagement.opposing_approach && (
                    <div>
                      <span className="font-medium text-gray-700">Opposing Representatives:</span>
                      <span className="ml-2 capitalize text-gray-600">
                        {profile.representative_engagement.opposing_approach.replace(/_/g, ' ')}
                      </span>
                    </div>
                  )}
                  {profile.representative_engagement.bipartisan_framing && (
                    <div>
                      <span className="font-medium text-gray-700">Bipartisan Framing:</span>
                      <span className="ml-2 capitalize text-gray-600">
                        {profile.representative_engagement.bipartisan_framing.replace(/_/g, ' ')}
                      </span>
                    </div>
                  )}
                </div>
              )}
            </section>
          )}

          {/* Regional Context */}
          {profile.regional_context && (profile.regional_context.community_type || profile.regional_context.state_concerns) && (
            <section>
              <button
                onClick={() => toggleSection('regional')}
                className="w-full text-left text-lg font-semibold text-gray-900 mb-3 flex items-center justify-between gap-2 hover:text-blue-600"
              >
                <span>📍 Regional Context</span>
                <span>{expandedSections.regional ? '▼' : '▶'}</span>
              </button>
              {expandedSections.regional && (
                <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                  {profile.regional_context.community_type && (
                    <div>
                      <span className="font-medium text-gray-700">Community Type:</span>
                      <span className="ml-2 capitalize text-gray-600">
                        {profile.regional_context.community_type}
                      </span>
                    </div>
                  )}
                  {profile.regional_context.state_concerns && (
                    <div>
                      <span className="font-medium text-gray-700">State/Local Concerns:</span>
                      <p className="text-gray-600 mt-1">{profile.regional_context.state_concerns}</p>
                    </div>
                  )}
                </div>
              )}
            </section>
          )}

          {/* Writing Samples */}
          {profile.writing_samples && profile.writing_samples.length > 0 && (
            <section>
              <button
                onClick={() => toggleSection('samples')}
                className="w-full text-left text-lg font-semibold text-gray-900 mb-3 flex items-center justify-between gap-2 hover:text-blue-600"
              >
                <span>✍️ Writing Samples ({profile.writing_samples.length})</span>
                <span>{expandedSections.samples ? '▼' : '▶'}</span>
              </button>
              {expandedSections.samples && (
                <div className="space-y-2">
                  {profile.writing_samples.map((sample, idx) => (
                    <div key={idx} className="bg-gray-50 rounded-lg p-4">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">
                        {sample.length > 300 ? sample.substring(0, 300) + '...' : sample}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}

          {/* Metadata */}
          <section className="text-xs text-gray-500 pt-4 border-t border-gray-200">
            <div className="flex gap-4">
              <span>Created: {new Date(profile.created_at).toLocaleDateString()}</span>
              <span>Updated: {new Date(profile.updated_at).toLocaleDateString()}</span>
              {profile.last_used_at && (
                <span>Last Used: {new Date(profile.last_used_at).toLocaleDateString()}</span>
              )}
            </div>
          </section>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4 flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
          >
            Close
          </button>
          <button
            onClick={onEdit}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
          >
            Edit Profile
          </button>
        </div>
      </div>
    </div>
  );
}
