import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { getBill, explainBill, Bill, BillLineItem } from "../api/bills";

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

function LineItemRow({ item }: { item: BillLineItem }) {
  return (
    <div className={`line-item-row ${item.flagged_overcharge ? "line-item-flagged" : ""}`}>
      <div className="line-item-main">
        <div className="line-item-description">
          {item.description}
          {item.flagged_overcharge && (
            <span className="flag-badge" title="Potential overcharge flagged by AI">
              ⚠️ Flagged
            </span>
          )}
        </div>
        <div className="line-item-amount">{formatCurrency(item.amount, "INR")}</div>
      </div>
      {item.explanation && (
        <div className="line-item-explanation">
          <span className="explanation-label">AI Explanation:</span>
          <span className="explanation-text">{item.explanation}</span>
        </div>
      )}
    </div>
  );
}

export function BillDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [bill, setBill] = useState<Bill | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [explaining, setExplaining] = useState(false);
  const [explainError, setExplainError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    getBill(id)
      .then(setBill)
      .catch(() => setError("Bill not found or failed to load."))
      .finally(() => setLoading(false));
  }, [id]);

  async function handleExplain() {
    if (!id) return;
    setExplainError(null);
    setExplaining(true);
    try {
      const updated = await explainBill(id);
      setBill(updated);
    } catch {
      setExplainError("Failed to get AI explanations. Please try again.");
    } finally {
      setExplaining(false);
    }
  }

  const hasExplanations = bill?.line_items?.some((li) => li.explanation);
  const flaggedCount = bill?.line_items?.filter((li) => li.flagged_overcharge).length ?? 0;

  if (loading) {
    return (
      <div className="app-layout">
        <main className="main-content centered">
          <div className="loading-state">
            <div className="spinner" aria-label="Loading bill"></div>
            <p>Loading bill details…</p>
          </div>
        </main>
      </div>
    );
  }

  if (error || !bill) {
    return (
      <div className="app-layout">
        <main className="main-content centered">
          <div className="error-banner" role="alert">{error ?? "Bill not found."}</div>
          <button className="btn btn-secondary mt-2" onClick={() => navigate("/dashboard")}>
            ← Back to Dashboard
          </button>
        </main>
      </div>
    );
  }

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <span className="logo-icon">🩺</span>
          <span className="logo-text">DecryptCare</span>
        </div>
        <nav className="sidebar-nav">
          <Link className="nav-item" to="/dashboard">📋 My Bills</Link>
        </nav>
      </aside>

      <main className="main-content">
        <header className="page-header">
          <div>
            <Link to="/dashboard" className="back-link">← My Bills</Link>
            <h1 className="page-title">Bill Details</h1>
          </div>
          {!hasExplanations && (
            <button
              className="btn btn-primary"
              onClick={handleExplain}
              disabled={explaining}
              id="explain-bill-btn"
            >
              {explaining ? "Analysing…" : "✨ Explain this bill"}
            </button>
          )}
        </header>

        {explainError && (
          <div className="error-banner mb-2" role="alert">{explainError}</div>
        )}

        {/* Summary card */}
        <div className="card bill-summary-card">
          <div className="bill-summary-row">
            <div>
              <p className="summary-label">Total Amount</p>
              <p className="summary-value large">
                {formatCurrency(bill.total_amount, bill.currency)}
              </p>
            </div>
            <div>
              <p className="summary-label">Status</p>
              <span className={`badge badge-${bill.status === "parsed" ? "green" : bill.status === "reviewed" ? "purple" : "blue"}`}>
                {bill.status}
              </span>
            </div>
            {flaggedCount > 0 && (
              <div className="flagged-summary">
                <p className="summary-label">⚠️ Potential overcharges</p>
                <p className="summary-value flagged-count">{flaggedCount} item{flaggedCount !== 1 ? "s" : ""}</p>
              </div>
            )}
          </div>
        </div>

        {/* Line items */}
        <section className="line-items-section card">
          <h2 className="section-title">Line Items</h2>
          {!bill.line_items || bill.line_items.length === 0 ? (
            <p className="empty-text">No line items extracted yet.</p>
          ) : (
            <div className="line-items-list">
              {bill.line_items.map((item) => (
                <LineItemRow key={item.id} item={item} />
              ))}
            </div>
          )}
          {!hasExplanations && bill.line_items && bill.line_items.length > 0 && (
            <p className="explain-hint">
              💡 Click "Explain this bill" to get AI-powered explanations for each line item.
            </p>
          )}
        </section>
      </main>
    </div>
  );
}
