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
  RefreshCcw,
  HardDrive
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
  const [driveFiles, setDriveFiles] = useState<any[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showUpload, setShowUpload] = useState(false);
  const [copiedLink, setCopiedLink] = useState(false);
  const [syncing, setSyncing] = useState(false);

  const businessId = id ? Number(id) : null;

  // ----------------------------
  // Load Business Profile
  // ----------------------------
  const loadBusiness = useCallback(async () => {
    if (!businessId) return;

    try {
      const data = await businessApi.get(businessId);
      setBusiness(data);
      setActiveBusiness(data);
      setError(null);
    } catch (error: unknown) {
      setError(getApiErrorMessage(error, "Failed to load business"));
    } finally {
      setLoading(false);
    }
  }, [businessId, setActiveBusiness]);

  // ----------------------------
  // Load Documents
  // ----------------------------
  const loadDocuments = useCallback(async () => {
    if (!businessId) return;
    try {
      const data = await businessApi.getDocuments(businessId);
      setDocuments(data);
    } catch (err) {
      console.error("Failed loading documents", err);
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
        description: "Upload at least one PDF so the AI can answer questions.",
      };
    }
    return {
      status: "Ready for Q&A",
      tone: "text-green-600",
      description: `Loaded ${documents.length} document${documents.length > 1 ? "s" : ""}.`,
    };
  }, [documents]);

  // ----------------------------
  // COPY CHAT LINK
  // ----------------------------
  const handleCopyLink = async () => {
    if (!chatUrl) return;
    await navigator.clipboard.writeText(chatUrl);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  // ----------------------------
  // CONNECT GOOGLE DRIVE
  // ----------------------------
  const connectGoogleDrive = async () => {
    if (!businessId) return;
    const res = await fetch(`http://localhost:8000/google/drive/connect?business_id=${businessId}`);
    const data = await res.json();
    window.location.href = data.auth_url;
  };

  // ----------------------------
  // SYNC DRIVE FILES
  // ----------------------------
  const syncDrive = async () => {
    if (!businessId) return;

    setSyncing(true);
    try {
      const res = await fetch(`http://localhost:8000/google/drive/sync?business_id=${businessId}`);
      const data = await res.json();
      setDriveFiles(data.files || []);
      await loadDocuments(); // After sync, refresh internal document list
    } catch (err) {
      console.error("Sync failed", err);
    }
    setSyncing(false);
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
        <div className="text-red-600 mb-4">{error || "Business not found"}</div>
        <Link to="/register" className="btn btn-primary">
          Register a Business
        </Link>
      </div>
    );
  }

  const DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];

  return (
    <div className="space-y-6">

      {/* HEADER */}
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

      {/* QUICK ACTIONS */}
      <div className="grid md:grid-cols-3 gap-4">
        <button
          onClick={() => setShowUpload(!showUpload)}
          className="card hover:shadow-md transition-shadow cursor-pointer text-left"
        >
          <div className="flex items-center space-x-3">
            <Upload className="h-6 w-6 text-primary-600" />
            <div>
              <h3 className="font-semibold">Upload Documents</h3>
              <p className="text-sm text-gray-600">Add PDFs for AI</p>
            </div>
          </div>
        </button>

        <button
          onClick={connectGoogleDrive}
          className="card hover:shadow-md cursor-pointer text-left"
        >
          <div className="flex items-center space-x-3">
            <HardDrive className="h-6 w-6 text-primary-600" />
            <div>
              <h3 className="font-semibold">Connect Google Drive</h3>
              <p className="text-sm text-gray-600">Sync all folder PDFs</p>
            </div>
          </div>
        </button>

        <button
          onClick={syncDrive}
          className="card hover:shadow-md cursor-pointer text-left"
        >
          <div className="flex items-center space-x-3">
            <RefreshCcw className="h-6 w-6 text-primary-600" />
            <div>
              <h3 className="font-semibold">
                {syncing ? "Syncing..." : "Sync Drive"}
              </h3>
              <p className="text-sm text-gray-600">Import PDFs into AI</p>
            </div>
          </div>
        </button>
      </div>

      {/* AI KNOWLEDGE BASE */}
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

        {driveFiles.length > 0 && (
          <div className="mt-3">
            <h3 className="font-medium">Google Drive Synced Files:</h3>
            <ul className="list-disc ml-6 text-sm text-gray-700">
              {driveFiles.map((f, i) => (
                <li key={i}>{f.name}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* DOCUMENT UPLOAD FORM */}
      {showUpload && (
        <DocumentUpload
          businessId={business.id}
          onUploaded={() => {
            loadDocuments();
            setShowUpload(false);
          }}
          onCancel={() => setShowUpload(false)}
        />
      )}

      {/* DOCUMENT LIST */}
      <div className="card">
        <div className="flex justify-between mb-3">
          <h2 className="text-xl font-semibold flex items-center space-x-2">
            <FileText className="h-5 w-5" />
            <span>Documents</span>
          </h2>

          <button
            onClick={() => setShowUpload(!showUpload)}
            className="btn btn-secondary text-sm"
          >
            {showUpload ? "Cancel" : "Upload"}
          </button>
        </div>

        {documents.length > 0 ? (
          <div className="space-y-2">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="p-3 bg-gray-50 rounded-lg flex justify-between items-center"
              >
                <div className="flex space-x-3 items-center">
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

      {/* WORKING HOURS */}
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
                className="flex items-center justify-between py-2 border-b border-gray-200 last:border-0"
              >
                <span className="capitalize font-medium">{day}</span>

                {hours?.open ? (
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
