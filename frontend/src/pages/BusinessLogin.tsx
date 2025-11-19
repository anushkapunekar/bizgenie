import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, UserCheck, LogIn } from 'lucide-react';
import { businessApi } from '../services/api';
import type { BusinessLoginPayload } from '../types';
import { useAuth } from '../context/AuthContext';
import { getApiErrorMessage } from '../utils/errors';

type LoginMode = 'id' | 'contact';

export default function BusinessLogin() {
  const navigate = useNavigate();
  const { setActiveBusiness, savedBusinesses, refreshBusiness } = useAuth();

  const [mode, setMode] = useState<LoginMode>('id');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    businessId: '',
    contact_email: '',
    contact_phone: '',
    name: '',
  });

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    const payload: BusinessLoginPayload = {};
    if (mode === 'id' && form.businessId.trim()) {
      payload.business_id = Number(form.businessId.trim());
    } else {
      if (form.contact_email.trim()) {
        payload.contact_email = form.contact_email.trim();
      }
      if (form.contact_phone.trim()) {
        payload.contact_phone = form.contact_phone.trim();
      }
      if (form.name.trim()) {
        payload.name = form.name.trim();
      }
    }

    if (Object.keys(payload).length === 0) {
      setError('Please provide at least one piece of information.');
      return;
    }

    try {
      setLoading(true);
      const business = await businessApi.login(payload);
      setActiveBusiness(business);
      navigate(`/business/${business.id}`);
    } catch (error: unknown) {
      console.error('Login failed', error);
      setError(getApiErrorMessage(error, 'Unable to find a matching business.'));
    } finally {
      setLoading(false);
    }
  };

  const handleResume = async (businessId: number) => {
    setLoading(true);
    setError(null);
    try {
      const business = await refreshBusiness(businessId);
      if (business) {
        navigate(`/business/${business.id}`);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div className="card space-y-6">
        <div className="flex items-center space-x-3">
          <Building2 className="h-8 w-8 text-primary-600" />
          <div>
            <h1 className="text-3xl font-bold">Welcome back</h1>
            <p className="text-gray-600">Log into an existing business workspace.</p>
          </div>
        </div>

        <div className="flex space-x-3">
          <button
            type="button"
            className={`flex-1 btn ${mode === 'id' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setMode('id')}
            disabled={loading}
          >
            Use Business ID
          </button>
          <button
            type="button"
            className={`flex-1 btn ${mode === 'contact' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setMode('contact')}
            disabled={loading}
          >
            Use Email / Phone
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          {mode === 'id' ? (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Business ID</label>
              <input
                type="number"
                className="input"
                value={form.businessId}
                onChange={(e) => setForm({ ...form, businessId: e.target.value })}
                placeholder="Enter the ID shown after registration"
                required
              />
            </div>
          ) : (
            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Contact email</label>
                <input
                  type="email"
                  className="input"
                  value={form.contact_email}
                  onChange={(e) => setForm({ ...form, contact_email: e.target.value })}
                  placeholder="you@company.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Contact phone</label>
                <input
                  type="tel"
                  className="input"
                  value={form.contact_phone}
                  onChange={(e) => setForm({ ...form, contact_phone: e.target.value })}
                  placeholder="+1 555 123 4567"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Business name</label>
                <input
                  type="text"
                  className="input"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="BizGenie HQ"
                />
              </div>
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary flex items-center justify-center space-x-2 w-full"
            disabled={loading}
          >
            <LogIn className="h-4 w-4" />
            <span>{loading ? 'Checking...' : 'Log In'}</span>
          </button>
        </form>
      </div>

      {savedBusinesses.length > 0 && (
        <div className="card space-y-4">
          <div className="flex items-center space-x-2">
            <UserCheck className="h-5 w-5 text-primary-600" />
            <h2 className="text-xl font-semibold">Recent workspaces</h2>
          </div>
          <div className="grid md:grid-cols-2 gap-3">
            {savedBusinesses.map((entry) => (
              <button
                key={entry.id}
                className="border border-gray-200 rounded-xl p-4 text-left hover:border-primary-300 hover:shadow-sm transition"
                onClick={() => handleResume(entry.id)}
                disabled={loading}
              >
                <div className="font-semibold text-gray-900">{entry.name}</div>
                <div className="text-sm text-gray-500">ID: {entry.id}</div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}


