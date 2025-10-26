import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { lettersAPI, repsAPI } from '../services/api';
import useAuthStore from '../stores/authStore';

export default function LetterWizard({ onClose }) {
  const navigate = useNavigate();

  const handleClose = () => {
    if (onClose) {
      onClose();
    } else {
      navigate('/letters');
    }
  };
  const { user } = useAuthStore();
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Data state
  const [writingProfiles, setWritingProfiles] = useState([]);
  const [savedReps, setSavedReps] = useState([]);

  // Form state
  const [formData, setFormData] = useState({
    writingProfileId: '',
    recipientIds: [],
    articleUrls: [],
    suggestedTopics: [],
    selectedTopic: '',
    customTopic: '',
    customContext: '',
    sameLetterForAll: true,
    generatedLetters: []
  });

  // UI state
  const [currentUrl, setCurrentUrl] = useState('');
  const [fetchingArticles, setFetchingArticles] = useState(false);
  const [generatingTopics, setGeneratingTopics] = useState(false);
  const [generatingLetters, setGeneratingLetters] = useState(false);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      const [profilesRes, repsRes] = await Promise.all([
        lettersAPI.getWritingProfiles(),
        repsAPI.getSavedRepresentatives()
      ]);

      setWritingProfiles(profilesRes.data || []);
      setSavedReps(repsRes.data.representatives || []);

      // Auto-select default writing profile
      const defaultProfile = profilesRes.data?.find(p => p.is_default);
      if (defaultProfile) {
        updateField('writingProfileId', defaultProfile.id);
      }
    } catch (err) {
      setError('Failed to load data: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const updateField = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError('');
  };

  const toggleRecipient = (repId) => {
    setFormData(prev => ({
      ...prev,
      recipientIds: prev.recipientIds.includes(repId)
        ? prev.recipientIds.filter(id => id !== repId)
        : [...prev.recipientIds, repId]
    }));
  };

  const addArticleUrl = () => {
    const trimmedUrl = currentUrl.trim();

    if (!trimmedUrl) {
      return;
    }

    // Validate URL format
    try {
      const url = new URL(trimmedUrl);
      // Ensure it's http or https
      if (!['http:', 'https:'].includes(url.protocol)) {
        setError('Please enter a valid HTTP or HTTPS URL');
        return;
      }
    } catch (e) {
      setError('Please enter a valid URL (e.g., https://example.com/article)');
      return;
    }

    // Check for duplicates
    if (formData.articleUrls.includes(trimmedUrl)) {
      setError('This URL has already been added');
      return;
    }

    // Add the URL
    setFormData(prev => ({
      ...prev,
      articleUrls: [...prev.articleUrls, trimmedUrl]
    }));
    setCurrentUrl('');
    setError('');
  };

  const removeArticleUrl = (index) => {
    setFormData(prev => ({
      ...prev,
      articleUrls: prev.articleUrls.filter((_, i) => i !== index)
    }));
  };

  const generateTopicSuggestions = async () => {
    if (formData.articleUrls.length === 0) {
      setError('Please add at least one article URL to generate topic suggestions');
      return;
    }

    setGeneratingTopics(true);
    setError('');

    try {
      const response = await lettersAPI.generateTopicSuggestions(formData.articleUrls);
      updateField('suggestedTopics', response.data.topics || []);
      // Explicitly clear any errors after successful generation
      setError('');
      // Don't auto-advance - let user select a topic first
    } catch (err) {
      setError('Failed to generate topics: ' + (err.response?.data?.detail || err.message));
    } finally {
      setGeneratingTopics(false);
    }
  };

  const generateLetters = async () => {
    setGeneratingLetters(true);
    setError('');

    const finalTopic = formData.customTopic || formData.selectedTopic;

    try {
      const response = await lettersAPI.generateLetter({
        writing_profile_id: formData.writingProfileId,
        recipient_ids: formData.recipientIds,
        topic: finalTopic,
        article_urls: formData.articleUrls,
        custom_context: formData.customContext,
        same_letter_for_all: formData.sameLetterForAll
      });

      // Transform the response to match the expected structure
      // Backend returns: { id, subject, base_content, recipients: [...] }
      // Frontend needs: [{ id, recipient_name, content, letter_id }, ...]
      const letter = response.data;
      const letters = letter.recipients.map(recipient => ({
        id: recipient.id,
        letter_id: letter.id,
        recipient_name: recipient.name,
        recipient_title: recipient.title,
        subject: recipient.personalized_subject || letter.subject,
        content: recipient.personalized_content || letter.base_content
      }));

      updateField('generatedLetters', letters);
      nextStep();
    } catch (err) {
      setError('Failed to generate letters: ' + (err.response?.data?.detail || err.message));
    } finally {
      setGeneratingLetters(false);
    }
  };

  const saveLetters = async () => {
    setLoading(true);
    setError('');

    try {
      // Get the letter_id from the first generated letter (they all share the same letter)
      if (formData.generatedLetters.length > 0) {
        const letterId = formData.generatedLetters[0].letter_id;
        await lettersAPI.finalizeLetter(letterId);
      }
      handleClose();
    } catch (err) {
      setError('Failed to save letters: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const nextStep = () => {
    if (validateCurrentStep()) {
      setCurrentStep(prev => prev + 1);
      setError('');
    }
  };

  const prevStep = () => {
    setCurrentStep(prev => prev - 1);
    setError('');
  };

  const validateCurrentStep = () => {
    switch (currentStep) {
      case 1:
        if (!formData.writingProfileId) {
          setError('Please select a writing profile');
          return false;
        }
        return true;
      case 2:
        if (formData.recipientIds.length === 0) {
          setError('Please select at least one representative');
          return false;
        }
        return true;
      case 3:
        // Articles are optional, but at least one is recommended
        return true;
      case 4:
        if (!formData.selectedTopic && !formData.customTopic) {
          setError('Please select or enter a topic for your letter');
          return false;
        }
        return true;
      case 5:
        // Additional context is optional
        return true;
      default:
        return true;
    }
  };

  const renderStepIndicator = () => {
    const steps = [
      { num: 1, label: 'Writing' },
      { num: 2, label: 'Recipients' },
      { num: 3, label: 'Context' },
      { num: 4, label: 'Topic' },
      { num: 5, label: 'Details' },
      { num: 6, label: 'Generate' },
      { num: 7, label: 'Review' }
    ];

    return (
      <>
        {/* Mobile: Progress Bar */}
        <div className="md:hidden mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              Step {currentStep} of {steps.length}: {steps[currentStep - 1].label}
            </span>
            <span className="text-xs text-gray-500">
              {Math.round((currentStep / steps.length) * 100)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(currentStep / steps.length) * 100}%` }}
            />
          </div>
        </div>

        {/* Desktop: Numbered Steps */}
        <div className="hidden md:flex items-center justify-between mb-8">
          {steps.map((step, idx) => (
            <div key={step.num} className="flex items-center flex-1 min-w-0">
              <div className="flex flex-col items-center flex-1 min-w-0">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm ${
                    currentStep === step.num
                      ? 'bg-blue-600 text-white'
                      : currentStep > step.num
                      ? 'bg-green-500 text-white'
                      : 'bg-gray-200 text-gray-600'
                  }`}
                >
                  {currentStep > step.num ? '✓' : step.num}
                </div>
                <span className="text-xs mt-1 text-gray-600 text-center">{step.label}</span>
              </div>
              {idx < steps.length - 1 && (
                <div
                  className={`h-1 flex-1 mx-2 ${
                    currentStep > step.num ? 'bg-green-500' : 'bg-gray-200'
                  }`}
                />
              )}
            </div>
          ))}
        </div>
      </>
    );
  };

  const renderStep1 = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-bold text-gray-900 mb-2">Select Writing Profile</h3>
        <p className="text-gray-600">Choose the writing style for your letter.</p>
      </div>

      {writingProfiles.length === 0 ? (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <div className="text-yellow-800 mb-4">
            <svg className="mx-auto h-12 w-12 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <h4 className="font-semibold text-lg">No Writing Profiles Found</h4>
          </div>
          <p className="text-sm text-yellow-700 mb-4">
            You need at least one writing profile to write letters.
          </p>
          <button
            onClick={() => navigate('/writing-profiles')}
            className="px-6 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 font-medium"
          >
            Create Writing Profile
          </button>
        </div>
      ) : (
        <div className="space-y-2 sm:space-y-3">
          {writingProfiles.map((profile) => (
            <label
              key={profile.id}
              className={`block p-2 sm:p-4 border rounded-lg cursor-pointer transition-colors ${
                formData.writingProfileId === profile.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <div className="flex items-start gap-1.5 sm:gap-3">
                <input
                  type="radio"
                  name="writingProfile"
                  value={profile.id}
                  checked={formData.writingProfileId === profile.id}
                  onChange={(e) => updateField('writingProfileId', e.target.value)}
                  className="mt-0.5 sm:mt-1 flex-shrink-0"
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
                    <span className="font-semibold text-gray-900 text-xs sm:text-base break-words leading-tight">{profile.name}</span>
                    {profile.is_default && (
                      <span className="px-1.5 py-0.5 text-[10px] sm:text-xs bg-blue-100 text-blue-700 rounded flex-shrink-0">
                        Default
                      </span>
                    )}
                  </div>
                  {profile.description && (
                    <p
                      className="text-xs sm:text-sm text-gray-600 mt-0.5 sm:mt-1"
                      style={{
                        display: '-webkit-box',
                        WebkitLineClamp: '1',
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis'
                      }}
                    >
                      {profile.description}
                    </p>
                  )}
                </div>
              </div>
            </label>
          ))}
        </div>
      )}
    </div>
  );

  const renderStep2 = () => {
    // Group representatives by Federal and State
    const federalReps = savedReps.filter(rep => rep.office_type?.startsWith('federal'));
    const stateReps = savedReps.filter(rep => !rep.office_type?.startsWith('federal'));

    const renderRepresentativeList = (reps) => (
      <div className="space-y-3">
        {reps.map((rep) => (
          <label
            key={rep.id}
            className={`block p-4 border rounded-lg cursor-pointer transition-colors ${
              formData.recipientIds.includes(rep.id)
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <div className="flex items-start">
              <input
                type="checkbox"
                checked={formData.recipientIds.includes(rep.id)}
                onChange={() => toggleRecipient(rep.id)}
                className="mt-1 mr-3"
              />
              <div className="flex-1">
                <div className="font-semibold text-gray-900">{rep.name}</div>
                <div className="text-sm text-gray-600">{rep.title}</div>
                <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                  {rep.party && <span>{rep.party}</span>}
                  {rep.district && <span>District {rep.district}</span>}
                </div>
              </div>
            </div>
          </label>
        ))}
      </div>
    );

    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-xl font-bold text-gray-900 mb-2">Select Recipients</h3>
          <p className="text-gray-600">Choose which representatives will receive your letter.</p>
        </div>

        {savedReps.length === 0 ? (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
            <h4 className="font-semibold text-lg text-yellow-800 mb-2">No Representatives Saved</h4>
            <p className="text-sm text-yellow-700 mb-4">
              You need to save representatives before you can write letters to them.
            </p>
            <button
              onClick={() => navigate('/representatives')}
              className="px-6 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 font-medium"
            >
              Find Representatives
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Federal Representatives */}
            {federalReps.length > 0 && (
              <div>
                <h4 className="text-lg font-semibold text-gray-800 mb-3">Federal Representatives</h4>
                {renderRepresentativeList(federalReps)}
              </div>
            )}

            {/* State Representatives */}
            {stateReps.length > 0 && (
              <div>
                <h4 className="text-lg font-semibold text-gray-800 mb-3">State Representatives</h4>
                {renderRepresentativeList(stateReps)}
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const renderStep3 = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-bold text-gray-900 mb-2">Add Context from News Articles</h3>
        <p className="text-gray-600">Add news articles to provide context for AI topic suggestions.</p>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <p className="text-sm text-blue-800">
          <strong>Recommended:</strong> Add URLs to news articles related to your advocacy area. The AI will analyze these to suggest relevant letter topics.
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Article URLs
        </label>
        <div className="flex flex-col sm:flex-row gap-2">
          <input
            type="url"
            value={currentUrl}
            onChange={(e) => setCurrentUrl(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addArticleUrl()}
            placeholder="https://example.com/article"
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            onClick={addArticleUrl}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 w-full sm:w-auto"
          >
            Add
          </button>
        </div>
      </div>

      {formData.articleUrls.length > 0 && (
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            Added Articles ({formData.articleUrls.length})
          </label>
          {formData.articleUrls.map((url, index) => (
            <div key={index} className="flex items-center gap-2 p-2 bg-gray-50 rounded">
              <span className="flex-1 text-sm text-gray-700 truncate">{url}</span>
              <button
                onClick={() => removeArticleUrl(index)}
                className="text-red-600 hover:text-red-700 text-sm"
              >
                Remove
              </button>
            </div>
          ))}
        </div>
      )}

      <div>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={formData.sameLetterForAll}
            onChange={(e) => updateField('sameLetterForAll', e.target.checked)}
            className="rounded"
          />
          <span className="text-sm text-gray-700">
            Generate the same letter for all recipients
          </span>
        </label>
        <p className="text-xs text-gray-500 mt-1 ml-6">
          {formData.sameLetterForAll
            ? 'One letter will be generated for all selected representatives'
            : 'Individual letters will be generated for each representative'}
        </p>
      </div>
    </div>
  );

  const renderStep4 = () => {
    const hasArticles = formData.articleUrls.length > 0;
    const hasTopicSuggestions = formData.suggestedTopics.length > 0;

    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-xl font-bold text-gray-900 mb-2">
            {hasArticles ? 'Choose or Enter Letter Topic' : 'Enter Letter Topic'}
          </h3>
          <p className="text-gray-600">
            {hasArticles
              ? 'AI will suggest topics based on your articles, or you can enter your own.'
              : 'Enter your letter topic below, or go back to step 3 to add articles for AI topic suggestions.'}
          </p>
        </div>

        {hasArticles && !hasTopicSuggestions && (
          <div className="text-center py-8">
            <button
              onClick={generateTopicSuggestions}
              disabled={generatingTopics}
              className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium disabled:opacity-50"
            >
              {generatingTopics ? 'Generating Topic Suggestions...' : 'Generate AI Topic Suggestions'}
            </button>
            <p className="text-sm text-gray-600 mt-3">
              AI will analyze your articles and suggest 10 relevant letter topics
            </p>
          </div>
        )}

        {hasTopicSuggestions && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Suggested Topics (Select One)
            </label>
            <select
              value={formData.selectedTopic}
              onChange={(e) => {
                updateField('selectedTopic', e.target.value);
                updateField('customTopic', '');
              }}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">-- Select a topic --</option>
              {formData.suggestedTopics.map((topic, index) => (
                <option key={index} value={topic}>
                  {topic}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Only show OR divider if there are AI suggestions to choose from */}
        {hasTopicSuggestions && (
          <div className="flex items-center gap-4">
            <div className="flex-1 border-t border-gray-300"></div>
            <span className="text-sm text-gray-600">OR</span>
            <div className="flex-1 border-t border-gray-300"></div>
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {hasTopicSuggestions ? 'Enter Your Own Topic' : 'Letter Topic'}
          </label>
          <input
            type="text"
            value={formData.customTopic}
            onChange={(e) => {
              updateField('customTopic', e.target.value);
              updateField('selectedTopic', '');
            }}
            placeholder="e.g., Support for Climate Change Legislation"
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          {!hasArticles && (
            <p className="text-sm text-gray-500 mt-2">
              💡 Tip: Add article URLs in step 3 to get AI-generated topic suggestions
            </p>
          )}
        </div>
      </div>
    );
  };

  const renderStep5 = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-bold text-gray-900 mb-2">Additional Context & Details</h3>
        <p className="text-gray-600">Add personal stories, specific points, or additional context for your letter.</p>
      </div>

      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h4 className="font-semibold text-gray-900 mb-1">Your Selected Topic:</h4>
        <p className="text-gray-700">{formData.customTopic || formData.selectedTopic}</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Additional Context (Optional)
        </label>
        <textarea
          value={formData.customContext}
          onChange={(e) => updateField('customContext', e.target.value)}
          placeholder="Provide any additional context, personal stories, or specific points you want to make..."
          rows={8}
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <p className="text-xs text-gray-500 mt-1">
          This will be incorporated into your letter along with the topic and article context
        </p>
      </div>
    </div>
  );

  const renderStep6 = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-bold text-gray-900 mb-2">Review & Generate Letters</h3>
        <p className="text-gray-600">Review your selections and generate AI-powered letters.</p>
      </div>

      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 space-y-4">
        <div>
          <h4 className="font-semibold text-gray-900">Writing Profile</h4>
          <p className="text-gray-700">
            {writingProfiles.find(p => p.id === formData.writingProfileId)?.name}
          </p>
        </div>

        <div>
          <h4 className="font-semibold text-gray-900">Recipients</h4>
          <p className="text-gray-700">{formData.recipientIds.length} representative(s) selected</p>
        </div>

        <div>
          <h4 className="font-semibold text-gray-900">Topic</h4>
          <p className="text-gray-700">{formData.customTopic || formData.selectedTopic}</p>
        </div>

        {formData.articleUrls.length > 0 && (
          <div>
            <h4 className="font-semibold text-gray-900">Context Articles</h4>
            <p className="text-gray-700">{formData.articleUrls.length} article(s) added</p>
          </div>
        )}

        {formData.customContext && (
          <div>
            <h4 className="font-semibold text-gray-900">Additional Context</h4>
            <p className="text-gray-700 text-sm">{formData.customContext.substring(0, 150)}...</p>
          </div>
        )}

        <div>
          <h4 className="font-semibold text-gray-900">Letter Strategy</h4>
          <p className="text-gray-700">
            {formData.sameLetterForAll
              ? 'Same letter for all recipients'
              : 'Individual letters for each recipient'}
          </p>
        </div>
      </div>

      <button
        onClick={generateLetters}
        disabled={generatingLetters}
        className="w-full px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium disabled:opacity-50"
      >
        {generatingLetters ? 'Generating Letters...' : 'Generate Letters'}
      </button>
    </div>
  );

  const renderStep7 = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-bold text-gray-900 mb-2">Review Your Letters</h3>
        <p className="text-gray-600">Review and edit your generated letters before saving.</p>
      </div>

      {formData.generatedLetters.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-gray-600">No letters generated yet.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {formData.generatedLetters.map((letter, index) => (
            <div key={letter.id} className="border border-gray-300 rounded-lg p-6">
              <div className="mb-4">
                <h4 className="font-semibold text-gray-900 text-lg mb-1">
                  Letter {index + 1}: To {letter.recipient_name}
                </h4>
                <p className="text-sm text-gray-600">{letter.recipient_title}</p>
              </div>

              <div className="mb-3">
                <p className="text-sm font-medium text-gray-700">Subject:</p>
                <p className="text-gray-900">{letter.subject}</p>
              </div>

              <div className="bg-white border border-gray-200 rounded p-4">
                <div className="whitespace-pre-wrap text-gray-800 font-serif text-sm leading-relaxed">
                  {letter.content}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="bg-green-50 border border-green-200 rounded-md p-4">
        <p className="text-sm text-green-800">
          Ready to save! Your letters will be saved to your account and available for download or sending.
        </p>
      </div>
    </div>
  );

  if (loading && currentStep === 1) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-600">Loading...</div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 overflow-y-auto">
      <div className="bg-white rounded-lg p-6 max-w-5xl w-full my-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Write New Letter</h1>
          <p className="text-gray-600 mt-2">Create advocacy letters to your representatives</p>
        </div>

        {renderStepIndicator()}

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <div className="min-h-[400px]">
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}
          {currentStep === 4 && renderStep4()}
          {currentStep === 5 && renderStep5()}
          {currentStep === 6 && renderStep6()}
          {currentStep === 7 && renderStep7()}
        </div>

        <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-200">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-gray-700 hover:text-gray-900"
          >
            Cancel
          </button>

          <div className="flex gap-3">
            {currentStep > 1 && currentStep < 7 && (
              <button
                onClick={prevStep}
                disabled={loading || generatingLetters}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 disabled:opacity-50"
              >
                Previous
              </button>
            )}

            {currentStep < 6 && writingProfiles.length > 0 && savedReps.length > 0 && (
              <button
                onClick={currentStep === 3 ? nextStep : nextStep}
                disabled={loading || generatingLetters}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {currentStep === 3 ? 'Continue to Topic Selection' : 'Next'}
              </button>
            )}

            {currentStep === 7 && (
              <button
                onClick={saveLetters}
                disabled={loading}
                className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 font-medium disabled:opacity-50"
              >
                {loading ? 'Saving...' : 'Save Letters'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
