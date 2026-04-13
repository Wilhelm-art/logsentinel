import { render, screen } from '@testing-library/react'
import SignInPage from '@/app/auth/signin/page'
import { Suspense } from 'react'

// Mock next/navigation useSearchParams
jest.mock('next/navigation', () => ({
  useSearchParams: jest.fn(),
}))

// Mock next-auth/react
jest.mock('next-auth/react', () => ({
  signIn: jest.fn(),
}))

describe('SignInPage Error Handling Component', () => {
  it('renders standard signin view when no error exists', () => {
    const { useSearchParams } = require('next/navigation')
    useSearchParams.mockReturnValue(new URLSearchParams(''))
    
    render(<SignInPage />)
    
    expect(screen.getByText('LogSentinel')).toBeInTheDocument()
    expect(screen.getByText('Continue with Google')).toBeInTheDocument()
    expect(screen.queryByText('Authentication Error')).not.toBeInTheDocument()
  })

  it('renders Access Denied error when error=AccessDenied', () => {
    const { useSearchParams } = require('next/navigation')
    useSearchParams.mockReturnValue(new URLSearchParams('?error=AccessDenied'))

    render(<SignInPage />)
    
    expect(screen.getByText('Access Denied')).toBeInTheDocument()
    expect(screen.getByText('Your email is not in the allowed users list. Contact your administrator.')).toBeInTheDocument()
  })

  it('renders Server Configuration Error when error=Configuration', () => {
    const { useSearchParams } = require('next/navigation')
    useSearchParams.mockReturnValue(new URLSearchParams('?error=Configuration'))

    render(<SignInPage />)
    
    expect(screen.getByText('Server Configuration Error')).toBeInTheDocument()
    expect(screen.getByText(/Authentication providers \(Google\/GitHub\) are missing/)).toBeInTheDocument()
  })

  it('renders generic Authentication Error for other errors', () => {
    const { useSearchParams } = require('next/navigation')
    useSearchParams.mockReturnValue(new URLSearchParams('?error=Callback'))

    render(<SignInPage />)
    
    expect(screen.getByText('Authentication Error')).toBeInTheDocument()
    expect(screen.getByText('An error occurred during sign in. Please try again.')).toBeInTheDocument()
  })
})
