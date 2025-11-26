import { Link, useLocation } from 'react-router-dom'
import { ReactNode, useState, useEffect, useRef } from 'react'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const [logManagementOpen, setLogManagementOpen] = useState(false)
  const [agentManagementOpen, setAgentManagementOpen] = useState(false)
  const [securityOpen, setSecurityOpen] = useState(false)
  const logManagementRef = useRef<HTMLDivElement>(null)
  const agentManagementRef = useRef<HTMLDivElement>(null)
  const securityRef = useRef<HTMLDivElement>(null)

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/'
    }
    return location.pathname === path || location.pathname.startsWith(path + '/')
  }

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (logManagementRef.current && !logManagementRef.current.contains(event.target as Node)) {
        setLogManagementOpen(false)
      }
      if (agentManagementRef.current && !agentManagementRef.current.contains(event.target as Node)) {
        setAgentManagementOpen(false)
      }
      if (securityRef.current && !securityRef.current.contains(event.target as Node)) {
        setSecurityOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  // Close dropdowns when route changes
  useEffect(() => {
    setLogManagementOpen(false)
    setAgentManagementOpen(false)
    setSecurityOpen(false)
  }, [location.pathname])

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <h1 className="text-xl font-bold text-gray-900">Flowgate</h1>
              </div>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                <Link
                  to="/"
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                    isActive('/') && !isActive('/templates') && !isActive('/deployments') && !isActive('/log-transformer') && !isActive('/agents') && !isActive('/opamp-config') && !isActive('/settings')
                      ? 'border-blue-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                  }`}
                >
                  Dashboard
                </Link>
                <Link
                  to="/templates"
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                    isActive('/templates')
                      ? 'border-blue-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                  }`}
                >
                  Templates
                </Link>
                <Link
                  to="/deployments"
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                    isActive('/deployments')
                      ? 'border-blue-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                  }`}
                >
                  Deployments
                </Link>
                
                {/* Log Management Dropdown */}
                <div className="relative" ref={logManagementRef}>
                  <button
                    type="button"
                    onClick={() => {
                      setLogManagementOpen(!logManagementOpen)
                      setAgentManagementOpen(false)
                    }}
                    className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                      isActive('/log-transformer')
                        ? 'border-blue-500 text-gray-900'
                        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    }`}
                  >
                    Log Management
                    <svg
                      className={`ml-1 h-4 w-4 transition-transform duration-200 ${logManagementOpen ? 'rotate-180' : ''}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  {logManagementOpen && (
                    <div className="absolute left-0 top-full mt-0 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-50">
                      <div className="py-1" role="menu">
                        <Link
                          to="/log-transformer"
                          onClick={() => setLogManagementOpen(false)}
                          className={`block px-4 py-2 text-sm transition-colors ${
                            isActive('/log-transformer')
                              ? 'bg-blue-50 text-blue-700 font-medium'
                              : 'text-gray-700 hover:bg-gray-50'
                          }`}
                          role="menuitem"
                        >
                          Log Transformer
                        </Link>
                      </div>
                    </div>
                  )}
                </div>

                {/* Agent Management Dropdown */}
                <div className="relative" ref={agentManagementRef}>
                  <button
                    type="button"
                    onClick={() => {
                      setAgentManagementOpen(!agentManagementOpen)
                      setLogManagementOpen(false)
                    }}
                    className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                      isActive('/agents') || isActive('/opamp-config')
                        ? 'border-blue-500 text-gray-900'
                        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    }`}
                  >
                    Agent Management
                    <svg
                      className={`ml-1 h-4 w-4 transition-transform duration-200 ${agentManagementOpen ? 'rotate-180' : ''}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  {agentManagementOpen && (
                    <div className="absolute left-0 top-full mt-0 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-50">
                      <div className="py-1" role="menu">
                        <Link
                          to="/agents"
                          onClick={() => setAgentManagementOpen(false)}
                          className={`block px-4 py-2 text-sm transition-colors ${
                            isActive('/agents')
                              ? 'bg-blue-50 text-blue-700 font-medium'
                              : 'text-gray-700 hover:bg-gray-50'
                          }`}
                          role="menuitem"
                        >
                          Agent Inventory
                        </Link>
                        <Link
                          to="/opamp-config"
                          onClick={() => setAgentManagementOpen(false)}
                          className={`block px-4 py-2 text-sm transition-colors ${
                            isActive('/opamp-config')
                              ? 'bg-blue-50 text-blue-700 font-medium'
                              : 'text-gray-700 hover:bg-gray-50'
                          }`}
                          role="menuitem"
                        >
                          OpAMP Config
                        </Link>
                      </div>
                    </div>
                  )}
                </div>

                {/* Security Dropdown */}
                <div className="relative" ref={securityRef}>
                  <button
                    type="button"
                    onClick={() => {
                      setSecurityOpen(!securityOpen)
                      setLogManagementOpen(false)
                      setAgentManagementOpen(false)
                    }}
                    className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                      isActive('/threat-management') || isActive('/access-governance') || isActive('/incidents') || isActive('/personas') || isActive('/soar-playbooks')
                        ? 'border-blue-500 text-gray-900'
                        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    }`}
                  >
                    Security
                    <svg
                      className={`ml-1 h-4 w-4 transition-transform duration-200 ${securityOpen ? 'rotate-180' : ''}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  {securityOpen && (
                    <div className="absolute left-0 top-full mt-0 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-50">
                      <div className="py-1" role="menu">
                        <Link
                          to="/threat-management"
                          onClick={() => setSecurityOpen(false)}
                          className={`block px-4 py-2 text-sm transition-colors ${
                            isActive('/threat-management')
                              ? 'bg-blue-50 text-blue-700 font-medium'
                              : 'text-gray-700 hover:bg-gray-50'
                          }`}
                          role="menuitem"
                        >
                          Threat Management
                        </Link>
                        <Link
                          to="/access-governance"
                          onClick={() => setSecurityOpen(false)}
                          className={`block px-4 py-2 text-sm transition-colors ${
                            isActive('/access-governance')
                              ? 'bg-blue-50 text-blue-700 font-medium'
                              : 'text-gray-700 hover:bg-gray-50'
                          }`}
                          role="menuitem"
                        >
                          Access Governance
                        </Link>
                        <Link
                          to="/incidents"
                          onClick={() => setSecurityOpen(false)}
                          className={`block px-4 py-2 text-sm transition-colors ${
                            isActive('/incidents')
                              ? 'bg-blue-50 text-blue-700 font-medium'
                              : 'text-gray-700 hover:bg-gray-50'
                          }`}
                          role="menuitem"
                        >
                          Incidents
                        </Link>
                        <Link
                          to="/personas"
                          onClick={() => setSecurityOpen(false)}
                          className={`block px-4 py-2 text-sm transition-colors ${
                            isActive('/personas')
                              ? 'bg-blue-50 text-blue-700 font-medium'
                              : 'text-gray-700 hover:bg-gray-50'
                          }`}
                          role="menuitem"
                        >
                          Personas
                        </Link>
                        <Link
                          to="/soar-playbooks"
                          onClick={() => setSecurityOpen(false)}
                          className={`block px-4 py-2 text-sm transition-colors ${
                            isActive('/soar-playbooks')
                              ? 'bg-blue-50 text-blue-700 font-medium'
                              : 'text-gray-700 hover:bg-gray-50'
                          }`}
                          role="menuitem"
                        >
                          SOAR Playbooks
                        </Link>
                      </div>
                    </div>
                  )}
                </div>

                <Link
                  to="/settings"
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                    isActive('/settings')
                      ? 'border-blue-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                  }`}
                >
                  Settings
                </Link>
                <Link
                  to="/users"
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                    isActive('/users')
                      ? 'border-blue-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                  }`}
                >
                  User Management
                </Link>
              </div>
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  )
}
