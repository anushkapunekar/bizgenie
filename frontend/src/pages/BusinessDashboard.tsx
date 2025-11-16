import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { MessageSquare, Upload, FileText, Building2, Mail, Phone, Clock } from 'lucide-react';
import { businessApi } from '../services/api';
import type { Business, Document } from '../types';
import DocumentUpload from '../components/DocumentUpload';

export default function BusinessDashboard() {
  const { id } = useParams<{ id: string }>();
  const [business, setBusiness] = useState<Business | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showUpload, setShowUpload] = useState(false);

  useEffect(() => {
    if (id) {
      loadBusiness();
      loadDocuments();
    }
  }, [id]);

  const loadBusiness = async () => {
    try {
      const data = await businessApi.get(Number(id));
      setBusiness(data);
    } catch (err: any) {
      console.error('Load business error:', err);
      
      // Handle Pydantic validation errors
      let errorMsg = 'Failed to load business';
      if (err.response?.data) {
        const errorData = err.response.data;
        if (Array.isArray(errorData.detail)) {
          errorMsg = errorData.detail.map((e: any) => e.msg).join('; ');
        } else if (typeof errorData.detail === 'string') {
          errorMsg = errorData.detail;
        }
      }
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const loadDocuments = async () => {
    if (!id) return;
    try {
      const data = await businessApi.getDocuments(Number(id));
      console.log('Documents loaded:', data);
      setDocuments(data);
    } catch (err: any) {
      console.error('Failed to load documents:', err);
      console.error('Error details:', err.response?.data);
    }
  };

  const handleDocumentUploaded = () => {
    loadDocuments();
    setShowUpload(false);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="text-gray-600">Loading...</div>
      </div>
    );
  }

  if (error || !business) {
    return (
      <div className="card text-center">
        <div className="text-red-600 mb-4">{error || 'Business not found'}</div>
        <Link to="/register" className="btn btn-primary">
          Register a Business
        </Link>
      </div>
    );
  }

  const DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center space-x-3">
            <Building2 className="h-8 w-8 text-primary-600" />
            <span>{business.name}</span>
          </h1>
          {business.description && (
            <p className="text-gray-600 mt-2">{business.description}</p>
          )}
        </div>
        <Link
          to={`/business/${id}/chat`}
          className="btn btn-primary flex items-center space-x-2"
        >
          <MessageSquare className="h-5 w-5" />
          <span>Start Chat</span>
        </Link>
      </div>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-2 gap-4">
        <button
          onClick={() => setShowUpload(!showUpload)}
          className="card hover:shadow-md transition-shadow cursor-pointer text-left"
        >
          <div className="flex items-center space-x-3">
            <div className="bg-primary-100 p-3 rounded-lg">
              <Upload className="h-6 w-6 text-primary-600" />
            </div>
            <div>
              <h3 className="font-semibold">Upload Documents</h3>
              <p className="text-sm text-gray-600">Add PDFs for AI Q&A</p>
            </div>
          </div>
        </button>

        <Link
          to={`/business/${id}/chat`}
          className="card hover:shadow-md transition-shadow text-left"
        >
          <div className="flex items-center space-x-3">
            <div className="bg-primary-100 p-3 rounded-lg">
              <MessageSquare className="h-6 w-6 text-primary-600" />
            </div>
            <div>
              <h3 className="font-semibold">Chat with AI</h3>
              <p className="text-sm text-gray-600">Test your AI assistant</p>
            </div>
          </div>
        </Link>
      </div>

      {/* Document Upload Form */}
      {showUpload && (
        <DocumentUpload
          businessId={Number(id)}
          onUploaded={handleDocumentUploaded}
          onCancel={() => setShowUpload(false)}
        />
      )}

      {/* Business Details */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Services */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Services</h2>
          {business.services.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {business.services.map((service, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm"
                >
                  {service}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-gray-500">No services listed</p>
          )}
        </div>

        {/* Contact Information */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Contact Information</h2>
          <div className="space-y-2">
            {business.contact_email && (
              <div className="flex items-center space-x-2 text-gray-700">
                <Mail className="h-4 w-4" />
                <span>{business.contact_email}</span>
              </div>
            )}
            {business.contact_phone && (
              <div className="flex items-center space-x-2 text-gray-700">
                <Phone className="h-4 w-4" />
                <span>{business.contact_phone}</span>
              </div>
            )}
            {!business.contact_email && !business.contact_phone && (
              <p className="text-gray-500">No contact information</p>
            )}
          </div>
        </div>
      </div>

      {/* Working Hours */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4 flex items-center space-x-2">
          <Clock className="h-5 w-5" />
          <span>Working Hours</span>
        </h2>
        <div className="space-y-2">
          {DAYS.map((day) => {
            const hours = business.working_hours[day];
            return (
              <div key={day} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                <span className="capitalize font-medium">{day}</span>
                {hours?.open && hours?.close ? (
                  <span className="text-gray-600">
                    {hours.open} - {hours.close}
                  </span>
                ) : (
                  <span className="text-gray-400">Closed</span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Documents */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold flex items-center space-x-2">
            <FileText className="h-5 w-5" />
            <span>Documents</span>
          </h2>
          <button
            onClick={() => setShowUpload(!showUpload)}
            className="btn btn-secondary text-sm"
          >
            {showUpload ? 'Cancel' : 'Upload'}
          </button>
        </div>
        {documents.length > 0 ? (
          <div className="space-y-2">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  <FileText className="h-5 w-5 text-gray-400" />
                  <span className="font-medium">{doc.filename}</span>
                </div>
                <span className="text-sm text-gray-500">
                  {new Date(doc.created_at).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">No documents uploaded yet</p>
        )}
      </div>
    </div>
  );
}

