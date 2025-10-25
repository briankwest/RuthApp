import { useState, useEffect } from 'react';
import { lettersAPI } from '../services/api';
import useAuthStore from '../stores/authStore';

export default function VoiceProfileWizard({ onClose, onSuccess }) {
  const { user } = useAuthStore();
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [politicalData, setPoliticalData] = useState(null);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    political_leaning: '',
    key_issues: [],
    custom_issues: '',
    preferred_tone: 'professional',
    writing_samples: [],
    additional_context: ''
  });

  // AI-generated descriptions
  const [aiDescriptions, setAiDescriptions] = useState(null);
  const [selectedDescription, setSelectedDescription] = useState('');

  // Load political issues data
  useEffect(() => {
    loadPoliticalData();
  }, []);

  const loadPoliticalData = async () => {
    try {
      const response = await lettersAPI.getPoliticalIssues();
      setPoliticalData(response.data);
    } catch (err) {
      console.error('Failed to load political issues:', err);
    }
  };

  const updateField = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError('');
  };

  const toggleIssue = (issueValue) => {
    setFormData(prev => ({
      ...prev,
      key_issues: prev.key_issues.includes(issueValue)
        ? prev.key_issues.filter(i => i !== issueValue)
        : [...prev.key_issues, issueValue]
    }));
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
        if (!formData.name.trim()) {
          setError('Please enter a profile name');
          return false;
        }
        return true;
      case 2:
        if (formData.key_issues.length === 0 && !formData.custom_issues.trim()) {
          setError('Please select at least one issue or enter custom issues');
          return false;
        }
        return true;
      case 3:
        if (!formData.preferred_tone) {
          setError('Please select a writing tone');
          return false;
        }
        return true;
      case 4:
        if (!selectedDescription.trim()) {
          setError('Please generate and select a profile description');
          return false;
        }
        return true;
      default:
        return true;
    }
  };

  const generateDescriptions = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await lettersAPI.generateDescription({
        user_name: user?.full_name || user?.email || 'Advocate',
        user_city: user?.city,
        user_state: user?.state,
        selected_issues: formData.key_issues,
        custom_issues: formData.custom_issues,
        political_leaning: formData.political_leaning,
        tone: politicalData?.tones?.find(t => t.value === formData.preferred_tone)?.label || 'Professional',
        additional_context: formData.additional_context
      });

      setAiDescriptions(response.data.descriptions);
      // Auto-select the balanced version by default
      if (response.data.descriptions.balanced) {
        setSelectedDescription(response.data.descriptions.balanced);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate descriptions');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!validateCurrentStep()) return;

    setLoading(true);
    setError('');

    try {
      await lettersAPI.createVoiceProfile({
        name: formData.name,
        description: selectedDescription,
        political_leaning: formData.political_leaning,
        key_issues: formData.key_issues,
        preferred_tone: formData.preferred_tone,
        writing_samples: formData.writing_samples,
        is_default: false
      });

      onSuccess();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create profile');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const renderStepIndicator = () => {
    const steps = [
      { num: 1, label: 'Basics' },
      { num: 2, label: 'Issues' },
      { num: 3, label: 'Tone' },
      { num: 4, label: 'Generate' },
      { num: 5, label: 'Samples' },
      { num: 6, label: 'Review' }
    ];

    return (
      <div className="flex items-center justify-between mb-8">
        {steps.map((step, idx) => (
          <div key={step.num} className="flex items-center flex-1">
            <div className="flex flex-col items-center flex-1">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                  currentStep === step.num
                    ? 'bg-blue-600 text-white'
                    : currentStep > step.num
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-200 text-gray-600'
                }`}
              >
                {currentStep > step.num ? '✓' : step.num}
              </div>
              <span className="text-xs mt-1 text-gray-600">{step.label}</span>
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
    );
  };

  const renderStep1 = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-bold text-gray-900 mb-2">Profile Basics</h3>
        <p className="text-gray-600">Give your voice profile a name and optional description.</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Profile Name *
        </label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => updateField('name', e.target.value)}
          placeholder="e.g., My Default Voice, Climate Advocate, etc."
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Brief Description (Optional)
        </label>
        <textarea
          value={formData.description}
          onChange={(e) => updateField('description', e.target.value)}
          placeholder="Briefly describe when you'd use this profile..."
          rows={3}
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <p className="text-xs text-gray-500 mt-1">
          Note: AI will generate a more detailed description in Step 4
        </p>
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-bold text-gray-900 mb-2">Political Values & Issues</h3>
        <p className="text-gray-600">Select the issues you care about most.</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Political Leaning (Optional)
        </label>
        <select
          value={formData.political_leaning}
          onChange={(e) => updateField('political_leaning', e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">Select your leaning...</option>
          {politicalData?.political_leanings?.map((leaning) => (
            <option key={leaning.value} value={leaning.value}>
              {leaning.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Key Issues * (Select all that apply)
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-96 overflow-y-auto">
          {politicalData?.issues?.map((issue) => (
            <label
              key={issue.value}
              className={`flex items-start p-3 border rounded-md cursor-pointer transition-colors ${
                formData.key_issues.includes(issue.value)
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <input
                type="checkbox"
                checked={formData.key_issues.includes(issue.value)}
                onChange={() => toggleIssue(issue.value)}
                className="mt-1 mr-3"
              />
              <div>
                <div className="font-medium text-gray-900">{issue.label}</div>
                <div className="text-xs text-gray-600">{issue.description}</div>
              </div>
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Custom Issues or Additional Context
        </label>
        <textarea
          value={formData.custom_issues}
          onChange={(e) => updateField('custom_issues', e.target.value)}
          placeholder="Add any specific issues or concerns not listed above..."
          rows={3}
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-bold text-gray-900 mb-2">Writing Style Preferences</h3>
        <p className="text-gray-600">Choose the tone that best represents your voice.</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Preferred Tone *
        </label>
        <div className="space-y-3">
          {politicalData?.tones?.map((tone) => (
            <label
              key={tone.value}
              className={`flex items-start p-4 border rounded-md cursor-pointer transition-colors ${
                formData.preferred_tone === tone.value
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <input
                type="radio"
                name="tone"
                value={tone.value}
                checked={formData.preferred_tone === tone.value}
                onChange={(e) => updateField('preferred_tone', e.target.value)}
                className="mt-1 mr-3"
              />
              <div>
                <div className="font-medium text-gray-900">{tone.label}</div>
                <div className="text-sm text-gray-600">{tone.description}</div>
              </div>
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Additional Context (Optional)
        </label>
        <textarea
          value={formData.additional_context}
          onChange={(e) => updateField('additional_context', e.target.value)}
          placeholder="Any specific writing preferences, phrases to use/avoid, or style notes..."
          rows={3}
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>
    </div>
  );

  const renderStep4 = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-bold text-gray-900 mb-2">AI-Assisted Profile Generation</h3>
        <p className="text-gray-600">
          Let AI generate personalized profile descriptions based on your preferences.
        </p>
      </div>

      {!aiDescriptions ? (
        <div className="text-center py-8">
          <button
            onClick={generateDescriptions}
            disabled={loading}
            className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Generating...' : 'Generate Profile Descriptions'}
          </button>
          <p className="text-sm text-gray-600 mt-3">
            This will create 3 variations of your voice profile for you to choose from.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-sm font-medium text-gray-700">
            Select the description that best represents your voice:
          </p>

          {aiDescriptions.formal && (
            <label
              className={`block p-4 border rounded-md cursor-pointer transition-colors ${
                selectedDescription === aiDescriptions.formal
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <input
                type="radio"
                name="description"
                checked={selectedDescription === aiDescriptions.formal}
                onChange={() => setSelectedDescription(aiDescriptions.formal)}
                className="mr-3"
              />
              <span className="font-medium text-gray-900">Formal & Professional</span>
              <p className="text-sm text-gray-700 mt-2 ml-6">{aiDescriptions.formal}</p>
            </label>
          )}

          {aiDescriptions.passionate && (
            <label
              className={`block p-4 border rounded-md cursor-pointer transition-colors ${
                selectedDescription === aiDescriptions.passionate
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <input
                type="radio"
                name="description"
                checked={selectedDescription === aiDescriptions.passionate}
                onChange={() => setSelectedDescription(aiDescriptions.passionate)}
                className="mr-3"
              />
              <span className="font-medium text-gray-900">Passionate & Personal</span>
              <p className="text-sm text-gray-700 mt-2 ml-6">{aiDescriptions.passionate}</p>
            </label>
          )}

          {aiDescriptions.balanced && (
            <label
              className={`block p-4 border rounded-md cursor-pointer transition-colors ${
                selectedDescription === aiDescriptions.balanced
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <input
                type="radio"
                name="description"
                checked={selectedDescription === aiDescriptions.balanced}
                onChange={() => setSelectedDescription(aiDescriptions.balanced)}
                className="mr-3"
              />
              <span className="font-medium text-gray-900">Balanced & Persuasive</span>
              <p className="text-sm text-gray-700 mt-2 ml-6">{aiDescriptions.balanced}</p>
            </label>
          )}

          <div className="pt-4">
            <button
              onClick={generateDescriptions}
              disabled={loading}
              className="text-sm text-blue-600 hover:text-blue-700 underline"
            >
              Regenerate descriptions
            </button>
          </div>
        </div>
      )}
    </div>
  );

  const renderStep5 = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-bold text-gray-900 mb-2">Writing Samples (Optional)</h3>
        <p className="text-gray-600">
          Paste examples of your writing to further refine your voice profile.
        </p>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <p className="text-sm text-blue-800">
          <strong>Optional:</strong> Writing samples help AI better match your personal style. You can
          skip this step if you prefer.
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Paste Your Writing Samples
        </label>
        <textarea
          value={formData.writing_samples.join('\n\n---\n\n')}
          onChange={(e) =>
            updateField(
              'writing_samples',
              e.target.value.split('\n\n---\n\n').filter((s) => s.trim())
            )
          }
          placeholder="Paste examples of emails, letters, or posts you've written... Separate multiple samples with '---'"
          rows={12}
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
        />
        <p className="text-xs text-gray-500 mt-1">
          Separate multiple samples with "---" on its own line
        </p>
      </div>
    </div>
  );

  const renderStep6 = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-bold text-gray-900 mb-2">Review Your Profile</h3>
        <p className="text-gray-600">Review your voice profile before saving.</p>
      </div>

      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 space-y-4">
        <div>
          <h4 className="font-semibold text-gray-900">Profile Name</h4>
          <p className="text-gray-700">{formData.name}</p>
        </div>

        {formData.political_leaning && (
          <div>
            <h4 className="font-semibold text-gray-900">Political Leaning</h4>
            <p className="text-gray-700 capitalize">{formData.political_leaning}</p>
          </div>
        )}

        <div>
          <h4 className="font-semibold text-gray-900">Key Issues</h4>
          <div className="flex flex-wrap gap-2 mt-2">
            {formData.key_issues.map((issueValue) => {
              const issue = politicalData?.issues?.find((i) => i.value === issueValue);
              return (
                <span
                  key={issueValue}
                  className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                >
                  {issue?.label || issueValue}
                </span>
              );
            })}
          </div>
          {formData.custom_issues && (
            <p className="text-sm text-gray-600 mt-2">
              <strong>Custom:</strong> {formData.custom_issues}
            </p>
          )}
        </div>

        <div>
          <h4 className="font-semibold text-gray-900">Preferred Tone</h4>
          <p className="text-gray-700 capitalize">
            {politicalData?.tones?.find((t) => t.value === formData.preferred_tone)?.label}
          </p>
        </div>

        <div>
          <h4 className="font-semibold text-gray-900">AI-Generated Description</h4>
          <p className="text-gray-700">{selectedDescription}</p>
        </div>

        {formData.writing_samples.length > 0 && (
          <div>
            <h4 className="font-semibold text-gray-900">Writing Samples</h4>
            <p className="text-sm text-gray-600">
              {formData.writing_samples.length} sample(s) provided
            </p>
          </div>
        )}
      </div>

      <div className="bg-green-50 border border-green-200 rounded-md p-4">
        <p className="text-sm text-green-800">
          Ready to save! This profile will be used to generate advocacy letters in your unique voice.
        </p>
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 overflow-y-auto">
      <div className="bg-white rounded-lg p-6 max-w-4xl w-full my-8">
        {renderStepIndicator()}

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
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
        </div>

        <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 hover:text-gray-900"
          >
            Cancel
          </button>

          <div className="flex gap-3">
            {currentStep > 1 && (
              <button
                onClick={prevStep}
                disabled={loading}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 disabled:opacity-50"
              >
                Previous
              </button>
            )}

            {currentStep < 6 && (
              <button
                onClick={nextStep}
                disabled={loading}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                Next
              </button>
            )}

            {currentStep === 6 && (
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 font-medium disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Profile'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
