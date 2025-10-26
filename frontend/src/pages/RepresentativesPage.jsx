import { useState, useEffect } from 'react';
import { repsAPI } from '../services/api';
import Toast from '../components/Toast';

// Representative Card Component
function RepresentativeCard({ rep, onSave }) {
  const [saving, setSaving] = useState(false);
  const [imageError, setImageError] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(rep);
    } finally {
      setSaving(false);
    }
  };

  const handleImageError = () => {
    setImageError(true);
  };

  // Placeholder SVG for broken/missing images
  const PlaceholderAvatar = () => (
    <div className="w-20 h-20 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center flex-shrink-0">
      <svg className="w-12 h-12 text-white" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
      </svg>
    </div>
  );

  return (
    <div className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
      <div className="flex flex-wrap items-start gap-4">
        {/* Photo */}
        {rep.photo_url && !imageError ? (
          <img
            src={rep.photo_url}
            alt={rep.name}
            onError={handleImageError}
            className="w-20 h-20 rounded-lg object-cover flex-shrink-0"
          />
        ) : (
          <PlaceholderAvatar />
        )}

        {/* Basic Info - stays next to image */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="text-lg font-bold text-gray-900">{rep.name}</h3>
              <p className="text-sm text-gray-600">{rep.title}</p>
              {rep.party && (
                <span className="inline-block mt-1 px-2 py-1 text-xs font-semibold rounded bg-gray-100 text-gray-700">
                  {rep.party}
                </span>
              )}
            </div>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-3 py-1 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 whitespace-nowrap flex-shrink-0"
            >
              {saving ? 'Saving...' : 'Save'}
            </button>
          </div>
        </div>

        {/* Contact Info and Offices - wraps below on mobile, full width */}
        <div className="basis-full sm:basis-auto sm:flex-1 sm:min-w-0">
          {/* Contact Info */}
          <div className="mt-3 space-y-1 text-sm">
            {rep.contact?.phone && (
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                </svg>
                <a href={`tel:${rep.contact.phone}`} className="text-gray-700 hover:text-blue-600">{rep.contact.phone}</a>
              </div>
            )}
            {rep.contact?.email && (
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <a href={`mailto:${rep.contact.email}`} className="text-blue-600 hover:text-blue-700 truncate">
                  {rep.contact.email}
                </a>
              </div>
            )}
            {rep.contact?.website && (
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                </svg>
                <a
                  href={rep.contact.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-700 truncate"
                >
                  Visit Website
                </a>
              </div>
            )}
          </div>

          {/* Social Media */}
          {(rep.social_media?.twitter || rep.social_media?.facebook || rep.social_media?.youtube) && (
            <div className="mt-3 flex items-center gap-3">
              {rep.social_media.twitter && (
                <a
                  href={`https://twitter.com/${rep.social_media.twitter}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-400 hover:text-blue-400"
                  title="Twitter"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" />
                  </svg>
                </a>
              )}
              {rep.social_media.facebook && (
                <a
                  href={`https://facebook.com/${rep.social_media.facebook}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-400 hover:text-blue-600"
                  title="Facebook"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
                  </svg>
                </a>
              )}
              {rep.social_media.youtube && (
                <a
                  href={`https://youtube.com/${rep.social_media.youtube}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-400 hover:text-red-600"
                  title="YouTube"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
                  </svg>
                </a>
              )}
            </div>
          )}

          {/* Offices */}
          {rep.offices && rep.offices.length > 0 && (
            <div className="mt-4 pt-3 border-t border-gray-200">
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Offices</h4>
              <div className="space-y-2">
                {rep.offices.map((office, idx) => (
                  <div key={idx} className="text-sm text-gray-600 break-words">
                    <p className="font-medium">{office.name}</p>
                    <p className="break-words">{office.street_1}</p>
                    {office.city && office.state && (
                      <p>{office.city}, {office.state} {office.zip}</p>
                    )}
                    {office.phone && <p>Phone: <a href={`tel:${office.phone}`} className="hover:text-blue-600">{office.phone}</a></p>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Saved Representative Card Component
function SavedRepCard({ rep, confirmDeleteRep, onRemove, onConfirmRemove, onCancelRemove }) {
  const [imageError, setImageError] = useState(false);

  const handleImageError = () => {
    setImageError(true);
  };

  const PlaceholderAvatar = () => (
    <div className="w-20 h-20 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center flex-shrink-0">
      <svg className="w-12 h-12 text-white" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
      </svg>
    </div>
  );

  return (
    <div className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
      <div className="flex flex-wrap items-start gap-4">
        {/* Photo or placeholder */}
        {rep.photo_url && !imageError ? (
          <img
            src={rep.photo_url}
            alt={rep.name}
            className="w-20 h-20 rounded-lg object-cover flex-shrink-0"
            onError={handleImageError}
          />
        ) : (
          <PlaceholderAvatar />
        )}

        {/* Basic Info - stays next to image */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="text-lg font-bold text-gray-900">{rep.name}</h3>
              <p className="text-sm text-gray-600">{rep.title}</p>
              {rep.party && (
                <span className="inline-block mt-1 px-2 py-1 text-xs font-semibold rounded bg-gray-100 text-gray-700">
                  {rep.party}
                </span>
              )}
              {rep.district && (
                <p className="text-sm text-gray-600 mt-1">District {rep.district}</p>
              )}
            </div>
            {confirmDeleteRep === rep.id ? (
              <div className="flex gap-2">
                <button
                  onClick={onConfirmRemove}
                  className="px-3 py-1 bg-red-600 text-white text-sm font-medium rounded hover:bg-red-700"
                >
                  Confirm
                </button>
                <button
                  onClick={onCancelRemove}
                  className="px-3 py-1 bg-gray-200 text-gray-700 text-sm font-medium rounded hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                onClick={() => onRemove(rep.id)}
                className="text-red-600 hover:text-red-700 text-sm font-medium whitespace-nowrap flex-shrink-0"
              >
                Remove
              </button>
            )}
          </div>
        </div>

        {/* Contact Info and Offices - wraps below on mobile, full width */}
        <div className="basis-full sm:basis-auto sm:flex-1 sm:min-w-0">
          {/* Contact Info */}
          <div className="mt-3 space-y-1 text-sm">
            {rep.contact?.phone && (
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                </svg>
                <a href={`tel:${rep.contact.phone}`} className="text-gray-700 hover:text-blue-600">{rep.contact.phone}</a>
              </div>
            )}
            {rep.contact?.email && (
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <a href={`mailto:${rep.contact.email}`} className="text-blue-600 hover:text-blue-700 truncate">
                  {rep.contact.email}
                </a>
              </div>
            )}
            {rep.contact?.website && (
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                </svg>
                <a
                  href={rep.contact.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-700 truncate"
                >
                  Visit Website
                </a>
              </div>
            )}
          </div>

          {/* Offices */}
          {rep.offices && rep.offices.length > 0 && (
            <div className="mt-4 pt-3 border-t border-gray-200">
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Offices</h4>
              <div className="space-y-2">
                {rep.offices.map((office, idx) => (
                  <div key={idx} className="text-sm text-gray-600 break-words">
                    <p className="font-medium">{office.name}</p>
                    <p className="break-words">{office.street_1}</p>
                    {office.city && office.state && (
                      <p>{office.city}, {office.state} {office.zip}</p>
                    )}
                    {office.phone && <p>Phone: <a href={`tel:${office.phone}`} className="hover:text-blue-600">{office.phone}</a></p>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function RepresentativesPage() {
  const [address, setAddress] = useState({
    street: '',
    city: '',
    state: '',
    zip_code: '',
  });
  const [lookupResult, setLookupResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [saveAddress, setSaveAddress] = useState(false);
  const [userAddresses, setUserAddresses] = useState([]);
  const [hasPrimaryAddress, setHasPrimaryAddress] = useState(false);
  const [savedReps, setSavedReps] = useState([]);
  const [loadingSavedReps, setLoadingSavedReps] = useState(true);
  const [confirmDeleteRep, setConfirmDeleteRep] = useState(null);

  // Load user's saved addresses and pre-populate if primary exists
  useEffect(() => {
    const loadUserAddresses = async () => {
      try {
        const response = await repsAPI.getUserAddresses();
        const addresses = response.data.addresses || [];
        setUserAddresses(addresses);

        // Pre-populate with primary address if exists
        const primaryAddress = addresses.find(addr => addr.is_primary);
        if (primaryAddress) {
          setAddress({
            street: primaryAddress.street_1,
            city: primaryAddress.city,
            state: primaryAddress.state,
            zip_code: primaryAddress.zip_code,
          });
          setHasPrimaryAddress(true);
        }
      } catch (err) {
        console.error('Failed to load addresses:', err);
      }
    };

    loadUserAddresses();
    loadSavedReps();
  }, []);

  const loadSavedReps = async () => {
    try {
      setLoadingSavedReps(true);
      const response = await repsAPI.getSavedRepresentatives();
      setSavedReps(response.data.representatives || []);
    } catch (err) {
      console.error('Failed to load saved representatives:', err);
    } finally {
      setLoadingSavedReps(false);
    }
  };

  const handleRemoveRep = (repId) => {
    setConfirmDeleteRep(repId);
  };

  const confirmRemoveRepAction = async () => {
    try {
      await repsAPI.removeSavedRepresentative(confirmDeleteRep);
      setConfirmDeleteRep(null);
      loadSavedReps();
      setSuccess('Representative removed successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Failed to remove representative');
      setTimeout(() => setError(''), 3000);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await repsAPI.lookupByAddress(address);
      setLookupResult(response.data);

      // Save address if checkbox is checked
      if (saveAddress) {
        try {
          await repsAPI.saveAddress({
            ...address,
            is_primary: true
          });
          setSuccess('Representatives found and address saved!');
          setTimeout(() => setSuccess(''), 3000);
        } catch (addrErr) {
          console.error('Failed to save address:', addrErr);
        }
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to lookup representatives');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setAddress({
      ...address,
      [e.target.name]: e.target.value,
    });
  };


  const handleSaveRepresentative = async (rep) => {
    try {
      const response = await repsAPI.saveRepresentative(rep);
      setSuccess(response.data.message);
      setTimeout(() => setSuccess(''), 3000);
      // Reload saved reps to update the list
      loadSavedReps();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save representative');
      setTimeout(() => setError(''), 3000);
    }
  };

  // Flatten representatives into a single array for display
  const allRepresentatives = lookupResult?.representatives ? [
    ...(lookupResult.representatives.federal?.senators || []),
    ...(lookupResult.representatives.federal?.representatives || []),
    ...(lookupResult.representatives.state?.senators || []),
    ...(lookupResult.representatives.state?.representatives || []),
  ].filter(Boolean) : [];

  // Organize saved reps
  const federalReps = savedReps.filter(rep => rep.office_type?.startsWith('federal'));
  const stateReps = savedReps.filter(rep => !rep.office_type?.startsWith('federal'));

  return (
    <div className="max-w-6xl mx-auto space-y-6 p-6">
      {success && <Toast message={success} type="success" onClose={() => setSuccess('')} />}
      {error && <Toast message={error} type="error" onClose={() => setError('')} />}

      <div>
        <h1 className="text-3xl font-bold text-gray-900">Representatives</h1>
        <p className="mt-2 text-gray-600">
          {savedReps.length > 0 ? 'Your saved representatives and tools to find more' : 'Find your state and federal representatives'}
        </p>
      </div>

      {/* Saved Representatives Section - Show first if they exist */}
      {!loadingSavedReps && savedReps.length > 0 && (
        <div className="bg-white shadow-sm rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">My Saved Representatives</h2>

          <div className="space-y-6">
            {/* Federal Representatives */}
            {federalReps.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Federal Representatives</h3>
                <div className="space-y-4">
                  {federalReps.map((rep) => (
                    <SavedRepCard
                      key={rep.id}
                      rep={rep}
                      confirmDeleteRep={confirmDeleteRep}
                      onRemove={handleRemoveRep}
                      onConfirmRemove={confirmRemoveRepAction}
                      onCancelRemove={() => setConfirmDeleteRep(null)}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* State Representatives */}
            {stateReps.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-4">State Representatives</h3>
                <div className="space-y-4">
                  {stateReps.map((rep) => (
                    <SavedRepCard
                      key={rep.id}
                      rep={rep}
                      confirmDeleteRep={confirmDeleteRep}
                      onRemove={handleRemoveRep}
                      onConfirmRemove={confirmRemoveRepAction}
                      onCancelRemove={() => setConfirmDeleteRep(null)}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Find Representatives Form */}
      <div className="bg-white shadow-sm rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          {savedReps.length > 0 ? 'Find More Representatives' : 'Find Your Representatives'}
        </h2>
        <p className="text-gray-600 mb-6">
          Enter your address to find your state and federal representatives
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="street" className="block text-sm font-medium text-gray-700 mb-1">
              Street Address
            </label>
            <input
              id="street"
              name="street"
              type="text"
              value={address.street}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="123 Main St"
              required
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label htmlFor="city" className="block text-sm font-medium text-gray-700 mb-1">
                City
              </label>
              <input
                id="city"
                name="city"
                type="text"
                value={address.city}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="McAlester"
                required
              />
            </div>

            <div>
              <label htmlFor="state" className="block text-sm font-medium text-gray-700 mb-1">
                State
              </label>
              <input
                id="state"
                name="state"
                type="text"
                value={address.state}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                maxLength={2}
                placeholder="OK"
                required
              />
            </div>
          </div>

          <div>
            <label htmlFor="zip_code" className="block text-sm font-medium text-gray-700 mb-1">
              ZIP Code
            </label>
            <input
              id="zip_code"
              name="zip_code"
              type="text"
              value={address.zip_code}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              maxLength={10}
              placeholder="74501"
              required
            />
          </div>

          <div className="flex items-center">
            <input
              id="save-address"
              type="checkbox"
              checked={saveAddress}
              onChange={(e) => setSaveAddress(e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="save-address" className="ml-2 block text-sm text-gray-700">
              Save this address to my profile
            </label>
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full px-4 py-2 text-white bg-blue-600 hover:bg-blue-700 rounded-md font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Looking up...' : 'Find Representatives'}
          </button>
        </form>
      </div>

      {lookupResult && (
        <div className="bg-white shadow-sm rounded-lg p-6">
          <div className="mb-6">
            <h2 className="text-xl font-bold text-gray-900">Your Representatives</h2>
            <p className="text-sm text-gray-600 mt-1">
              {lookupResult.address}
            </p>
            {lookupResult.cached && (
              <p className="text-xs text-gray-500 mt-1">
                Cached result from {new Date(lookupResult.cached_at).toLocaleDateString()}
              </p>
            )}
          </div>

          {/* Federal Representatives */}
          {(lookupResult.representatives.federal?.senators?.length > 0 ||
            lookupResult.representatives.federal?.representatives?.length > 0) && (
            <div className="mb-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
                Federal Representatives
              </h3>
              <div className="space-y-4">
                {lookupResult.representatives.federal.senators?.map((rep, idx) => (
                  <RepresentativeCard
                    key={`fed-senator-${idx}`}
                    rep={rep}
                    onSave={handleSaveRepresentative}
                  />
                ))}
                {lookupResult.representatives.federal.representatives?.map((rep, idx) => (
                  <RepresentativeCard
                    key={`fed-rep-${idx}`}
                    rep={rep}
                    onSave={handleSaveRepresentative}
                  />
                ))}
              </div>
            </div>
          )}

          {/* State Representatives */}
          {(lookupResult.representatives.state?.senators?.length > 0 ||
            lookupResult.representatives.state?.representatives?.length > 0) && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
                State Representatives
              </h3>
              <div className="space-y-4">
                {lookupResult.representatives.state.senators?.map((rep, idx) => (
                  <RepresentativeCard
                    key={`state-senator-${idx}`}
                    rep={rep}
                    onSave={handleSaveRepresentative}
                  />
                ))}
                {lookupResult.representatives.state.representatives?.map((rep, idx) => (
                  <RepresentativeCard
                    key={`state-rep-${idx}`}
                    rep={rep}
                    onSave={handleSaveRepresentative}
                  />
                ))}
              </div>
            </div>
          )}

          {allRepresentatives.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No representatives found for this address
            </div>
          )}
        </div>
      )}
    </div>
  );
}
