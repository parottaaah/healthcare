import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from '../context/AuthContext'
import { LoginPage } from '../pages/LoginPage'
import * as authApi from '../api/auth'

// Mock the auth API module
vi.mock('../api/auth')

function renderLoginPage() {
  vi.mocked(authApi.getMe).mockRejectedValue(new Error('unauthenticated'))
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

  it('renders login form fields', async () => {
    renderLoginPage()
    expect(await screen.findByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('calls login API on success', async () => {
    vi.mocked(authApi.login).mockResolvedValueOnce({
      message: 'Logged in successfully',
    })

    renderLoginPage()

    const emailInput = await screen.findByLabelText(/email/i)
    fireEvent.change(emailInput, {
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
  })

  it('shows error message on login failure', async () => {
    vi.mocked(authApi.login).mockRejectedValueOnce({
      response: { data: { detail: 'Invalid email or password' } },
    })

    renderLoginPage()

    const emailInput = await screen.findByLabelText(/email/i)
    fireEvent.change(emailInput, {
      target: { value: 'wrong@example.com' },
    })
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'wrongpass' },
    })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(
        'Invalid email or password'
      )
    })
  })
})
