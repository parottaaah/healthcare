import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '../context/AuthContext'
import { BillDetailPage } from '../pages/BillDetailPage'
import * as billsApi from '../api/bills'
import { Bill } from '../api/bills'

vi.mock('../api/bills')

function renderBillDetail(billId: string, token = 'mock-token') {
  localStorage.setItem('token', token)
  return render(
    <MemoryRouter initialEntries={[`/bills/${billId}`]}>
      <AuthProvider>
        <Routes>
          <Route path="/bills/:id" element={<BillDetailPage />} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  )
}

const billWithFlaggedItem: Bill = {
  id: 'bill-abc',
  user_id: 'user-1',
  raw_file_url: 'uploads/bill.jpg',
  total_amount: 2200.0,
  currency: 'INR',
  status: 'parsed',
  created_at: '2024-02-01T09:00:00Z',
  updated_at: '2024-02-01T09:01:00Z',
  line_items: [
    {
      id: 'li-normal',
      description: 'Consultation Fee',
      amount: 200,
      flagged_overcharge: false,
      explanation: 'Standard consultation charge, within normal range.',
    },
    {
      id: 'li-flagged',
      description: 'Advanced MRI Scan',
      amount: 2000,
      flagged_overcharge: true,
      explanation: 'This charge appears significantly above the market average.',
    },
  ],
}

describe('BillDetailPage — flagged line items', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders the bill total amount', async () => {
    vi.mocked(billsApi.getBill).mockResolvedValueOnce(billWithFlaggedItem)
    renderBillDetail('bill-abc')
    await waitFor(() => {
      expect(screen.getByText(/2,200/)).toBeInTheDocument()
    })
  })

  it('renders all line item descriptions', async () => {
    vi.mocked(billsApi.getBill).mockResolvedValueOnce(billWithFlaggedItem)
    renderBillDetail('bill-abc')
    await waitFor(() => {
      expect(screen.getByText('Consultation Fee')).toBeInTheDocument()
      expect(screen.getByText('Advanced MRI Scan')).toBeInTheDocument()
    })
  })

  it('shows a ⚠️ Flagged badge for overcharge items', async () => {
    vi.mocked(billsApi.getBill).mockResolvedValueOnce(billWithFlaggedItem)
    renderBillDetail('bill-abc')
    await waitFor(() => {
      const badges = screen.getAllByText(/flagged/i)
      expect(badges.length).toBeGreaterThan(0)
    })
  })

  it('applies the line-item-flagged CSS class to overcharge rows', async () => {
    vi.mocked(billsApi.getBill).mockResolvedValueOnce(billWithFlaggedItem)
    const { container } = renderBillDetail('bill-abc')
    await waitFor(() => {
      const flaggedRows = container.querySelectorAll('.line-item-flagged')
      expect(flaggedRows.length).toBe(1) // only MRI row is flagged
    })
  })

  it('renders AI explanations for explained items', async () => {
    vi.mocked(billsApi.getBill).mockResolvedValueOnce(billWithFlaggedItem)
    renderBillDetail('bill-abc')
    await waitFor(() => {
      expect(screen.getByText(/standard consultation charge/i)).toBeInTheDocument()
      expect(screen.getByText(/significantly above the market average/i)).toBeInTheDocument()
    })
  })

  it('shows the overcharge count in the summary', async () => {
    vi.mocked(billsApi.getBill).mockResolvedValueOnce(billWithFlaggedItem)
    renderBillDetail('bill-abc')
    await waitFor(() => {
      expect(screen.getByText(/potential overcharges/i)).toBeInTheDocument()
      expect(screen.getByText('1 item')).toBeInTheDocument()
    })
  })

  it('shows an error when bill fails to load', async () => {
    vi.mocked(billsApi.getBill).mockRejectedValueOnce(new Error('Not found'))
    renderBillDetail('bill-xyz')
    await waitFor(() => {
      expect(screen.getByText(/bill not found or failed to load/i)).toBeInTheDocument()
    })
  })
})
