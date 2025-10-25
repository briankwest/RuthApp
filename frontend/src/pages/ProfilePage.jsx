import { useState, useEffect } from 'react';
import { repsAPI, authAPI } from '../services/api';
import useAuthStore from '../stores/authStore';
import Toast from '../components/Toast';

export default function ProfilePage() {
  const { user, setUser } = useAuthStore();
  const [addresses, setAddresses] = useState([]);
  const [savedReps, setSavedReps] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [editMode, setEditMode] = useState(false);
  const [confirmDeleteRep, setConfirmDeleteRep] = useState(null); // Track which rep to delete
  const [confirmDeleteAddress, setConfirmDeleteAddress] = useState(null); // Track which address to delete

  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
  });

  const [newAddress, setNewAddress] = useState({
    street: '',
    street_2: '',
    city: '',
    state: '',
    zip_code: '',
    is_primary: false,
  });

  useEffect(() => {
    if (user) {
      setFormData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        phone: user.phone || '',
      });
    }
    loadAddresses();
    loadSavedReps();
  }, [user]);

  const loadAddresses = async () => {
    try {
      const response = await repsAPI.getUserAddresses();
      setAddresses(response.data.addresses || []);
    } catch (err) {
      console.error('Failed to load addresses:', err);
    }
  };

  const loadSavedReps = async () => {
    try {
      const response = await repsAPI.getSavedRepresentatives();
      setSavedReps(response.data.representatives || []);
    } catch (err) {
      console.error('Failed to load saved representatives:', err);
    }
  };

  const handleDeleteAddress = async (addressId) => {
    setConfirmDeleteAddress(addressId);
  };

  const confirmDeleteAddressAction = async () => {
    try {
      await repsAPI.deleteAddress(confirmDeleteAddress);
      setSuccess('Address deleted successfully!');
      setTimeout(() => setSuccess(''), 3000);
      loadAddresses();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete address');
      setTimeout(() => setError(''), 3000);
    } finally {
      setConfirmDeleteAddress(null);
    }
  };

  const handleRemoveRep = async (repId) => {
    setConfirmDeleteRep(repId);
  };

  const confirmRemoveRepAction = async () => {
    try {
      await repsAPI.removeSavedRepresentative(confirmDeleteRep);
      setSuccess('Representative removed successfully!');
      setTimeout(() => setSuccess(''), 3000);
      loadSavedReps();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to remove representative');
      setTimeout(() => setError(''), 3000);
    } finally {
      setConfirmDeleteRep(null);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleAddressChange = (e) => {
    setNewAddress({
      ...newAddress,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await authAPI.updateProfile(formData);
      setUser(response.data);
      setSuccess('Profile updated successfully!');
      setTimeout(() => setSuccess(''), 3000);
      setEditMode(false);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const handleAddAddress = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await repsAPI.saveAddress(newAddress);
      setSuccess('Address saved successfully!');
      setTimeout(() => setSuccess(''), 3000);
      setNewAddress({
        street: '',
        street_2: '',
        city: '',
        state: '',
        zip_code: '',
        is_primary: false,
      });
      loadAddresses();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save address');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {success && <Toast message={success} type="success" onClose={() => setSuccess('')} />}
      {error && <Toast message={error} type="error" onClose={() => setError('')} />}

      <div>
        <h1 className="text-3xl font-bold text-gray-900">My Profile</h1>
        <p className="mt-2 text-gray-600">
          Manage your personal information and addresses
        </p>
      </div>


      {/* Personal Information */}
      <div className="bg-white shadow-sm rounded-lg p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Personal Information</h2>
          <button
            onClick={() => setEditMode(!editMode)}
            className="text-sm text-blue-600 hover:text-blue-700"
          >
            {editMode ? 'Cancel' : 'Edit'}
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="first_name" className="block text-sm font-medium text-gray-700 mb-1">
                First Name
              </label>
              <input
                id="first_name"
                name="first_name"
                type="text"
                value={formData.first_name}
                onChange={handleChange}
                disabled={!editMode}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                required
              />
            </div>

            <div>
              <label htmlFor="last_name" className="block text-sm font-medium text-gray-700 mb-1">
                Last Name
              </label>
              <input
                id="last_name"
                name="last_name"
                type="text"
                value={formData.last_name}
                onChange={handleChange}
                disabled={!editMode}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                required
              />
            </div>
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              disabled={!editMode}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              required
            />
          </div>

          <div>
            <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
              Phone
            </label>
            <input
              id="phone"
              name="phone"
              type="tel"
              value={formData.phone}
              onChange={handleChange}
              disabled={!editMode}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
            />
          </div>

          {editMode && (
            <button
              type="submit"
              disabled={loading}
              className="w-full px-4 py-2 text-white bg-blue-600 hover:bg-blue-700 rounded-md font-medium disabled:opacity-50"
            >
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
          )}
        </form>
      </div>

      {/* Saved Addresses */}
      <div className="bg-white shadow-sm rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">My Addresses</h2>

        {addresses.length > 0 && (
          <div className="space-y-3 mb-6">
            {addresses.map((addr) => (
              <div
                key={addr.id}
                className={`p-4 rounded-md border ${
                  addr.is_primary
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    {addr.is_primary && (
                      <span className="inline-block px-2 py-1 text-xs font-semibold text-blue-700 bg-blue-100 rounded mb-2">
                        Primary
                      </span>
                    )}
                    <p className="font-medium text-gray-900">{addr.street_1}</p>
                    {addr.street_2 && (
                      <p className="text-gray-600">{addr.street_2}</p>
                    )}
                    <p className="text-gray-600">
                      {addr.city}, {addr.state} {addr.zip_code}
                    </p>
                  </div>
                  <button
                    onClick={() => handleDeleteAddress(addr.id)}
                    className="text-red-600 hover:text-red-700 text-sm font-medium"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Add New Address Form */}
        <div className="border-t border-gray-200 pt-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Address</h3>
          <form onSubmit={handleAddAddress} className="space-y-4">
            <div>
              <label htmlFor="street" className="block text-sm font-medium text-gray-700 mb-1">
                Street Address
              </label>
              <input
                id="street"
                name="street"
                type="text"
                value={newAddress.street}
                onChange={handleAddressChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="123 Main St"
                required
              />
            </div>

            <div>
              <label htmlFor="street_2" className="block text-sm font-medium text-gray-700 mb-1">
                Apt/Suite (Optional)
              </label>
              <input
                id="street_2"
                name="street_2"
                type="text"
                value={newAddress.street_2}
                onChange={handleAddressChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Apt 4B"
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
                  value={newAddress.city}
                  onChange={handleAddressChange}
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
                  value={newAddress.state}
                  onChange={handleAddressChange}
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
                value={newAddress.zip_code}
                onChange={handleAddressChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                maxLength={10}
                placeholder="74501"
                required
              />
            </div>

            <div className="flex items-center">
              <input
                id="is_primary"
                name="is_primary"
                type="checkbox"
                checked={newAddress.is_primary}
                onChange={(e) => setNewAddress({ ...newAddress, is_primary: e.target.checked })}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="is_primary" className="ml-2 block text-sm text-gray-700">
                Set as primary address
              </label>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full px-4 py-2 text-white bg-blue-600 hover:bg-blue-700 rounded-md font-medium disabled:opacity-50"
            >
              {loading ? 'Saving...' : 'Add Address'}
            </button>
          </form>
        </div>
      </div>

      {/* Saved Representatives */}
      <div className="bg-white shadow-sm rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">My Saved Representatives</h2>

        {savedReps.length === 0 ? (
          <p className="text-gray-600 text-center py-8">
            No saved representatives yet. Visit the Representatives page to find and save your representatives.
          </p>
        ) : (
          <div className="space-y-6">
            {/* Federal Representatives */}
            {(() => {
              const federalReps = savedReps.filter(rep => rep.office_type?.startsWith('federal'));
              return federalReps.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-4">Federal Representatives</h3>
                  <div className="space-y-4">
                    {federalReps.map((rep) => (
                      <div
                        key={rep.id}
                        className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start gap-4">
                          {/* Photo or placeholder */}
                          {rep.photo_url ? (
                            <img
                              src={rep.photo_url}
                              alt={rep.name}
                              className="w-20 h-20 rounded-lg object-cover flex-shrink-0"
                              onError={(e) => {
                                e.target.style.display = 'none';
                                e.target.nextSibling.style.display = 'flex';
                              }}
                            />
                          ) : null}
                          <div
                            className="w-20 h-20 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center flex-shrink-0"
                            style={{ display: rep.photo_url ? 'none' : 'flex' }}
                          >
                            <svg className="w-12 h-12 text-white" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                            </svg>
                          </div>

                          {/* Info */}
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
                                    onClick={confirmRemoveRepAction}
                                    className="px-3 py-1 bg-red-600 text-white text-sm font-medium rounded hover:bg-red-700"
                                  >
                                    Confirm
                                  </button>
                                  <button
                                    onClick={() => setConfirmDeleteRep(null)}
                                    className="px-3 py-1 bg-gray-200 text-gray-700 text-sm font-medium rounded hover:bg-gray-300"
                                  >
                                    Cancel
                                  </button>
                                </div>
                              ) : (
                                <button
                                  onClick={() => handleRemoveRep(rep.id)}
                                  className="text-red-600 hover:text-red-700 text-sm font-medium whitespace-nowrap"
                                >
                                  Remove
                                </button>
                              )}
                            </div>

                            {/* Contact Info */}
                            <div className="mt-3 space-y-1 text-sm">
                              {rep.contact?.phone && (
                                <div className="flex items-center gap-2">
                                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                                  </svg>
                                  <span className="text-gray-700">{rep.contact.phone}</span>
                                </div>
                              )}
                              {rep.contact?.fax && (
                                <div className="flex items-center gap-2">
                                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                                  </svg>
                                  <span className="text-gray-700">Fax: {rep.contact.fax}</span>
                                </div>
                              )}
                              {rep.contact?.email && (
                                <div className="flex items-center gap-2">
                                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                  </svg>
                                  <a href={`mailto:${rep.contact.email}`} className="text-blue-600 hover:text-blue-700">
                                    {rep.contact.email}
                                  </a>
                                </div>
                              )}
                              {rep.contact?.website && (
                                <div className="flex items-center gap-2">
                                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                                    <div key={idx} className="text-sm text-gray-600">
                                      <p className="font-medium">{office.name}</p>
                                      <p>{office.street_1}</p>
                                      {office.city && office.state && (
                                        <p>{office.city}, {office.state} {office.zip}</p>
                                      )}
                                      {office.phone && <p>Phone: {office.phone}</p>}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })()}

            {/* State Representatives */}
            {(() => {
              const stateReps = savedReps.filter(rep => !rep.office_type?.startsWith('federal'));
              return stateReps.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-4">State Representatives</h3>
                  <div className="space-y-4">
                    {stateReps.map((rep) => (
                      <div
                        key={rep.id}
                        className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
                      >
                <div className="flex items-start gap-4">
                  {/* Photo or placeholder */}
                  {rep.photo_url ? (
                    <img
                      src={rep.photo_url}
                      alt={rep.name}
                      className="w-20 h-20 rounded-lg object-cover flex-shrink-0"
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.nextSibling.style.display = 'flex';
                      }}
                    />
                  ) : null}
                  <div
                    className="w-20 h-20 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center flex-shrink-0"
                    style={{ display: rep.photo_url ? 'none' : 'flex' }}
                  >
                    <svg className="w-12 h-12 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                    </svg>
                  </div>

                  {/* Info */}
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
                            onClick={confirmRemoveRepAction}
                            className="px-3 py-1 bg-red-600 text-white text-sm font-medium rounded hover:bg-red-700"
                          >
                            Confirm
                          </button>
                          <button
                            onClick={() => setConfirmDeleteRep(null)}
                            className="px-3 py-1 bg-gray-200 text-gray-700 text-sm font-medium rounded hover:bg-gray-300"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => handleRemoveRep(rep.id)}
                          className="text-red-600 hover:text-red-700 text-sm font-medium whitespace-nowrap"
                        >
                          Remove
                        </button>
                      )}
                    </div>

                    {/* Contact Info */}
                    <div className="mt-3 space-y-1 text-sm">
                      {rep.contact?.phone && (
                        <div className="flex items-center gap-2">
                          <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                          </svg>
                          <span className="text-gray-700">{rep.contact.phone}</span>
                        </div>
                      )}
                      {rep.contact?.fax && (
                        <div className="flex items-center gap-2">
                          <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                          </svg>
                          <span className="text-gray-700">Fax: {rep.contact.fax}</span>
                        </div>
                      )}
                      {rep.contact?.email && (
                        <div className="flex items-center gap-2">
                          <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                          </svg>
                          <a href={`mailto:${rep.contact.email}`} className="text-blue-600 hover:text-blue-700">
                            {rep.contact.email}
                          </a>
                        </div>
                      )}
                      {rep.contact?.website && (
                        <div className="flex items-center gap-2">
                          <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                            <div key={idx} className="text-sm text-gray-600">
                              <p className="font-medium">{office.name}</p>
                              <p>{office.street_1}</p>
                              {office.city && office.state && (
                                <p>{office.city}, {office.state} {office.zip}</p>
                              )}
                              {office.phone && <p>Phone: {office.phone}</p>}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    })()}
  </div>
)}
      </div>
    </div>
  );
}
