import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '../context/AuthContext'
import { BillDetailPage } from '../pages/BillDetailPage'
import * as billsApi from '../api/bills'
import * as authApi from '../api/auth'
import type { Bill } from '../api/bills'

vi.mock('../api/bills')
vi.mock('../api/auth')

function renderBillDetail(billId: string) {
  vi.mocked(authApi.getMe).mockResolvedValue({ id: '1', email: 'test@test.com', name: 'Test' })
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
      explanation: 'This charge appears significantly above the market average for this procedure.',
    },
  ],
}

describe('BillDetailPage — flagged line items', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders bill total amount', async () => {
    vi.mocked(billsApi.getBill).mockResolvedValueOnce(billWithFlaggedItem)
    renderBillDetail('bill-abc')

    await waitFor(() => {
      expect(screen.getByText(/2,200/)).toBeInTheDocument()
    })
  })

  it('renders line item descriptions', async () => {
    vi.mocked(billsApi.getBill).mockResolvedValueOnce(billWithFlaggedItem)
    renderBillDetail('bill-abc')

    await waitFor(() => {
      expect(screen.getByText('Consultation Fee')).toBeInTheDocument()
      expect(screen.getByText('Advanced MRI Scan')).toBeInTheDocument()
    })
  })

  it('shows a visual flag indicator for flagged overcharge items', async () => {
    vi.mocked(billsApi.getBill).mockResolvedValueOnce(billWithFlaggedItem)
    renderBillDetail('bill-abc')

    await waitFor(() => {
      // The flagged badge should appear for overcharge items
      const flagBadges = screen.getAllByText(/flagged/i)
      expect(flagBadges.length).toBeGreaterThan(0)
    })
  })

  it('applies flagged CSS class to overcharge line items', async () => {
    vi.mocked(billsApi.getBill).mockResolvedValueOnce(billWithFlaggedItem)
    const { container } = renderBillDetail('bill-abc')

    await waitFor(() => {
      const flaggedRows = container.querySelectorAll('.line-item-flagged')
      expect(flaggedRows.length).toBe(1) // Only MRI is flagged
    })
  })

  it('shows AI explanations for explained items', async () => {
    vi.mocked(billsApi.getBill).mockResolvedValueOnce(billWithFlaggedItem)
    renderBillDetail('bill-abc')

    await waitFor(() => {
      expect(
        screen.getByText(/standard consultation charge/i)
      ).toBeInTheDocument()
      expect(
        screen.getByText(/significantly above the market average/i)
      ).toBeInTheDocument()
    })
  })

  it('shows flagged summary count when overcharges present', async () => {
    vi.mocked(billsApi.getBill).mockResolvedValueOnce(billWithFlaggedItem)
    renderBillDetail('bill-abc')

    await waitFor(() => {
      expect(screen.getByText(/potential overcharges/i)).toBeInTheDocument()
      expect(screen.getByText('1 item')).toBeInTheDocument()
    })
  })

  it('shows error state when bill fails to load', async () => {
    vi.mocked(billsApi.getBill).mockRejectedValueOnce(new Error('Not found'))
    renderBillDetail('bill-xyz')

    await waitFor(() => {
      expect(screen.getByText(/failed to load/i)).toBeInTheDocument()
    })
  })
})
