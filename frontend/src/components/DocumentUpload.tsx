import { useState } from "react";
import { Upload, X } from "lucide-react";
import { businessApi } from "../services/api";

interface Props {
  businessId: number;
  onUploaded: () => void;
  onCancel: () => void;
}

export default function DocumentUpload({ businessId, onUploaded, onCancel }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    const f = e.target.files?.[0] || null;
    setFile(f);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a PDF file first.");
      return;
    }

    setUploading(true);
    setError(null);

    try {
      await businessApi.uploadDocument(businessId, file);
      onUploaded();
    } catch (err) {
      console.error("Upload failed:", err);
      setError("Failed to upload document. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="card p-6 space-y-4">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-lg font-semibold flex items-center space-x-2">
          <Upload className="h-5 w-5 text-primary-600" />
          <span>Upload PDF</span>
        </h2>
        <button
          type="button"
          onClick={onCancel}
          className="text-gray-500 hover:text-gray-800"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      <p className="text-sm text-gray-600">
        Add PDF documents like service menus, pricing, FAQs, or policies. The AI
        will use them to answer customer questions.
      </p>

      {error && (
        <div className="text-sm text-red-600 bg-red-50 border border-red-200 px-3 py-2 rounded-lg">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Choose PDF
          </label>
          <input
            type="file"
            accept="application/pdf"
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-900 file:mr-4 file:py-2 file:px-4 
                       file:rounded-md file:border-0 file:text-sm file:font-semibold 
                       file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
          />
          {file && (
            <p className="text-xs text-gray-500 mt-1">Selected: {file.name}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={uploading || !file}
          className="btn btn-primary w-full disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {uploading ? "Uploading..." : "Upload document"}
        </button>
      </form>
    </div>
  );
}
