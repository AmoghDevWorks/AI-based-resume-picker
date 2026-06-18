import React from 'react';
import { useTheme } from './contexts/ThemeContext';
import UploadZone from './components/UploadZone';
import ResultsDashboard from './components/ResultsDashboard';

export default function App() {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen relative overflow-hidden transition-colors duration-500">
      {/* Background Gradients */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-indigo-500/10 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-500/10 blur-[120px] rounded-full pointer-events-none" />
      
      <nav className="border-b border-slate-200/50 dark:border-white/[0.05] bg-white/50 dark:bg-[#0f1115]/50 backdrop-blur-md sticky top-0 z-50 transition-all">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
                RedRob<span className="text-indigo-600 dark:text-indigo-400 font-medium">Ranker</span>
              </h1>
            </div>
            
            <div className="flex items-center">
              <button
                onClick={toggleTheme}
                className="p-2 rounded-full text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-white/5 transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                aria-label="Toggle Dark Mode"
              >
                {theme === 'dark' ? (
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-6xl mx-auto py-12 px-4 sm:px-6 lg:px-8 relative z-10 animate-fade-in-up">
        <div className="mb-12 text-center max-w-2xl mx-auto">
          <h2 className="text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white mb-4">
            Intelligent Candidate Ranking
          </h2>
          <p className="text-base text-slate-500 dark:text-slate-400 leading-relaxed">
            Upload your Job Description and Candidate JSONL dataset. Our local offline engine uses Hybrid Search and Mathematical Heuristics to extract the perfect matches.
          </p>
        </div>

        <div className="grid gap-8 grid-cols-1">
          <UploadZone />
          <ResultsDashboard />
        </div>
      </main>
    </div>
  );
}