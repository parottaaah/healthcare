import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from '../context/AuthContext'
import { DashboardPage } from '../pages/DashboardPage'
import * as billsApi from '../api/bills'
import * as authApi from '../api/auth'
import type { Bill } from '../api/bills'

vi.mock('../api/bills')
vi.mock('../api/auth')

// Mock fetch for health footer
globalThis.fetch = vi.fn().mockResolvedValue({
  json: () => Promise.resolve({ status: 'ok' }),
} as Response)

function renderDashboard() {
  vi.mocked(authApi.getMe).mockResolvedValue({ id: '1', email: 'test@test.com', name: 'Test' })
  return render(
    <MemoryRouter initialEntries={['/dashboard']}>
      <AuthProvider>
        <DashboardPage />
      </AuthProvider>
    </MemoryRouter>
  )
}

const mockBills: Bill[] = [
  {
    id: 'bill-1',
    user_id: 'user-1',
    raw_file_url: 'uploads/bill1.jpg',
    total_amount: 1500.0,
    currency: 'INR',
    status: 'parsed',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:01:00Z',
    line_items: [
      {
        id: 'li-1',
        description: 'Consultation Fee',
        amount: 500,
        flagged_overcharge: false,
        explanation: null,
      },
      {
        id: 'li-2',
        description: 'MRI Scan',
        amount: 1000,
        flagged_overcharge: true,
        explanation: 'Above average cost for this procedure',
      },
    ],
  },
  {
    id: 'bill-2',
    user_id: 'user-1',
    raw_file_url: 'uploads/bill2.pdf',
    total_amount: 350.0,
    currency: 'INR',
    status: 'uploaded',
    created_at: '2024-01-20T14:00:00Z',
    updated_at: '2024-01-20T14:00:00Z',
    line_items: [],
  },
]

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('shows loading state initially', async () => {
    vi.mocked(billsApi.getBills).mockReturnValue(new Promise(() => {})) // Never resolves
    renderDashboard()
    expect(await screen.findByLabelText(/loading bills/i)).toBeInTheDocument()
  })

  it('renders list of bills from API', async () => {
    vi.mocked(billsApi.getBills).mockResolvedValueOnce(mockBills)
    renderDashboard()

    await waitFor(() => {
      // Both bills should appear — check by amount display
      expect(screen.getByText(/1,500/)).toBeInTheDocument()
      expect(screen.getByText(/350/)).toBeInTheDocument()
    })
  })

  it('shows empty state when no bills returned', async () => {
    vi.mocked(billsApi.getBills).mockResolvedValueOnce([])
    renderDashboard()

    await waitFor(() => {
      expect(
        screen.getByText(/no bills yet/i)
      ).toBeInTheDocument()
    })
  })

  it('shows error message if API call fails', async () => {
    vi.mocked(billsApi.getBills).mockRejectedValueOnce(new Error('Network error'))
    renderDashboard()

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/failed to load bills/i)
    })
  })
})
