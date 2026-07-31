import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from '../context/AuthContext'
import { LoginPage } from '../pages/LoginPage'
import * as authApi from '../api/auth'

vi.mock('../api/auth')

function renderLoginPage() {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    </MemoryRouter>
  )
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders email and password fields', () => {
    renderLoginPage()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('calls login API and stores token in localStorage on success', async () => {
    const mockToken = 'test-jwt-token-abc123'
    vi.mocked(authApi.login).mockResolvedValueOnce({
      access_token: mockToken,
      token_type: 'bearer',
    })

    renderLoginPage()

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'test@example.com' },
    })
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'password123' },
    })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(authApi.login).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
      })
    })
    expect(localStorage.getItem('token')).toBe(mockToken)
  })

  it('shows error alert on login failure', async () => {
    vi.mocked(authApi.login).mockRejectedValueOnce({
      response: { data: { detail: 'Invalid email or password' } },
    })

    renderLoginPage()

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'bad@example.com' },
    })
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'wrong' },
    })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(
        'Invalid email or password'
      )
    })
  })
})
