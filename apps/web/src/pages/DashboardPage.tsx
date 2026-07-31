import { useState, useEffect, useRef, FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getBills, uploadBill, Bill } from "../api/bills";
import { useAuth } from "../context/AuthContext";

function StatusBadge({ status }: { status: Bill["status"] }) {
  const classes: Record<string, string> = {
    uploaded: "badge badge-blue",
    parsed: "badge badge-green",
    reviewed: "badge badge-purple",
  };
  return <span className={classes[status] ?? "badge"}>{status}</span>;
}

function formatCurrency(amount: number, currency: string) {
  try {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: currency || "INR",
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    return `${currency ?? "INR"} ${amount.toFixed(2)}`;
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-IN", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function DashboardPage() {
  const [bills, setBills] = useState<Bill[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { logout } = useAuth();
  const navigate = useNavigate();

  async function fetchBills() {
    setLoading(true);
    setError(null);
    try {
      const data = await getBills();
      setBills(data);
    } catch {
      setError("Failed to load bills. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchBills();
  }, []);

  async function handleUpload(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const file = fileInputRef.current?.files?.[0];
    if (!file) return;
    setUploadError(null);
    setUploading(true);
    try {
      await uploadBill(file);
      if (fileInputRef.current) fileInputRef.current.value = "";
      await fetchBills();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Upload failed. Please check your file and try again.";
      setUploadError(msg);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <span className="logo-icon">🩺</span>
          <span className="logo-text">DecryptCare</span>
        </div>
        <nav className="sidebar-nav">
          <a className="nav-item active" href="/dashboard">📋 My Bills</a>
        </nav>
        <div className="sidebar-footer">
          <button className="btn btn-ghost" onClick={() => { logout(); navigate("/login"); }}>
            Sign out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="main-content">
        <header className="page-header">
          <div>
            <h1 className="page-title">My Bills</h1>
            <p className="page-subtitle">Upload and review your medical bills</p>
          </div>
        </header>

        {/* Upload form */}
        <section className="upload-section card">
          <h2 className="section-title">Upload a Bill</h2>
          <p className="section-desc">
            Supports PDF, JPEG, and PNG files (max 10 MB). We'll extract
            line items automatically using OCR.
          </p>
          <form onSubmit={handleUpload} className="upload-form">
            <label className="file-input-label" htmlFor="bill-file-input">
              <span className="file-input-icon">📎</span>
              <span>Choose file</span>
              <input
                id="bill-file-input"
                type="file"
                accept=".pdf,.jpg,.jpeg,.png"
                ref={fileInputRef}
                required
                disabled={uploading}
              />
            </label>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={uploading}
            >
              {uploading ? "Uploading…" : "Upload & Parse"}
            </button>
          </form>
          {uploadError && (
            <div className="error-banner mt-2" role="alert">{uploadError}</div>
          )}
        </section>

        {/* Bills list */}
        <section className="bills-section">
          {loading ? (
            <div className="loading-state">
              <div className="spinner" aria-label="Loading bills"></div>
              <p>Loading your bills…</p>
            </div>
          ) : error ? (
            <div className="error-banner" role="alert">{error}</div>
          ) : bills.length === 0 ? (
            <div className="empty-state card">
              <p className="empty-icon">📄</p>
              <p className="empty-text">No bills yet. Upload your first medical bill above.</p>
            </div>
          ) : (
            <div className="bills-grid">
              {bills.map((bill) => (
                <Link
                  to={`/bills/${bill.id}`}
                  key={bill.id}
                  className="bill-card card"
                >
                  <div className="bill-card-header">
                    <StatusBadge status={bill.status} />
                    <span className="bill-date">{formatDate(bill.created_at)}</span>
                  </div>
                  <div className="bill-amount">
                    {formatCurrency(bill.total_amount, bill.currency)}
                  </div>
                  <div className="bill-footer">
                    <span className="bill-items-count">
                      {bill.line_items?.length ?? 0} line items
                    </span>
                    <span className="bill-view-link">View details →</span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </section>
      </main>

      {/* Health status footer */}
      <HealthFooter />
    </div>
  );
}

function HealthFooter() {
  const [status, setStatus] = useState<string>("checking…");
  useEffect(() => {
    const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
    fetch(`${apiUrl}/health`)
      .then((r) => r.json())
      .then((d) => setStatus(d.status === "ok" ? "🟢 API healthy" : "🟡 " + d.status))
      .catch(() => setStatus("🔴 API unreachable"));
  }, []);
  return (
    <footer className="health-footer">
      <span>Backend: <strong>{status}</strong></span>
    </footer>
  );
}
