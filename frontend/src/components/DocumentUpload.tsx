import { useState } from 'react';
import { Upload, X, FileText, Loader2 } from 'lucide-react';
import { businessApi } from '../services/api';
import { getApiErrorMessage } from '../utils/errors';

interface DocumentUploadProps {
  businessId: number;
  onUploaded: () => void;
  onCancel: () => void;
}

export default function DocumentUpload({ businessId, onUploaded, onCancel }: DocumentUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (selectedFile.type !== 'application/pdf') {
        setError('Only PDF files are supported');
        return;
      }
      if (selectedFile.size > 10 * 1024 * 1024) {
        setError('File size must be less than 10MB');
        return;
      }
      setFile(selectedFile);
      setError(null);
      setSuccess(false);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);
    setSuccess(false);

    try {
      await businessApi.uploadDocument(businessId, file);
      setUploadedFileName(file.name);
      setFile(null);
      setSuccess(true);
      
      // Wait a moment to show success message, then refresh and hide
      setTimeout(() => {
        onUploaded();
      }, 1500);
    } catch (error: unknown) {
      console.error('Upload error:', error);
      setError(getApiErrorMessage(error, 'Failed to upload document. Please try again.'));
      setSuccess(false);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="card space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center space-x-2">
          <Upload className="h-5 w-5" />
          <span>Upload Document</span>
        </h3>
        <button
          onClick={onCancel}
          className="text-gray-400 hover:text-gray-600"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg">
          ✓ Document "{uploadedFileName}" uploaded successfully! It will be processed and available for AI queries shortly.
        </div>
      )}

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select PDF File
          </label>
          <div className="flex items-center space-x-4">
            <label className="flex-1 cursor-pointer">
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                className="hidden"
                disabled={uploading}
              />
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-primary-500 transition-colors">
                {file ? (
                  <div className="flex items-center justify-center space-x-2">
                    <FileText className="h-6 w-6 text-primary-600" />
                    <span className="font-medium">{file.name}</span>
                  </div>
                ) : (
                  <div>
                    <Upload className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                    <p className="text-sm text-gray-600">Click to select PDF file</p>
                    <p className="text-xs text-gray-500 mt-1">Max size: 10MB</p>
                  </div>
                )}
              </div>
            </label>
          </div>
        </div>

        {file && (
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-2">
              <FileText className="h-5 w-5 text-gray-400" />
              <span className="text-sm">{file.name}</span>
              <span className="text-xs text-gray-500">
                ({(file.size / 1024 / 1024).toFixed(2)} MB)
              </span>
            </div>
            <button
              onClick={() => setFile(null)}
              className="text-gray-400 hover:text-gray-600"
              disabled={uploading}
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        )}

        <div className="flex justify-end space-x-2">
          <button
            onClick={onCancel}
            className="btn btn-secondary"
            disabled={uploading || success}
          >
            {success ? 'Close' : 'Cancel'}
          </button>
          {!success && (
            <button
              onClick={handleUpload}
              className="btn btn-primary flex items-center space-x-2"
              disabled={!file || uploading}
            >
              {uploading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Uploading...</span>
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4" />
                  <span>Upload</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

