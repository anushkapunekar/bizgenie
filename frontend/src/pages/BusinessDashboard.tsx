import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  MessageSquare,
  Upload,
  FileText,
  Building2,
  Mail,
  Phone,
  Clock,
  Link2,
  Copy,
  CheckCircle,
} from "lucide-react";

import { businessApi } from "../services/api";
import type { Business, Document } from "../types";
import DocumentUpload from "../components/DocumentUpload";
import { useAuth } from "../context/AuthContext";
import { getApiErrorMessage } from "../utils/errors";

export default function BusinessDashboard() {
  const { id } = useParams<{ id: string }>();
  const { setActiveBusiness } = useAuth();

  const [business, setBusiness] = useState<Business | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showUpload, setShowUpload] = useState(false);
  const [copiedLink, setCopiedLink] = useState(false);

  const businessId = id ? Number(id) : null;

  const loadBusiness = useCallback(async () => {
    if (!businessId) return;
    try {
      const data = await businessApi.get(businessId);
      setBusiness(data);
      setActiveBusiness(data);
      setError(null);
    } catch (err: unknown) {
      console.error("Load business error:", err);
      setError(getApiErrorMessage(err, "Failed to load business"));
    } finally {
      setLoading(false);
    }
  }, [businessId, setActiveBusiness]);

  const loadDocuments = useCallback(async () => {
    if (!businessId) return;
    try {
      const data = await businessApi.getDocuments(businessId);
      setDocuments(data);
    } catch (err) {
      console.error("Failed to load documents:", err);
    }
  }, [businessId]);

  useEffect(() => {
    loadBusiness();
    loadDocuments();
  }, [loadBusiness, loadDocuments]);

  const chatUrl = useMemo(() => {
    if (!business) return "";
    return `${window.location.origin}/business/${business.id}/chat`;
  }, [business]);

  const knowledgeStatus = useMemo(() => {
    if (!documents.length) {
      return {
        status: "Needs content",
        tone: "text-red-600",
        description:
          "Upload at least one PDF so the AI can answer company-specific questions.",
      };
    }
    return {
      status: "Ready for Q&A",
      tone: "text-green-600",
      description: `Loaded ${documents.length} document${
        documents.length > 1 ? "s" : ""
      } into the knowledge base.`,
    };
  }, [documents.length]);

  const handleCopyLink = async () => {
    if (!chatUrl) return;
    try {
      await navigator.clipboard.writeText(chatUrl);
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2000);
    } catch (error) {
      console.error("Copy failed", error);
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
      <div className="card text-center max-w-xl mx-auto">
        <div className="text-red-600 mb-4">{error || "Business not found"}</div>
        <Link to="/register" className="btn btn-primary">
          Register a Business
        </Link>
      </div>
    );
  }

  const DAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto px-4 pb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center space-x-3">
            <Building2 className="h-8 w-8 text-primary-600" />
            <span>{business.name}</span>
          </h1>
          {business.description && (
            <p className="text-gray-600 mt-2 max-w-2xl">{business.description}</p>
          )}
        </div>
        <Link
          to={`/business/${id}/chat`}
          className="btn btn-primary flex items-center justify-center space-x-2 w-full md:w-auto"
        >
          <MessageSquare className="h-5 w-5" />
          <span>Start Chat</span>
        </Link>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
              <p className="text-sm text-gray-600">
                Add PDFs for AI Q&amp;A (menus, FAQs, policies)
              </p>
            </div>
          </div>
        </button>

        <div className="card hover:shadow-md transition-shadow">
          <div className="flex items-center space-x-3">
            <div className="bg-primary-100 p-3 rounded-lg">
              <MessageSquare className="h-6 w-6 text-primary-600" />
            </div>
            <div>
              <h3 className="font-semibold">Share Chat Link</h3>
              <p className="text-sm text-gray-600">
                Share with staff or embed in your site.
              </p>
            </div>
          </div>
          <div className="mt-3 flex flex-col sm:flex-row sm:items-center gap-2">
            <input
              type="text"
              readOnly
              className="input flex-1 text-xs sm:text-sm"
              value={chatUrl}
            />
            <button
              onClick={handleCopyLink}
              className="btn btn-secondary text-sm flex items-center justify-center space-x-1"
            >
              <Copy className="h-4 w-4" />
              <span>{copiedLink ? "Copied" : "Copy"}</span>
            </button>
          </div>
        </div>
      </div>

      {/* AI Knowledge Base */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card space-y-3">
          <div className="flex items-center space-x-2">
            <CheckCircle className="h-5 w-5 text-primary-600" />
            <h2 className="text-xl font-semibold">AI Knowledge Base</h2>
          </div>
          <div className={`text-lg font-semibold ${knowledgeStatus.tone}`}>
            {knowledgeStatus.status}
          </div>
          <p className="text-gray-600">{knowledgeStatus.description}</p>
          <div className="text-sm text-gray-500">
            Last sync: {new Date().toLocaleString()}
          </div>
        </div>

        {/* Contact Info */}
        <div className="card space-y-3">
          <h2 className="text-xl font-semibold mb-2">Contact Information</h2>
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
              <p className="text-gray-500 text-sm">No contact information set.</p>
            )}
          </div>
        </div>
      </div>

      {/* Upload Form */}
      {showUpload && (
        <DocumentUpload
          businessId={business.id}
          onUploaded={handleDocumentUploaded}
          onCancel={() => setShowUpload(false)}
        />
      )}

      {/* Documents */}
      <div className="card">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <h2 className="text-xl font-semibold flex items-center space-x-2">
            <FileText className="h-5 w-5" />
            <span>Documents</span>
          </h2>
          <button
            onClick={() => setShowUpload(!showUpload)}
            className="btn btn-secondary text-sm w-full sm:w-auto"
          >
            {showUpload ? "Cancel" : "Upload"}
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
                  <span className="font-medium break-all">{doc.filename}</span>
                </div>
                <span className="text-sm text-gray-500">
                  {new Date(doc.created_at).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-sm">
            No documents uploaded yet. Start by adding your menu, services, or FAQ
            PDFs.
          </p>
        )}
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
              <div
                key={day}
                className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0"
              >
                <span className="capitalize font-medium">{day}</span>
                {hours?.open && hours?.close ? (
                  <span className="text-gray-700">
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
    </div>
  );
}
