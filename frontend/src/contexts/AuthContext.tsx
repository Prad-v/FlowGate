/** Authentication context for React */

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { authService, User, LoginRequest, ChangePasswordRequest } from '../services/auth'

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (credentials: LoginRequest) => Promise<void>
  logout: () => Promise<void>
  changePassword: (data: ChangePasswordRequest) => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Check if user is authenticated on mount
  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      if (authService.isAuthenticated()) {
        const currentUser = await authService.getCurrentUser()
        setUser(currentUser)
      }
    } catch (error) {
      // Not authenticated or token expired
      authService.clearTokens()
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (credentials: LoginRequest) => {
    const response = await authService.login(credentials)
    setUser(response.user)
    
    // If password change required, don't set as fully authenticated yet
    if (response.requires_password_change) {
      // User will need to change password
      return
    }
  }

  const logout = async () => {
    await authService.logout()
    setUser(null)
  }

  const changePassword = async (data: ChangePasswordRequest) => {
    await authService.changePassword(data)
    // Refresh user info after password change
    await refreshUser()
  }

  const refreshUser = async () => {
    try {
      const currentUser = await authService.getCurrentUser()
      setUser(currentUser)
    } catch (error) {
      setUser(null)
    }
  }

  const value: AuthContextType = {
    user,
    isAuthenticated: user !== null && authService.isAuthenticated(),
    isLoading,
    login,
    logout,
    changePassword,
    refreshUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

