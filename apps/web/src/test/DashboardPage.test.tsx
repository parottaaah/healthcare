import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from '../context/AuthContext'
import { DashboardPage } from '../pages/DashboardPage'
import * as billsApi from '../api/bills'
import { Bill } from '../api/bills'

vi.mock('../api/bills')

// Stub fetch used by HealthFooter
global.fetch = vi.fn().mockResolvedValue({
  json: () => Promise.resolve({ status: 'ok' }),
} as Response)

function renderDashboard(token = 'mock-token') {
  localStorage.setItem('token', token)
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
      { id: 'li-1', description: 'Consultation Fee', amount: 500, flagged_overcharge: false },
      { id: 'li-2', description: 'MRI Scan', amount: 1000, flagged_overcharge: true },
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

  it('shows a loading spinner while fetching', () => {
    vi.mocked(billsApi.getBills).mockReturnValue(new Promise(() => {}))
    renderDashboard()
    expect(screen.getByLabelText(/loading bills/i)).toBeInTheDocument()
  })

  it('renders list of bills returned from the API', async () => {
    vi.mocked(billsApi.getBills).mockResolvedValueOnce(mockBills)
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByText(/1,500/)).toBeInTheDocument()
      expect(screen.getByText(/350/)).toBeInTheDocument()
    })
  })

  it('shows empty-state message when no bills exist', async () => {
    vi.mocked(billsApi.getBills).mockResolvedValueOnce([])
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByText(/no bills yet/i)).toBeInTheDocument()
    })
  })

  it('shows an error message when the API call fails', async () => {
    vi.mocked(billsApi.getBills).mockRejectedValueOnce(new Error('Network error'))
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/failed to load bills/i)
    })
  })
})
