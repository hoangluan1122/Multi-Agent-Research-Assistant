import { useState, useEffect } from 'react'
import './index.css'

function App() {
  const [healthStatus, setHealthStatus] = useState<string>('checking...')

  useEffect(() => {
    fetch('http://localhost:8000/api/health')
      .then((res) => res.json())
      .then((data) => setHealthStatus(data.status))
      .catch(() => setHealthStatus('Backend not running'))
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white">
      {/* Header */}
      <header className="border-b border-gray-700/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            Multi-Agent Research Assistant
          </h1>
          <div className="flex items-center gap-2 text-sm">
            <span
              className={`inline-block w-2 h-2 rounded-full ${
                healthStatus === 'healthy' ? 'bg-green-400' : 'bg-red-400'
              }`}
            />
            <span className="text-gray-400">
              API: {healthStatus}
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-16">
        <div className="text-center space-y-8">
          {/* Hero */}
          <div className="space-y-4">
            <h2 className="text-5xl font-bold tracking-tight">
              <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                Research Assistant
              </span>
            </h2>
            <p className="text-gray-400 text-lg max-w-2xl mx-auto">
              Hệ thống hỗ trợ nghiên cứu đa tác tử thông minh, được xây dựng với
              React + Vite + TypeScript + Tailwind CSS và FastAPI.
            </p>
          </div>

          {/* Tech Stack Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-12">
            {[
              { name: 'React', desc: 'UI Library', color: 'from-cyan-500 to-blue-500' },
              { name: 'TypeScript', desc: 'Type Safety', color: 'from-blue-500 to-indigo-500' },
              { name: 'Tailwind CSS', desc: 'Utility-First CSS', color: 'from-teal-500 to-cyan-500' },
              { name: 'FastAPI', desc: 'Backend API', color: 'from-green-500 to-emerald-500' },
            ].map((tech) => (
              <div
                key={tech.name}
                className="group relative p-6 rounded-2xl bg-gray-800/50 border border-gray-700/50 hover:border-gray-600/50 transition-all duration-300 hover:shadow-lg hover:shadow-purple-500/5 hover:-translate-y-1"
              >
                <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${tech.color} opacity-0 group-hover:opacity-5 transition-opacity duration-300`} />
                <h3 className={`text-lg font-semibold bg-gradient-to-r ${tech.color} bg-clip-text text-transparent`}>
                  {tech.name}
                </h3>
                <p className="text-gray-500 text-sm mt-1">{tech.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-700/50 mt-auto">
        <div className="max-w-7xl mx-auto px-6 py-6 text-center text-gray-500 text-sm">
          Multi-Agent Research Assistant &copy; {new Date().getFullYear()}
        </div>
      </footer>
    </div>
  )
}

export default App
