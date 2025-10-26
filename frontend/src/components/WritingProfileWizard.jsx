import { useState, useEffect } from 'react';
import { lettersAPI } from '../services/api';
import useAuthStore from '../stores/authStore';

export default function WritingProfileWizard({ onClose, onSuccess, editMode = false, existingProfile = null }) {
  const { user } = useAuthStore();
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [politicalData, setPoliticalData] = useState(null);

  // Form state - ENHANCED
  const [formData, setFormData] = useState({
    // Basic info
    name: '',
    description: '',
    political_leaning: '',

    // Enhanced issue positions (position, priority, personal_connection per issue)
    issue_positions: {},

    // Abortion position
    abortion_position: '',

    // Core values (array of selected values)
    core_values: [],

    // Tone
    preferred_tone: 'professional',
    additional_context: '',

    // Argumentative frameworks (object with framework: bool)
    argumentative_frameworks: {},

    // Representative engagement
    representative_engagement: {
      aligned_approach: '',
      opposing_approach: '',
      bipartisan_framing: ''
    },

    // Regional context
    regional_context: {
      state_concerns: '',
      community_type: ''
    },

    // Compromise positioning
    compromise_positioning: {
      incremental_progress: '',
      bipartisan_preference: ''
    },

    // Writing samples
    writing_samples: []
  });

  // AI-generated descriptions
  const [aiDescriptions, setAiDescriptions] = useState(null);
  const [selectedDescription, setSelectedDescription] = useState('');

  // Load political issues data
  useEffect(() => {
    loadPoliticalData();
  }, []);

  // Pre-populate form data when in edit mode
  useEffect(() => {
    if (editMode && existingProfile) {
      setFormData({
        name: existingProfile.name || '',
        description: existingProfile.description || '',
        political_leaning: existingProfile.political_leaning || '',
        issue_positions: existingProfile.issue_positions || {},
        abortion_position: existingProfile.abortion_position || '',
        core_values: existingProfile.core_values || [],
        preferred_tone: existingProfile.preferred_tone || 'professional',
        additional_context: '',
        argumentative_frameworks: existingProfile.argumentative_frameworks || {},
        representative_engagement: existingProfile.representative_engagement || {
          aligned_approach: '',
          opposing_approach: '',
          bipartisan_framing: ''
        },
        regional_context: existingProfile.regional_context || {
          state_concerns: '',
          community_type: ''
        },
        compromise_positioning: existingProfile.compromise_positioning || {
          incremental_progress: '',
          bipartisan_preference: ''
        },
        writing_samples: existingProfile.writing_samples || []
      });
      setSelectedDescription(existingProfile.description || '');
    }
  }, [editMode, existingProfile]);

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

  const updateNestedField = (parentField, childField, value) => {
    setFormData(prev => ({
      ...prev,
      [parentField]: {
        ...prev[parentField],
        [childField]: value
      }
    }));
    setError('');
  };

  const toggleIssueSelection = (issueValue) => {
    setFormData(prev => {
      const newPositions = { ...prev.issue_positions };
      if (newPositions[issueValue]) {
        delete newPositions[issueValue];
      } else {
        newPositions[issueValue] = {
          position: '',
          priority: '',
          personal_connection: ''
        };
      }
      return { ...prev, issue_positions: newPositions };
    });
  };

  const updateIssuePosition = (issueValue, field, value) => {
    setFormData(prev => ({
      ...prev,
      issue_positions: {
        ...prev.issue_positions,
        [issueValue]: {
          ...prev.issue_positions[issueValue],
          [field]: value
        }
      }
    }));
  };

  const toggleCoreValue = (valueKey) => {
    setFormData(prev => ({
      ...prev,
      core_values: prev.core_values.includes(valueKey)
        ? prev.core_values.filter(v => v !== valueKey)
        : [...prev.core_values, valueKey]
    }));
  };

  const toggleFramework = (framework) => {
    setFormData(prev => ({
      ...prev,
      argumentative_frameworks: {
        ...prev.argumentative_frameworks,
        [framework]: !prev.argumentative_frameworks[framework]
      }
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

  const isNextButtonDisabled = () => {
    // Check if Next button should be disabled for current step
    if (loading) return true;

    // Step 8: Disable until descriptions are generated
    if (currentStep === 8 && !aiDescriptions) {
      return true;
    }

    return false;
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
        const selectedIssues = Object.keys(formData.issue_positions);
        if (selectedIssues.length === 0) {
          setError('Please select at least one issue');
          return false;
        }
        // Check that selected issues have position and priority
        for (const issue of selectedIssues) {
          if (!formData.issue_positions[issue].position || !formData.issue_positions[issue].priority) {
            setError('Please set position and priority for all selected issues');
            return false;
          }
        }
        return true;
      case 3:
        // Abortion position is optional
        return true;
      case 4:
        if (formData.core_values.length < 3) {
          setError('Please select at least 3 core values');
          return false;
        }
        if (formData.core_values.length > 5) {
          setError('Please select no more than 5 core values');
          return false;
        }
        return true;
      case 5:
        if (!formData.preferred_tone) {
          setError('Please select a writing tone');
          return false;
        }
        return true;
      case 6:
        const selectedFrameworks = Object.values(formData.argumentative_frameworks).filter(Boolean).length;
        if (selectedFrameworks === 0) {
          setError('Please select at least one argumentative framework');
          return false;
        }
        return true;
      case 7:
        if (!formData.representative_engagement.aligned_approach ||
            !formData.representative_engagement.opposing_approach ||
            !formData.representative_engagement.bipartisan_framing) {
          setError('Please complete all representative engagement options');
          return false;
        }
        return true;
      case 8:
        if (!aiDescriptions) {
          setError('Please generate descriptions for your profile');
          return false;
        }
        if (!selectedDescription.trim()) {
          setError('Please select a profile description');
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
      // Build enhanced prompt data
      const selectedIssues = Object.keys(formData.issue_positions).map(issueKey => {
        const issue = politicalData?.issues?.find(i => i.value === issueKey);
        const position = formData.issue_positions[issueKey];
        return {
          issue: issue?.label || issueKey,
          position: position.position,
          priority: position.priority,
          personal_connection: position.personal_connection
        };
      });

      const response = await lettersAPI.generateDescription({
        user_name: user?.full_name || user?.email || 'Advocate',
        user_city: user?.city,
        user_state: user?.state,
        selected_issues: selectedIssues,
        political_leaning: formData.political_leaning,
        abortion_position: formData.abortion_position,
        core_values: formData.core_values,
        tone: politicalData?.tones?.find(t => t.value === formData.preferred_tone)?.label || 'Professional',
        argumentative_frameworks: formData.argumentative_frameworks,
        representative_engagement: formData.representative_engagement,
        additional_context: formData.additional_context
      });

      setAiDescriptions(response.data.descriptions);
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
      const profileData = {
        name: formData.name,
        description: selectedDescription,
        political_leaning: formData.political_leaning,
        issue_positions: formData.issue_positions,
        abortion_position: formData.abortion_position,
        core_values: formData.core_values,
        preferred_tone: formData.preferred_tone,
        argumentative_frameworks: formData.argumentative_frameworks,
        representative_engagement: formData.representative_engagement,
        regional_context: formData.regional_context,
        compromise_positioning: formData.compromise_positioning,
        writing_samples: formData.writing_samples,
        is_default: editMode ? existingProfile.is_default : false
      };

      if (editMode && existingProfile) {
        await lettersAPI.updateWritingProfile(existingProfile.id, profileData);
      } else {
        await lettersAPI.createWritingProfile(profileData);
      }

      onSuccess();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || `Failed to ${editMode ? 'update' : 'create'} profile`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const renderStepIndicator = () => {
    const steps = [
      { num: 1, label: 'Basics' },
      { num: 2, label: 'Issues' },
      { num: 3, label: 'Abortion' },
      { num: 4, label: 'Values' },
      { num: 5, label: 'Tone' },
      { num: 6, label: 'Arguments' },
      { num: 7, label: 'Engagement' },
      { num: 8, label: 'Generate' },
      { num: 9, label: 'Samples' },
      { num: 10, label: 'Review' }
    ];

    return (
      <>
        {/* Mobile: Condensed step indicator */}
        <div className="md:hidden mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Step {currentStep} of {steps.length}: {steps[currentStep - 1].label}
            </span>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {Math.round((currentStep / steps.length) * 100)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(currentStep / steps.length) * 100}%` }}
            />
          </div>
        </div>

        {/* Desktop: Full step indicator */}
        <div className="hidden md:flex items-center justify-between mb-8 overflow-x-auto">
          {steps.map((step, idx) => (
            <div key={step.num} className="flex items-center flex-shrink-0">
              <div className="flex flex-col items-center">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold ${
                    currentStep === step.num
                      ? 'bg-blue-600 text-white'
                      : currentStep > step.num
                      ? 'bg-green-500 text-white'
                      : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                  }`}
                >
                  {currentStep > step.num ? '✓' : step.num}
                </div>
                <span className="text-[10px] mt-1 text-gray-600 dark:text-gray-400 text-center">{step.label}</span>
              </div>
              {idx < steps.length - 1 && (
                <div
                  className={`h-0.5 w-6 mx-1 ${
                    currentStep > step.num ? 'bg-green-500' : 'bg-gray-200 dark:bg-gray-700'
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
        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Profile Basics</h3>
        <p className="text-gray-600 dark:text-gray-400">Give your writing profile a name and optional description.</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Profile Name *
        </label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => updateField('name', e.target.value)}
          placeholder="e.g., My Default Style, Climate Advocate, etc."
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Brief Description (Optional)
        </label>
        <textarea
          value={formData.description}
          onChange={(e) => updateField('description', e.target.value)}
          placeholder="Briefly describe when you'd use this profile..."
          rows={3}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          Note: AI will generate a more detailed description later
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Political Leaning (Optional)
        </label>
        <select
          value={formData.political_leaning}
          onChange={(e) => updateField('political_leaning', e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">Select your leaning...</option>
          {politicalData?.political_leanings?.map((leaning) => (
            <option key={leaning.value} value={leaning.value}>
              {leaning.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );

  const renderStep2 = () => {
    const selectedIssues = Object.keys(formData.issue_positions);

    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Issues You Care About</h3>
          <p className="text-gray-600 dark:text-gray-400">Select issues and specify your position, priority, and why you care.</p>
        </div>

        <div className="space-y-4 max-h-96 overflow-y-auto">
          {politicalData?.issues?.map((issue) => {
            const isSelected = selectedIssues.includes(issue.value);
            const position = formData.issue_positions[issue.value] || {};

            return (
              <div
                key={issue.value}
                className={`border rounded-md p-4 ${
                  isSelected ? 'border-blue-500 bg-blue-50 dark:border-blue-400 dark:bg-blue-900/30' : 'border-gray-300 dark:border-gray-600'
                }`}
              >
                <label className="flex items-start cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleIssueSelection(issue.value)}
                    className="mt-1 mr-3"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-gray-900 dark:text-white">{issue.label}</div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">{issue.description}</div>

                    {isSelected && (
                      <div className="mt-3 space-y-3 pl-6 border-l-2 border-blue-300 dark:border-blue-600">
                        <div>
                          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Your Position *
                          </label>
                          <select
                            value={position.position || ''}
                            onChange={(e) => updateIssuePosition(issue.value, 'position', e.target.value)}
                            className="w-full px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-white rounded-md"
                          >
                            <option value="">Select position...</option>
                            {politicalData?.position_options?.map((pos) => (
                              <option key={pos.value} value={pos.value}>
                                {pos.label}
                              </option>
                            ))}
                          </select>
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Priority Level *
                          </label>
                          <select
                            value={position.priority || ''}
                            onChange={(e) => updateIssuePosition(issue.value, 'priority', e.target.value)}
                            className="w-full px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-white rounded-md"
                          >
                            <option value="">Select priority...</option>
                            {politicalData?.priority_options?.map((pri) => (
                              <option key={pri.value} value={pri.value}>
                                {pri.label} - {pri.description}
                              </option>
                            ))}
                          </select>
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Why This Matters to You (Optional)
                          </label>
                          <textarea
                            value={position.personal_connection || ''}
                            onChange={(e) => updateIssuePosition(issue.value, 'personal_connection', e.target.value)}
                            placeholder="Personal story, experience, or reason..."
                            rows={2}
                            className="w-full px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 rounded-md"
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </label>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderStep3 = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Abortion Position</h3>
        <p className="text-gray-600 dark:text-gray-400">This issue often requires more nuanced positioning. Select your stance (optional).</p>
      </div>

      <div className="space-y-3">
        {politicalData?.abortion_positions?.map((position) => (
          <label
            key={position.value}
            className={`flex items-start p-4 border rounded-md cursor-pointer transition-colors ${
              formData.abortion_position === position.value
                ? 'border-blue-500 bg-blue-50 dark:border-blue-400 dark:bg-blue-900/30'
                : 'border-gray-300 dark:border-gray-600 hover:border-gray-400'
            }`}
          >
            <input
              type="radio"
              name="abortion_position"
              value={position.value}
              checked={formData.abortion_position === position.value}
              onChange={(e) => updateField('abortion_position', e.target.value)}
              className="mt-1 mr-3"
            />
            <div>
              <div className="font-medium text-gray-900 dark:text-white">{position.label}</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">{position.description}</div>
            </div>
          </label>
        ))}
      </div>
    </div>
  );

  const renderStep4 = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Core Values</h3>
        <p className="text-gray-600 dark:text-gray-400">Select 3-5 core values that guide your political decisions.</p>
      </div>

      <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-md p-3">
        <p className="text-sm text-blue-800 dark:text-blue-300">
          Selected: {formData.core_values.length} / 5 (minimum 3 required)
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-96 overflow-y-auto">
        {politicalData?.core_values?.map((value) => (
          <label
            key={value.value}
            className={`flex items-start p-3 border rounded-md cursor-pointer transition-colors ${
              formData.core_values.includes(value.value)
                ? 'border-blue-500 bg-blue-50 dark:border-blue-400 dark:bg-blue-900/30'
                : 'border-gray-300 dark:border-gray-600 hover:border-gray-400'
            }`}
          >
            <input
              type="checkbox"
              checked={formData.core_values.includes(value.value)}
              onChange={() => toggleCoreValue(value.value)}
              className="mt-1 mr-3"
            />
            <div>
              <div className="font-medium text-gray-900 dark:text-white">{value.label}</div>
              <div className="text-xs text-gray-600 dark:text-gray-400">{value.description}</div>
            </div>
          </label>
        ))}
      </div>
    </div>
  );

  const renderStep5 = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Writing Tone</h3>
        <p className="text-gray-600 dark:text-gray-400">Choose the tone that best represents your voice.</p>
      </div>

      <div className="space-y-3">
        {politicalData?.tones?.map((tone) => (
          <label
            key={tone.value}
            className={`flex items-start p-4 border rounded-md cursor-pointer transition-colors ${
              formData.preferred_tone === tone.value
                ? 'border-blue-500 bg-blue-50 dark:border-blue-400 dark:bg-blue-900/30'
                : 'border-gray-300 dark:border-gray-600 hover:border-gray-400'
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
              <div className="font-medium text-gray-900 dark:text-white">{tone.label}</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">{tone.description}</div>
            </div>
          </label>
        ))}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Additional Context (Optional)
        </label>
        <textarea
          value={formData.additional_context}
          onChange={(e) => updateField('additional_context', e.target.value)}
          placeholder="Any specific writing preferences, phrases to use/avoid, or style notes..."
          rows={3}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>
    </div>
  );

  const renderStep6 = () => {
    const selectedCount = Object.values(formData.argumentative_frameworks).filter(Boolean).length;

    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Argumentative Frameworks</h3>
          <p className="text-gray-600 dark:text-gray-400">Select the types of arguments you want to emphasize in your letters.</p>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
          <p className="text-sm text-blue-800">
            Selected: {selectedCount} framework{selectedCount !== 1 ? 's' : ''} (at least 1 required)
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {politicalData?.argumentative_frameworks?.map((framework) => (
            <label
              key={framework.value}
              className={`flex items-start p-3 border rounded-md cursor-pointer transition-colors ${
                formData.argumentative_frameworks[framework.value]
                  ? 'border-blue-500 bg-blue-50 dark:border-blue-400 dark:bg-blue-900/30'
                  : 'border-gray-300 dark:border-gray-600 hover:border-gray-400'
              }`}
            >
              <input
                type="checkbox"
                checked={!!formData.argumentative_frameworks[framework.value]}
                onChange={() => toggleFramework(framework.value)}
                className="mt-1 mr-3"
              />
              <div>
                <div className="font-medium text-gray-900 dark:text-white">{framework.label}</div>
                <div className="text-xs text-gray-600 dark:text-gray-400">{framework.description}</div>
              </div>
            </label>
          ))}
        </div>
      </div>
    );
  };

  const renderStep7 = () => (
    <div className="space-y-6 max-h-[300px] sm:max-h-[500px] overflow-y-auto pr-2">
      <div>
        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Representative Engagement Strategy</h3>
        <p className="text-gray-600 dark:text-gray-400">How should letters be framed based on representative alignment?</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Approach for Aligned Representatives *
        </label>
        <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
          Representatives who generally share your views
        </p>
        <div className="space-y-2">
          {politicalData?.engagement_approaches?.aligned?.map((approach) => (
            <label
              key={approach.value}
              className={`flex items-start p-3 border rounded-md cursor-pointer transition-colors ${
                formData.representative_engagement.aligned_approach === approach.value
                  ? 'border-blue-500 bg-blue-50 dark:border-blue-400 dark:bg-blue-900/30'
                  : 'border-gray-300 dark:border-gray-600 hover:border-gray-400'
              }`}
            >
              <input
                type="radio"
                name="aligned_approach"
                value={approach.value}
                checked={formData.representative_engagement.aligned_approach === approach.value}
                onChange={(e) => updateNestedField('representative_engagement', 'aligned_approach', e.target.value)}
                className="mt-1 mr-3"
              />
              <div>
                <div className="font-medium text-gray-900 dark:text-white">{approach.label}</div>
                <div className="text-xs text-gray-600 dark:text-gray-400">{approach.description}</div>
              </div>
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Approach for Opposing Representatives *
        </label>
        <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
          Representatives who generally oppose your views
        </p>
        <div className="space-y-2">
          {politicalData?.engagement_approaches?.opposing?.map((approach) => (
            <label
              key={approach.value}
              className={`flex items-start p-3 border rounded-md cursor-pointer transition-colors ${
                formData.representative_engagement.opposing_approach === approach.value
                  ? 'border-blue-500 bg-blue-50 dark:border-blue-400 dark:bg-blue-900/30'
                  : 'border-gray-300 dark:border-gray-600 hover:border-gray-400'
              }`}
            >
              <input
                type="radio"
                name="opposing_approach"
                value={approach.value}
                checked={formData.representative_engagement.opposing_approach === approach.value}
                onChange={(e) => updateNestedField('representative_engagement', 'opposing_approach', e.target.value)}
                className="mt-1 mr-3"
              />
              <div>
                <div className="font-medium text-gray-900 dark:text-white">{approach.label}</div>
                <div className="text-xs text-gray-600 dark:text-gray-400">{approach.description}</div>
              </div>
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Bipartisan Framing Preference *
        </label>
        <div className="space-y-2">
          {politicalData?.engagement_approaches?.bipartisan?.map((approach) => (
            <label
              key={approach.value}
              className={`flex items-start p-3 border rounded-md cursor-pointer transition-colors ${
                formData.representative_engagement.bipartisan_framing === approach.value
                  ? 'border-blue-500 bg-blue-50 dark:border-blue-400 dark:bg-blue-900/30'
                  : 'border-gray-300 dark:border-gray-600 hover:border-gray-400'
              }`}
            >
              <input
                type="radio"
                name="bipartisan_framing"
                value={approach.value}
                checked={formData.representative_engagement.bipartisan_framing === approach.value}
                onChange={(e) => updateNestedField('representative_engagement', 'bipartisan_framing', e.target.value)}
                className="mt-1 mr-3"
              />
              <div>
                <div className="font-medium text-gray-900 dark:text-white">{approach.label}</div>
                <div className="text-xs text-gray-600 dark:text-gray-400">{approach.description}</div>
              </div>
            </label>
          ))}
        </div>
      </div>

      <div className="border-t pt-4">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Community Type (Optional)
        </label>
        <select
          value={formData.regional_context.community_type}
          onChange={(e) => updateNestedField('regional_context', 'community_type', e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-white rounded-md"
        >
          <option value="">Select your community type...</option>
          {politicalData?.community_types?.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          State/Local Concerns (Optional)
        </label>
        <textarea
          value={formData.regional_context.state_concerns}
          onChange={(e) => updateNestedField('regional_context', 'state_concerns', e.target.value)}
          placeholder="Any state-specific or local concerns that are important to you..."
          rows={3}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-white rounded-md"
        />
      </div>
    </div>
  );

  const renderStep8 = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">AI-Assisted Profile Generation</h3>
        <p className="text-gray-600 dark:text-gray-400">
          Let AI generate personalized profile descriptions based on all your preferences.
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
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-3">
            This will create 3 variations of your writing profile for you to choose from.
          </p>
          <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-700 rounded-md">
            <p className="text-sm text-yellow-800 dark:text-yellow-300">
              ⚠️ You must generate descriptions before proceeding to the next step
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Select the description that best represents your voice:
          </p>

          {aiDescriptions.formal && (
            <label
              className={`block p-4 border rounded-md cursor-pointer transition-colors ${
                selectedDescription === aiDescriptions.formal
                  ? 'border-blue-500 bg-blue-50 dark:border-blue-400 dark:bg-blue-900/30'
                  : 'border-gray-300 dark:border-gray-600 hover:border-gray-400'
              }`}
            >
              <input
                type="radio"
                name="description"
                checked={selectedDescription === aiDescriptions.formal}
                onChange={() => setSelectedDescription(aiDescriptions.formal)}
                className="mr-3"
              />
              <span className="font-medium text-gray-900 dark:text-white">Formal & Professional</span>
              <p className="text-sm text-gray-700 dark:text-gray-300 mt-2 ml-6">{aiDescriptions.formal}</p>
            </label>
          )}

          {aiDescriptions.passionate && (
            <label
              className={`block p-4 border rounded-md cursor-pointer transition-colors ${
                selectedDescription === aiDescriptions.passionate
                  ? 'border-blue-500 bg-blue-50 dark:border-blue-400 dark:bg-blue-900/30'
                  : 'border-gray-300 dark:border-gray-600 hover:border-gray-400'
              }`}
            >
              <input
                type="radio"
                name="description"
                checked={selectedDescription === aiDescriptions.passionate}
                onChange={() => setSelectedDescription(aiDescriptions.passionate)}
                className="mr-3"
              />
              <span className="font-medium text-gray-900 dark:text-white">Passionate & Personal</span>
              <p className="text-sm text-gray-700 dark:text-gray-300 mt-2 ml-6">{aiDescriptions.passionate}</p>
            </label>
          )}

          {aiDescriptions.balanced && (
            <label
              className={`block p-4 border rounded-md cursor-pointer transition-colors ${
                selectedDescription === aiDescriptions.balanced
                  ? 'border-blue-500 bg-blue-50 dark:border-blue-400 dark:bg-blue-900/30'
                  : 'border-gray-300 dark:border-gray-600 hover:border-gray-400'
              }`}
            >
              <input
                type="radio"
                name="description"
                checked={selectedDescription === aiDescriptions.balanced}
                onChange={() => setSelectedDescription(aiDescriptions.balanced)}
                className="mr-3"
              />
              <span className="font-medium text-gray-900 dark:text-white">Balanced & Persuasive</span>
              <p className="text-sm text-gray-700 dark:text-gray-300 mt-2 ml-6">{aiDescriptions.balanced}</p>
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

  const renderStep9 = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Writing Samples (Optional)</h3>
        <p className="text-gray-600 dark:text-gray-400">
          Paste examples of your writing to further refine your writing profile.
        </p>
      </div>

      <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-md p-4">
        <p className="text-sm text-blue-800 dark:text-blue-300">
          <strong>Optional:</strong> Writing samples help AI better match your personal style. You can
          skip this step if you prefer.
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
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
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
        />
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          Separate multiple samples with "---" on its own line
        </p>
      </div>
    </div>
  );

  const renderStep10 = () => {
    const selectedIssues = Object.keys(formData.issue_positions);

    return (
      <div className="space-y-6 max-h-[300px] sm:max-h-[500px] overflow-y-auto">
        <div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Review Your Profile</h3>
          <p className="text-gray-600 dark:text-gray-400">Review your writing profile before saving.</p>
        </div>

        <div className="bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-6 space-y-4">
          <div>
            <h4 className="font-semibold text-gray-900 dark:text-white">Profile Name</h4>
            <p className="text-gray-700 dark:text-gray-300">{formData.name}</p>
          </div>

          {formData.political_leaning && (
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-white">Political Leaning</h4>
              <p className="text-gray-700 dark:text-gray-300 capitalize">{formData.political_leaning}</p>
            </div>
          )}

          <div>
            <h4 className="font-semibold text-gray-900 dark:text-white">Key Issues ({selectedIssues.length})</h4>
            <div className="space-y-2 mt-2">
              {selectedIssues.map((issueValue) => {
                const issue = politicalData?.issues?.find((i) => i.value === issueValue);
                const position = formData.issue_positions[issueValue];
                return (
                  <div key={issueValue} className="border-l-4 border-blue-400 pl-3 py-1">
                    <div className="font-medium text-gray-900 dark:text-white">{issue?.label || issueValue}</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      Position: <span className="capitalize">{position.position?.replace('_', ' ')}</span> |
                      Priority: <span className="capitalize">{position.priority}</span>
                    </div>
                    {position.personal_connection && (
                      <div className="text-xs text-gray-600 dark:text-gray-400 italic mt-1">
                        "{position.personal_connection}"
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {formData.abortion_position && (
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-white">Abortion Position</h4>
              <p className="text-gray-700 dark:text-gray-300">
                {politicalData?.abortion_positions?.find(p => p.value === formData.abortion_position)?.label}
              </p>
            </div>
          )}

          <div>
            <h4 className="font-semibold text-gray-900 dark:text-white">Core Values ({formData.core_values.length})</h4>
            <div className="flex flex-wrap gap-2 mt-2">
              {formData.core_values.map((valueKey) => {
                const value = politicalData?.core_values?.find((v) => v.value === valueKey);
                return (
                  <span
                    key={valueKey}
                    className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm"
                  >
                    {value?.label || valueKey}
                  </span>
                );
              })}
            </div>
          </div>

          <div>
            <h4 className="font-semibold text-gray-900 dark:text-white">Preferred Tone</h4>
            <p className="text-gray-700 dark:text-gray-300 capitalize">
              {politicalData?.tones?.find((t) => t.value === formData.preferred_tone)?.label}
            </p>
          </div>

          <div>
            <h4 className="font-semibold text-gray-900 dark:text-white">Argumentative Frameworks</h4>
            <div className="flex flex-wrap gap-2 mt-2">
              {Object.keys(formData.argumentative_frameworks).filter(k => formData.argumentative_frameworks[k]).map((fwKey) => {
                const fw = politicalData?.argumentative_frameworks?.find((f) => f.value === fwKey);
                return (
                  <span
                    key={fwKey}
                    className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm"
                  >
                    {fw?.label || fwKey}
                  </span>
                );
              })}
            </div>
          </div>

          <div>
            <h4 className="font-semibold text-gray-900 dark:text-white">Representative Engagement</h4>
            <div className="text-sm text-gray-700 dark:text-gray-300 space-y-1 mt-2">
              <div>Aligned Reps: <span className="capitalize">{formData.representative_engagement.aligned_approach}</span></div>
              <div>Opposing Reps: <span className="capitalize">{formData.representative_engagement.opposing_approach}</span></div>
              <div>Bipartisan Framing: <span className="capitalize">{formData.representative_engagement.bipartisan_framing}</span></div>
            </div>
          </div>

          <div>
            <h4 className="font-semibold text-gray-900 dark:text-white">AI-Generated Description</h4>
            <p className="text-gray-700 dark:text-gray-300 text-sm">{selectedDescription}</p>
          </div>

          {formData.writing_samples.length > 0 && (
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-white">Writing Samples</h4>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {formData.writing_samples.length} sample(s) provided
              </p>
            </div>
          )}
        </div>

        <div className="bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-700 rounded-md p-4">
          <p className="text-sm text-green-800 dark:text-green-300">
            Ready to save! This profile will be used to generate advocacy letters in your unique voice.
          </p>
        </div>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 overflow-y-auto">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-5xl w-full my-8">
        {renderStepIndicator()}

        {error && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded-md">
            <p className="text-sm text-red-600 dark:text-red-300">{error}</p>
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
          {currentStep === 8 && renderStep8()}
          {currentStep === 9 && renderStep9()}
          {currentStep === 10 && renderStep10()}
        </div>

        <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:text-white"
          >
            Cancel
          </button>

          <div className="flex gap-3">
            {currentStep > 1 && (
              <button
                onClick={prevStep}
                disabled={loading}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
              >
                Previous
              </button>
            )}

            {currentStep < 10 && (
              <button
                onClick={nextStep}
                disabled={isNextButtonDisabled()}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            )}

            {currentStep === 10 && (
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 font-medium disabled:opacity-50"
              >
                {loading
                  ? (editMode ? 'Saving...' : 'Creating...')
                  : (editMode ? 'Save Changes' : 'Create Profile')
                }
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
