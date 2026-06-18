import React, { useState } from 'react';
import { useUser } from '../contexts/UserContext';

export default function ResultsDashboard() {
    const { results, csvData, loading, error } = useUser();
    const [expandedRow, setExpandedRow] = useState(null);

    if (loading) return null; // Loading handled by UploadZone button

    if (error) {
        return (
            <div className="mt-8 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-500/20 rounded-xl animate-fade-in-up">
                <div className="flex">
                    <div className="flex-shrink-0">
                        <svg className="h-5 w-5 text-red-400 dark:text-red-500" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                        </svg>
                    </div>
                    <div className="ml-3">
                        <h3 className="text-sm font-medium text-red-800 dark:text-red-200">Processing Error</h3>
                        <div className="mt-2 text-sm text-red-700 dark:text-red-300">
                            <p>{error}</p>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    if (!results) return null;

    const downloadCsv = () => {
        const blob = new Blob([csvData], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'TEAM_ID.csv';
        a.click();
    };

    return (
        <div className="mt-12 glass-panel rounded-2xl overflow-hidden animate-fade-in-up">
            <div className="p-6 flex flex-col sm:flex-row justify-between items-start sm:items-center border-b border-slate-200 dark:border-slate-700/50 bg-white/50 dark:bg-[#0f1115]/50">
                <div>
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center">
                        <svg className="w-5 h-5 mr-2 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                        </svg>
                        Top 100 Matches
                    </h2>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Sorted by Hybrid RRF and Deep Scoring Engine.</p>
                </div>
                <button 
                    onClick={downloadCsv}
                    className="mt-4 sm:mt-0 inline-flex items-center glass-button px-4 py-2 rounded-lg text-sm font-semibold"
                >
                    <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    Export Submission CSV
                </button>
            </div>
            
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700/50">
                    <thead className="bg-slate-50/50 dark:bg-[#0f1115]/50 backdrop-blur-md">
                        <tr>
                            <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Rank</th>
                            <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Candidate ID</th>
                            <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Match Score</th>
                            <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Current Role</th>
                            <th scope="col" className="px-6 py-4 relative"><span className="sr-only">Expand</span></th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 dark:divide-slate-700/50 bg-white/40 dark:bg-white/[0.01]">
                        {results.map((candidate) => (
                            <React.Fragment key={candidate.candidate_id}>
                                <tr 
                                    className={`hover:bg-slate-50 dark:hover:bg-white/[0.03] transition-colors cursor-pointer ${expandedRow === candidate.rank ? 'bg-indigo-50/50 dark:bg-indigo-900/10' : ''}`} 
                                    onClick={() => setExpandedRow(expandedRow === candidate.rank ? null : candidate.rank)}
                                >
                                    <td className="px-6 py-5 whitespace-nowrap">
                                        <div className="flex items-center">
                                            <span className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${candidate.rank <= 3 ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300 ring-1 ring-indigo-500/30' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'}`}>
                                                {candidate.rank}
                                            </span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-5 whitespace-nowrap">
                                        <span className="text-sm font-mono text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                                            {candidate.candidate_id}
                                        </span>
                                    </td>
                                    <td className="px-6 py-5 whitespace-nowrap">
                                        <div className="flex items-center">
                                            <div className="w-16 bg-slate-200 dark:bg-slate-700 rounded-full h-2 mr-3">
                                                <div className="bg-indigo-500 h-2 rounded-full" style={{ width: `${Math.min(100, candidate.score * 100)}%` }}></div>
                                            </div>
                                            <span className="text-sm font-medium text-slate-900 dark:text-white">
                                                {(candidate.score * 100).toFixed(1)}%
                                            </span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-5 whitespace-nowrap">
                                        <div className="text-sm text-slate-900 dark:text-white font-medium">{candidate.profile?.current_title || 'N/A'}</div>
                                        <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{candidate.profile?.years_of_experience || 0} years experience</div>
                                    </td>
                                    <td className="px-6 py-5 whitespace-nowrap text-right text-sm font-medium">
                                        <div className="flex justify-end">
                                            <svg className={`w-5 h-5 text-slate-400 transition-transform duration-200 ${expandedRow === candidate.rank ? 'rotate-180 text-indigo-500' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                            </svg>
                                        </div>
                                    </td>
                                </tr>
                                {expandedRow === candidate.rank && (
                                    <tr>
                                        <td colSpan="5" className="px-6 py-4 bg-indigo-50/30 dark:bg-indigo-900/5 border-t-0 animate-fade-in-up">
                                            <div className="flex">
                                                <div className="flex-shrink-0 mt-1 mr-3">
                                                    <svg className="w-5 h-5 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                                        <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                    </svg>
                                                </div>
                                                <div>
                                                    <h4 className="text-xs font-semibold uppercase tracking-wider text-indigo-800 dark:text-indigo-300 mb-1">Algorithmic Reasoning</h4>
                                                    <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed italic border-l-2 border-indigo-200 dark:border-indigo-500/30 pl-3">
                                                        "{candidate.reasoning}"
                                                    </p>
                                                </div>
                                            </div>
                                        </td>
                                    </tr>
                                )}
                            </React.Fragment>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
