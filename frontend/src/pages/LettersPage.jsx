import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { lettersAPI } from '../services/api';
import RichTextEditor from '../components/RichTextEditor';

export default function LettersPage() {
  const [letters, setLetters] = useState([]);
  const [filteredLetters, setFilteredLetters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRepFilter, setSelectedRepFilter] = useState('all');

  // Edit recipient modal
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingRecipient, setEditingRecipient] = useState(null);
  const [editedContent, setEditedContent] = useState('');
  const [saving, setSaving] = useState(false);

  // PDF generation options modal
  const [showPdfOptionsModal, setShowPdfOptionsModal] = useState(false);
  const [pdfOptions, setPdfOptions] = useState({
    letterId: null,
    recipientId: null,
    recipientName: '',
    include_email: false,
    include_phone: false
  });

  useEffect(() => {
    loadLetters();
  }, []);

  useEffect(() => {
    filterLetters();
  }, [letters, searchTerm, selectedRepFilter]);

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
      const { letterId, recipientId, recipientName, include_email, include_phone } = pdfOptions;

      const response = await lettersAPI.generatePDF(letterId, recipientId, {
        include_email,
        include_phone
      });

      // Get the PDF path from the response
      const pdfPath = response.data.pdf_path;
      const filename = response.data.filename;

      // Create download URL (uploads are served at /uploads)
      const downloadUrl = `/${pdfPath}`;

      // Create a temporary link element and trigger download
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename || `letter-${recipientName.replace(/\s+/g, '-')}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // Close modal
      setShowPdfOptionsModal(false);
    } catch (err) {
      alert(`Failed to download PDF for ${pdfOptions.recipientName}: ` + (err.response?.data?.detail || err.message));
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-600">Loading letters...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Letters</h1>
          <p className="mt-2 text-gray-600">View and manage all your advocacy letters</p>
        </div>
        <Link
          to="/letters/new"
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
        >
          Write New Letter
        </Link>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Search and Filter Controls */}
      {letters.length > 0 && (
        <div className="bg-white shadow-sm rounded-lg p-4">
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
            <Link
              to="/letters/new"
              className="mt-6 inline-block px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
            >
              Write Your First Letter
            </Link>
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

                  {/* Status badge */}
                  <div className="mt-2 flex items-center gap-3 text-xs">
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
                          <div className="flex items-start justify-between">
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
                            <div className="flex gap-2 ml-4">
                              <button
                                onClick={() => startEditingRecipient(letter.id, recipient)}
                                className="px-3 py-1.5 text-sm border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 font-medium"
                              >
                                Edit
                              </button>
                              <button
                                onClick={() => handleDownloadPDF(letter.id, recipient.id, recipient.name)}
                                className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
                              >
                                Download PDF
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
    </div>
  );
}
