import { useState, useEffect } from 'react';
import { repsAPI, authAPI } from '../services/api';
import useAuthStore from '../stores/authStore';
import Toast from '../components/Toast';
import voteRegistrationData from '../data/vote.json';

export default function ProfilePage() {
  const { user, setUser } = useAuthStore();
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [editMode, setEditMode] = useState(false);
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
  }, [user]);

  const loadAddresses = async () => {
    try {
      const response = await repsAPI.getUserAddresses();
      setAddresses(response.data.addresses || []);
    } catch (err) {
      console.error('Failed to load addresses:', err);
    }
  };

  const getVoterRegistrationUrl = (state) => {
    if (!state) return null;
    const stateCode = state.toUpperCase();
    return voteRegistrationData[stateCode] || null;
  };

  const primaryAddress = addresses.find(addr => addr.is_primary) || addresses[0];
  const voterRegUrl = primaryAddress ? getVoterRegistrationUrl(primaryAddress.state) : null;
  const isNorthDakota = primaryAddress?.state?.toUpperCase() === 'ND';

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

        {/* Voter Registration Link */}
        {isNorthDakota && (
          <div className="mb-6 p-4 bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-200 rounded-lg">
            <div className="flex flex-col gap-3">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                North Dakota Voting Information
              </h3>
              <p className="text-sm text-gray-700 leading-relaxed">
                North Dakota is the only state that does not require voter registration. The state's Voter ID law instead requires that anyone who has lived in North Dakota for at least 30 days bring a valid form of identification (e.g., ND driver's license, tribal ID, or long-term care certificate) when they vote.
              </p>
            </div>
          </div>
        )}
        {voterRegUrl && primaryAddress && !isNorthDakota && (
          <div className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-lg">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Register to Vote
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  Check your voter registration status or register to vote in {primaryAddress.state}
                </p>
              </div>
              <a
                href={voterRegUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-semibold text-center whitespace-nowrap transition-colors shadow-md hover:shadow-lg"
              >
                Register / Check Status →
              </a>
            </div>
          </div>
        )}

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
    </div>
  );
}
