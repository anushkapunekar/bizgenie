import { useState } from "react";
import { X } from "lucide-react";
import { appointmentsApi } from "../services/api";

interface BookingModalProps {
  open: boolean;
  onClose: () => void;
  business: { id: number; name: string };
  profile: { name: string; email?: string };
  onSuccess: (appointment: any) => void;
}

export default function BookingModal({
  open,
  onClose,
  business,
  profile,
  onSuccess,
}: BookingModalProps) {
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [loading, setLoading] = useState(false);

  if (!open) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!date || !time) return;

    setLoading(true);

    try {
      const appt = await appointmentsApi.create({
        business_id: business.id,
        customer_name: profile.name,
        customer_email: profile.email || null,
        date,
        time,
      });

      onSuccess(appt);
      onClose();
    } catch (err) {
      console.error("Booking error:", err);
      alert("Failed to book appointment. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white w-full max-w-md rounded-xl shadow-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">
            Book an appointment at {business.name}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-500 hover:text-gray-800"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700">
              Select date
            </label>
            <input
              type="date"
              className="input mt-1 w-full"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700">
              Select time
            </label>
            <input
              type="time"
              className="input mt-1 w-full"
              value={time}
              onChange={(e) => setTime(e.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary w-full"
            disabled={loading}
          >
            {loading ? "Booking..." : "Confirm Appointment"}
          </button>
        </form>
      </div>
    </div>
  );
}
