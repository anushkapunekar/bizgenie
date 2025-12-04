import { useState } from "react";
import axios from "axios";

interface Props {
  businessId: number;
  onUploaded: () => void;
  onCancel: () => void;
}

declare global {
  interface Window {
    gapi: any;
    google: any;
  }
}

export default function DocumentUpload({ businessId, onUploaded, onCancel }: Props) {
  const [loading, setLoading] = useState(false);

  const openPicker = () => {
    const developerKey = import.meta.env.VITE_GOOGLE_API_KEY;
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    const appId = developerKey; // doesn't matter for picker
    const scope = ["https://www.googleapis.com/auth/drive.readonly"];

    window.gapi.load("auth", () => {
      window.gapi.auth.authorize(
        {
          client_id: clientId,
          scope,
          immediate: false,
        },
        (authResult: any) => {
          if (authResult && !authResult.error) {
            createPicker(authResult.access_token);
          } else {
            alert("Google Drive authorization failed.");
          }
        }
      );
    });

    const createPicker = (token: string) => {
      window.gapi.load("picker", () => {
        const view = new window.google.picker.DocsView()
          .setIncludeFolders(true)
          .setSelectFolderEnabled(false)
          .setMimeTypes("application/pdf");

        const picker = new window.google.picker.PickerBuilder()
          .setAppId(appId)
          .setOAuthToken(token)
          .setDeveloperKey(developerKey)
          .addView(view)
          .setCallback((data: any) => pickerCallback(data, token))
          .build();

        picker.setVisible(true);
      });
    };
  };

  const pickerCallback = async (data: any, token: string) => {
    if (data.action === window.google.picker.Action.PICKED) {
      const file = data.docs[0]; // only single file for now
      const fileId = file.id;
      const filename = file.name;

      setLoading(true);
      try {
        // send to backend
        await axios.post(`${import.meta.env.VITE_API_URL}/google-drive/upload`, {
          business_id: businessId,
          file_id: fileId,
          filename,
          access_token: token,
        });

        onUploaded();
      } catch (err) {
        console.error(err);
        alert("Upload failed.");
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="card p-6 space-y-4">
      <h2 className="text-xl font-semibold">Upload from Google Drive</h2>

      <button
        onClick={openPicker}
        disabled={loading}
        className="btn btn-primary"
      >
        {loading ? "Uploading..." : "Choose PDF from Google Drive"}
      </button>

      <button onClick={onCancel} className="btn btn-secondary w-full">
        Cancel
      </button>
    </div>
  );
}
