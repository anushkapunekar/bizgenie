import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, Plus, X } from 'lucide-react';
import { businessApi } from '../services/api';
import type { BusinessCreate } from '../types';

const DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];

export default function BusinessRegister() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<BusinessCreate>({
    name: '',
    description: '',
    services: [''],
    working_hours: {},
    contact_email: '',
    contact_phone: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Filter out empty services
      const services = formData.services.filter(s => s.trim() !== '');
      
      // Validate required fields
      if (!formData.name.trim()) {
        throw new Error('Business name is required');
      }
      if (services.length === 0) {
        throw new Error('At least one service is required');
      }

      const data: BusinessCreate = {
        ...formData,
        services,
        working_hours: formData.working_hours,
      };

      const business = await businessApi.register(data);
      navigate(`/business/${business.id}`);
    } catch (err: any) {
      console.error('Registration error:', err);
      
      // Handle Pydantic validation errors (array of error objects)
      let errorMessage = 'Failed to register business';
      
      if (err.response?.data) {
        const errorData = err.response.data;
        
        // If detail is an array (Pydantic validation errors)
        if (Array.isArray(errorData.detail)) {
          const errors = errorData.detail.map((e: any) => {
            const field = e.loc?.join('.') || 'field';
            return `${field}: ${e.msg}`;
          });
          errorMessage = errors.join('; ');
        } 
        // If detail is a string
        else if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail;
        }
        // If detail is an object, try to stringify it
        else if (errorData.detail && typeof errorData.detail === 'object') {
          errorMessage = JSON.stringify(errorData.detail);
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const addService = () => {
    setFormData({
      ...formData,
      services: [...formData.services, ''],
    });
  };

  const removeService = (index: number) => {
    setFormData({
      ...formData,
      services: formData.services.filter((_, i) => i !== index),
    });
  };

  const updateService = (index: number, value: string) => {
    const newServices = [...formData.services];
    newServices[index] = value;
    setFormData({ ...formData, services: newServices });
  };

  const updateWorkingHours = (day: string, field: 'open' | 'close', value: string) => {
    setFormData({
      ...formData,
      working_hours: {
        ...formData.working_hours,
        [day]: {
          ...formData.working_hours[day],
          [field]: value,
        },
      },
    });
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="card space-y-6">
        <div className="flex items-center space-x-3">
          <Building2 className="h-8 w-8 text-primary-600" />
          <h1 className="text-3xl font-bold">Register Your Business</h1>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Basic Information</h2>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Business Name *
              </label>
              <input
                type="text"
                required
                className="input"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Acme Consulting"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                className="input min-h-[100px]"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Describe your business..."
              />
            </div>
          </div>

          {/* Services */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">Services *</h2>
              <button
                type="button"
                onClick={addService}
                className="btn btn-secondary flex items-center space-x-1"
              >
                <Plus className="h-4 w-4" />
                <span>Add Service</span>
              </button>
            </div>
            
            {formData.services.map((service, index) => (
              <div key={index} className="flex items-center space-x-2">
                <input
                  type="text"
                  className="input"
                  value={service}
                  onChange={(e) => updateService(index, e.target.value)}
                  placeholder="Service name"
                />
                {formData.services.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeService(index)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                  >
                    <X className="h-5 w-5" />
                  </button>
                )}
              </div>
            ))}
          </div>

          {/* Working Hours */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Working Hours</h2>
            <div className="space-y-3">
              {DAYS.map((day) => (
                <div key={day} className="flex items-center space-x-4">
                  <div className="w-24 capitalize font-medium">{day}</div>
                  <input
                    type="time"
                    className="input flex-1"
                    value={formData.working_hours[day]?.open || ''}
                    onChange={(e) => updateWorkingHours(day, 'open', e.target.value)}
                  />
                  <span className="text-gray-500">to</span>
                  <input
                    type="time"
                    className="input flex-1"
                    value={formData.working_hours[day]?.close || ''}
                    onChange={(e) => updateWorkingHours(day, 'close', e.target.value)}
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Contact Information */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Contact Information</h2>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                type="email"
                className="input"
                value={formData.contact_email}
                onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
                placeholder="contact@example.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Phone
              </label>
              <input
                type="tel"
                className="input"
                value={formData.contact_phone}
                onChange={(e) => setFormData({ ...formData, contact_phone: e.target.value })}
                placeholder="+1234567890"
              />
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex justify-end space-x-4 pt-4">
            <button
              type="button"
              onClick={() => navigate('/')}
              className="btn btn-secondary"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? 'Registering...' : 'Register Business'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

