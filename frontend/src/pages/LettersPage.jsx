import { useState, useEffect, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { lettersAPI } from '../services/api';
import RichTextEditor from '../components/RichTextEditor';
import Toast from '../components/Toast';
import LetterWizard from '../components/LetterWizard';
import useAuthStore from '../stores/authStore';

export default function LettersPage() {
  const navigate = useNavigate();
  const [letters, setLetters] = useState([]);
  const [filteredLetters, setFilteredLetters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRepFilter, setSelectedRepFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('draft'); // 'draft' or 'finalized'
  const [showWizard, setShowWizard] = useState(false);

  // Edit recipient modal
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingRecipient, setEditingRecipient] = useState(null);
  const [editedContent, setEditedContent] = useState('');
  const [saving, setSaving] = useState(false);

  // PDF generation options modal
  const [showPdfOptionsModal, setShowPdfOptionsModal] = useState(false);
  const [pdfOptions, setPdfOptions] = useState({
    action: 'download', // 'download' or 'print'
    letterId: null,
    recipientId: null,
    recipientName: '',
    include_email: false,
    include_phone: false
  });

  // Email options modal
  const [showEmailOptionsModal, setShowEmailOptionsModal] = useState(false);
  const [emailOptions, setEmailOptions] = useState({
    recipientEmail: '',
    recipientName: '',
    subject: '',
    content: '',
    include_email: false,
    include_phone: false
  });

  // Website prompt after copy
  const [showWebsitePrompt, setShowWebsitePrompt] = useState(false);
  const [websitePromptData, setWebsitePromptData] = useState({
    recipientName: '',
    website: ''
  });

  // Toggle letter status
  const [togglingStatus, setTogglingStatus] = useState(null);

  useEffect(() => {
    loadLetters();
  }, []);

  useEffect(() => {
    filterLetters();
  }, [letters, searchTerm, selectedRepFilter, statusFilter]);

  const loadLetters = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await lettersAPI.getLetters({ limit: 50 });
      setLetters(response.data || []);
    } catch (err) {
      if (err.response?.status !== 404) {
        setError('Failed to load letters');
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filterLetters = () => {
    let result = [...letters];

    // Filter by status
    result = result.filter(letter => letter.status === statusFilter);

    // Filter by search term (only search subject and recipient names, not full content for performance)
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter(letter =>
        letter.subject?.toLowerCase().includes(term) ||
        letter.category?.toLowerCase().includes(term) ||
        letter.recipients?.some(r => r.name.toLowerCase().includes(term))
      );
    }

    // Filter by representative
    if (selectedRepFilter !== 'all') {
      result = result.filter(letter =>
        letter.recipients?.some(r => r.name === selectedRepFilter)
      );
    }

    setFilteredLetters(result);
  };

  // Get unique representative names for filter dropdown (memoized to prevent recalculation on every render)
  const representativeNames = useMemo(() => {
    const names = new Set();
    letters.forEach(letter => {
      letter.recipients?.forEach(r => names.add(r.name));
    });
    return Array.from(names).sort();
  }, [letters]);

  const handleDownloadPDF = (letterId, recipientId, recipientName) => {
    // Show modal to collect PDF options
    setPdfOptions({
      action: 'download',
      letterId,
      recipientId,
      recipientName,
      include_email: false,
      include_phone: false
    });
    setShowPdfOptionsModal(true);
  };

  const confirmGeneratePDF = async () => {
    try {
      const { action, letterId, recipientId, recipientName, include_email, include_phone } = pdfOptions;

      const response = await lettersAPI.generatePDF(letterId, recipientId, {
        include_email,
        include_phone
      });

      // Get the PDF path from the response
      const pdfPath = response.data.pdf_path;
      const filename = response.data.filename;

      // Create download URL (uploads are served at /uploads)
      // Add timestamp to prevent caching
      const downloadUrl = `/${pdfPath}?t=${Date.now()}`;

      if (action === 'print') {
        // Open PDF in new window and trigger print dialog
        const printWindow = window.open(downloadUrl, '_blank');

        if (printWindow) {
          // Wait for PDF to load, then trigger print dialog
          printWindow.onload = () => {
            setTimeout(() => {
              printWindow.print();
            }, 500);
          };
        } else {
          setError('Please allow pop-ups to print letters');
          setTimeout(() => setError(''), 3000);
        }
      } else {
        // Download action
        // Create a temporary link element and trigger download
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = filename || `letter-${recipientName.replace(/\s+/g, '-')}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }

      // Close modal
      setShowPdfOptionsModal(false);
    } catch (err) {
      const actionText = pdfOptions.action === 'print' ? 'print' : 'download';
      setError(`Failed to ${actionText} PDF for ${pdfOptions.recipientName}: ${err.response?.data?.detail || err.message}`);
      setTimeout(() => setError(''), 3000);
      setShowPdfOptionsModal(false);
    }
  };

  const handleEmailLetter = (recipientEmail, recipientName, subject, content) => {
    // Show modal to collect email options
    setEmailOptions({
      recipientEmail,
      recipientName,
      subject,
      content,
      include_email: false,
      include_phone: false
    });
    setShowEmailOptionsModal(true);
  };

  const confirmSendEmail = () => {
    try {
      const { recipientEmail, subject, content, include_email, include_phone } = emailOptions;
      const { user } = useAuthStore.getState();

      // Build signature
      let signature = `\n\nSincerely,\n${user.first_name} ${user.last_name}`;

      if (include_email && user.email) {
        signature += `\n${user.email}`;
      }

      if (include_phone && user.phone_number) {
        signature += `\n${user.phone_number}`;
      }

      // Build mailto link with signature
      const emailBody = content + signature;
      const mailtoLink = `mailto:${recipientEmail}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(emailBody)}`;

      // Open email client
      window.location.href = mailtoLink;

      // Close modal
      setShowEmailOptionsModal(false);
    } catch (err) {
      setError(`Failed to open email client: ${err.message}`);
      setTimeout(() => setError(''), 3000);
      setShowEmailOptionsModal(false);
    }
  };

  const handleDownloadText = (letter) => {
    const element = document.createElement('a');
    const file = new Blob([letter.base_content], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `letter-${letter.subject.replace(/\s+/g, '-')}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const handleDelete = async (letterId) => {
    if (!window.confirm('Are you sure you want to delete this letter?')) {
      return;
    }

    try {
      await lettersAPI.deleteLetter(letterId);
      loadLetters();
    } catch (err) {
      alert('Failed to delete letter: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleToggleStatus = async (letterId, currentStatus) => {
    try {
      setTogglingStatus(letterId);
      const newStatus = currentStatus === 'draft' ? 'finalized' : 'draft';
      await lettersAPI.updateLetterStatus(letterId, newStatus);
      await loadLetters();
      setSuccess(`Letter marked as ${newStatus === 'finalized' ? 'sent' : 'draft'}`);
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Failed to update letter status: ' + (err.response?.data?.detail || err.message));
      setTimeout(() => setError(''), 3000);
    } finally {
      setTogglingStatus(null);
    }
  };

  const startEditingRecipient = (letterId, recipient) => {
    setEditingRecipient({ letterId, ...recipient });
    setEditedContent(recipient.content || '');
    setShowEditModal(true);
  };

  const cancelEditingRecipient = () => {
    setShowEditModal(false);
    setEditingRecipient(null);
    setEditedContent('');
  };

  const saveRecipientEdit = async () => {
    if (!editingRecipient) return;

    try {
      setSaving(true);
      await lettersAPI.updateRecipientContent(
        editingRecipient.letterId,
        editingRecipient.id,
        editedContent
      );
      setShowEditModal(false);
      setEditingRecipient(null);
      setEditedContent('');
      await loadLetters();
    } catch (err) {
      alert('Failed to save changes: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
    }
  };

  const handleCopyLetter = async (recipient) => {
    if (!recipient.content || !recipient.content.trim()) {
      setError('No content to copy');
      setTimeout(() => setError(''), 3000);
      return;
    }

    try {
      await navigator.clipboard.writeText(recipient.content);
      setSuccess(`Letter for ${recipient.name} copied to clipboard!`);
      setTimeout(() => setSuccess(''), 3000);

      // If recipient has a website, offer to open it
      if (recipient.website && recipient.website.trim()) {
        setWebsitePromptData({
          recipientName: recipient.name,
          website: recipient.website
        });
        setShowWebsitePrompt(true);
      }
    } catch (err) {
      setError('Failed to copy to clipboard');
      setTimeout(() => setError(''), 3000);
    }
  };

  const openRepWebsite = () => {
    if (websitePromptData.website) {
      window.open(websitePromptData.website, '_blank');
    }
    setShowWebsitePrompt(false);
  };

  const handlePrintLetter = (letterId, recipientId, recipientName) => {
    // Show modal to collect PDF options for printing
    setPdfOptions({
      action: 'print',
      letterId,
      recipientId,
      recipientName,
      include_email: false,
      include_phone: false
    });
    setShowPdfOptionsModal(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-600">Loading letters...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {success && <Toast message={success} type="success" onClose={() => setSuccess('')} />}
      {error && <Toast message={error} type="error" onClose={() => setError('')} />}

      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Letters</h1>
          <p className="mt-2 text-gray-600">View and manage all your advocacy letters</p>
        </div>
        <button
          onClick={() => setShowWizard(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium w-full sm:w-auto text-center"
        >
          Write New Letter
        </button>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Status Toggle */}
      {letters.length > 0 && (
        <div className="bg-white shadow-sm rounded-lg p-4">
          <div className="flex items-center justify-center mb-6">
            <div className="inline-flex items-center bg-gray-200 rounded-full p-1">
              <button
                onClick={() => setStatusFilter('draft')}
                className={`px-6 py-2 rounded-full font-medium text-sm transition-all ${
                  statusFilter === 'draft'
                    ? 'bg-yellow-500 text-white shadow-md'
                    : 'text-gray-700 hover:text-gray-900'
                }`}
              >
                Draft
              </button>
              <button
                onClick={() => setStatusFilter('finalized')}
                className={`px-6 py-2 rounded-full font-medium text-sm transition-all ${
                  statusFilter === 'finalized'
                    ? 'bg-green-500 text-white shadow-md'
                    : 'text-gray-700 hover:text-gray-900'
                }`}
              >
                Sent
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Search letters
              </label>
              <input
                type="text"
                placeholder="Search by subject, category, or recipient..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Filter by Representative */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Filter by representative
              </label>
              <select
                value={selectedRepFilter}
                onChange={(e) => setSelectedRepFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All representatives</option>
                {representativeNames.map(name => (
                  <option key={name} value={name}>{name}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Results count */}
          <div className="mt-3 text-sm text-gray-600">
            Showing {filteredLetters.length} of {letters.length} letters
          </div>
        </div>
      )}

      {letters.length === 0 ? (
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
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900">
              No letters yet
            </h3>
            <p className="mt-2 text-sm text-gray-600">
              Get started by writing your first advocacy letter to your representatives.
            </p>
            <button
              onClick={() => setShowWizard(true)}
              className="mt-6 px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
            >
              Write Your First Letter
            </button>
          </div>
        </div>
      ) : filteredLetters.length === 0 ? (
        <div className="bg-white shadow-sm rounded-lg p-12 text-center">
          <div className="max-w-md mx-auto">
            <h3 className="text-lg font-medium text-gray-900">No matching letters found</h3>
            <p className="mt-2 text-sm text-gray-600">
              Try adjusting your search or filter criteria
            </p>
            <button
              onClick={() => {
                setSearchTerm('');
                setSelectedRepFilter('all');
              }}
              className="mt-4 px-4 py-2 text-sm border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
            >
              Clear filters
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredLetters.map((letter) => (
            <div
              key={letter.id}
              className="bg-white shadow-sm rounded-lg p-6 hover:shadow-md transition-shadow"
            >
              {/* Header with Subject and Date */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900">{letter.subject}</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Created: {new Date(letter.created_at).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </p>

                  {/* Status toggle */}
                  <div className="mt-3 flex items-center gap-4 flex-wrap">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-700">Status:</span>
                      <button
                        onClick={() => handleToggleStatus(letter.id, letter.status)}
                        disabled={togglingStatus === letter.id}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                          letter.status === 'finalized'
                            ? 'bg-green-500 focus:ring-green-500'
                            : 'bg-yellow-500 focus:ring-yellow-500'
                        } ${togglingStatus === letter.id ? 'opacity-50 cursor-not-allowed' : ''}`}
                        title={`Mark as ${letter.status === 'draft' ? 'sent' : 'draft'}`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            letter.status === 'finalized' ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                      <span className={`text-sm font-medium ${
                        letter.status === 'finalized' ? 'text-green-700' : 'text-yellow-700'
                      }`}>
                        {letter.status === 'finalized' ? 'Sent' : 'Draft'}
                      </span>
                    </div>
                    {letter.category && (
                      <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                        {letter.category}
                      </span>
                    )}
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2 ml-4">
                  <button
                    onClick={() => handleDelete(letter.id)}
                    className="px-3 py-1.5 text-sm border border-red-300 text-red-700 rounded-md hover:bg-red-50"
                  >
                    Delete
                  </button>
                </div>
              </div>

              {/* Recipients Section */}
              {letter.recipients && letter.recipients.length > 0 && (
                <div className="p-4 bg-gray-50 rounded-lg">
                  <h4 className="text-sm font-semibold text-gray-700 mb-3">
                    Recipients ({letter.recipients.length})
                  </h4>
                  <div className="space-y-2">
                    {letter.recipients.map((recipient) => {
                      const wordCount = recipient.content ? recipient.content.split(/\s+/).filter(w => w).length : 0;
                      return (
                        <div key={recipient.id} className="p-3 bg-white rounded border border-gray-200">
                          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                            <div className="flex-1">
                              <div className="font-medium text-gray-900">{recipient.name}</div>
                              <div className="text-sm text-gray-600">{recipient.title}</div>
                              {recipient.subject && (
                                <div className="text-sm text-gray-700 mt-1 italic">
                                  Subject: {recipient.subject}
                                </div>
                              )}
                              {wordCount > 0 && (
                                <div className="text-xs text-gray-500 mt-1">
                                  {wordCount} words
                                </div>
                              )}
                            </div>
                            <div className="grid grid-cols-2 sm:flex gap-2">
                              <button
                                onClick={() => startEditingRecipient(letter.id, recipient)}
                                className="px-3 py-1.5 text-sm border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 font-medium"
                              >
                                📝 Edit
                              </button>
                              {recipient.email && (
                                <button
                                  onClick={() => handleEmailLetter(recipient.email, recipient.name, recipient.subject || letter.subject, recipient.content || '')}
                                  className="px-3 py-1.5 text-sm border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 font-medium"
                                >
                                  ✉️ Email
                                </button>
                              )}
                              <button
                                onClick={() => handleCopyLetter(recipient)}
                                className="px-3 py-1.5 text-sm border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 font-medium"
                              >
                                📋 Copy
                              </button>
                              <button
                                onClick={() => handlePrintLetter(letter.id, recipient.id, recipient.name)}
                                className="px-3 py-1.5 text-sm border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 font-medium"
                              >
                                🖨️ Print
                              </button>
                              <button
                                onClick={() => handleDownloadPDF(letter.id, recipient.id, recipient.name)}
                                className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
                              >
                                📄 PDF
                              </button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Edit Recipient Modal */}
      {showEditModal && editingRecipient && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-bold text-gray-900 mb-2">
              Edit Letter for {editingRecipient.name}
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              {editingRecipient.title} • {editingRecipient.subject}
            </p>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Letter Content
              </label>
              <RichTextEditor
                value={editedContent}
                onChange={setEditedContent}
                placeholder="Enter letter content..."
              />
            </div>

            <div className="flex gap-3 justify-end">
              <button
                onClick={cancelEditingRecipient}
                disabled={saving}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={saveRecipientEdit}
                disabled={saving}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* PDF Options Modal */}
      {showPdfOptionsModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold text-gray-900 mb-4">
              PDF Generation Options
            </h3>
            <p className="text-gray-600 mb-4">
              Generating PDF for: <span className="font-semibold">{pdfOptions.recipientName}</span>
            </p>

            <div className="space-y-3 mb-6">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={pdfOptions.include_email}
                  onChange={(e) => setPdfOptions(prev => ({ ...prev, include_email: e.target.checked }))}
                  className="rounded"
                />
                <span className="text-sm text-gray-700">
                  Include my email address in signature
                </span>
              </label>

              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={pdfOptions.include_phone}
                  onChange={(e) => setPdfOptions(prev => ({ ...prev, include_phone: e.target.checked }))}
                  className="rounded"
                />
                <span className="text-sm text-gray-700">
                  Include my phone number in signature
                </span>
              </label>
            </div>

            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowPdfOptionsModal(false)}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={confirmGeneratePDF}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Generate PDF
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Email Options Modal */}
      {showEmailOptionsModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold text-gray-900 mb-4">
              Email Options
            </h3>
            <p className="text-gray-600 mb-4">
              Sending email to: <span className="font-semibold">{emailOptions.recipientName}</span>
            </p>

            <div className="space-y-3 mb-6">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={emailOptions.include_email}
                  onChange={(e) => setEmailOptions(prev => ({ ...prev, include_email: e.target.checked }))}
                  className="rounded"
                />
                <span className="text-sm text-gray-700">
                  Include my email address in signature
                </span>
              </label>

              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={emailOptions.include_phone}
                  onChange={(e) => setEmailOptions(prev => ({ ...prev, include_phone: e.target.checked }))}
                  className="rounded"
                />
                <span className="text-sm text-gray-700">
                  Include my phone number in signature
                </span>
              </label>
            </div>

            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowEmailOptionsModal(false)}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={confirmSendEmail}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Open Email Client
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Website Prompt Modal */}
      {showWebsitePrompt && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold text-gray-900 mb-4">
              Letter Copied!
            </h3>
            <p className="text-gray-700 mb-6">
              Your letter for <strong>{websitePromptData.recipientName}</strong> has been copied to your clipboard.
            </p>
            <p className="text-gray-600 mb-6">
              Would you like to open {websitePromptData.recipientName}'s website to paste it into their contact form?
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowWebsitePrompt(false)}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                No Thanks
              </button>
              <button
                onClick={openRepWebsite}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Open Website
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Letter Wizard Modal */}
      {showWizard && (
        <LetterWizard
          onClose={() => {
            setShowWizard(false);
            loadLetters();
          }}
        />
      )}
    </div>
  );
}
