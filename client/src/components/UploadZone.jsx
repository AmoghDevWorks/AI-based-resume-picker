import React, { useState } from 'react';
import { useUser } from '../contexts/UserContext';

export default function UploadZone() {
    const { setResults, setCsvData, loading, setLoading, setError } = useUser();

    const [jdFile, setJdFile] = useState(null);
    const [candFile, setCandFile] = useState(null);

    const handleUpload = async () => {
        if (!jdFile || !candFile) {
            setError("Please select both a Job Description and a Candidates JSONL file.");
            return;
        }

        setLoading(true);
        setError(null);
        setResults(null);

        const formData = new FormData();
        formData.append("jd", jdFile);
        formData.append("candidates", candFile);
        formData.append("top_k", "100");

        try {
            const res = await fetch("http://localhost:8000/rank", {
                method: "POST",
                body: formData,
            });

            if (!res.ok) {
                throw new Error(`Ranking Engine Failed: ${res.statusText}`);
            }

            const data = await res.json();
            setResults(data.results);
            setCsvData(data.csv_data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="glass-panel rounded-2xl p-8 w-full max-w-3xl mx-auto transition-all">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h3 className="text-xl font-semibold text-slate-900 dark:text-white">Data Sources</h3>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Provide the inputs for the ranking engine.</p>
                </div>
                <div className="px-3 py-1 rounded-full bg-green-500/10 text-green-600 dark:text-green-400 text-xs font-medium border border-green-500/20">
                    Offline Engine Ready
                </div>
            </div>
            
            <div className="space-y-6">
                <div className="relative group">
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                        Job Description <span className="text-slate-400 font-normal">(PDF, DOCX)</span>
                    </label>
                    <div className="flex items-center justify-center w-full">
                        <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl cursor-pointer bg-slate-50 hover:bg-slate-100 dark:bg-[#0f1115]/50 dark:hover:bg-white/[0.02] transition-all group-hover:border-indigo-400 dark:group-hover:border-indigo-500/50">
                            <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                <svg className="w-8 h-8 mb-3 text-slate-400 group-hover:text-indigo-500 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                                </svg>
                                <p className="mb-2 text-sm text-slate-500 dark:text-slate-400">
                                    <span className="font-semibold text-indigo-600 dark:text-indigo-400">Click to upload</span> or drag and drop
                                </p>
                                <p className="text-xs text-slate-400 dark:text-slate-500">
                                    {jdFile ? jdFile.name : "No file selected"}
                                </p>
                            </div>
                            <input type="file" className="hidden" accept=".pdf,.docx" onChange={(e) => setJdFile(e.target.files[0])} />
                        </label>
                    </div>
                </div>

                <div className="relative group">
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                        Candidate Dataset <span className="text-slate-400 font-normal">(JSONL)</span>
                    </label>
                    <div className="flex items-center justify-center w-full">
                        <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl cursor-pointer bg-slate-50 hover:bg-slate-100 dark:bg-[#0f1115]/50 dark:hover:bg-white/[0.02] transition-all group-hover:border-purple-400 dark:group-hover:border-purple-500/50">
                            <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                <svg className="w-8 h-8 mb-3 text-slate-400 group-hover:text-purple-500 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                                </svg>
                                <p className="mb-2 text-sm text-slate-500 dark:text-slate-400">
                                    <span className="font-semibold text-purple-600 dark:text-purple-400">Click to upload</span> or drag and drop
                                </p>
                                <p className="text-xs text-slate-400 dark:text-slate-500">
                                    {candFile ? candFile.name : "candidates.jsonl required"}
                                </p>
                            </div>
                            <input type="file" className="hidden" accept=".jsonl" onChange={(e) => setCandFile(e.target.files[0])} />
                        </label>
                    </div>
                </div>

                <div className="pt-4 border-t border-slate-200 dark:border-slate-700/50 flex justify-end">
                    <button 
                        onClick={handleUpload}
                        disabled={loading}
                        className={`relative inline-flex items-center justify-center px-8 py-3 overflow-hidden font-medium text-white transition-all duration-300 bg-indigo-600 rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 ${loading ? 'opacity-70 cursor-not-allowed' : 'shadow-lg shadow-indigo-500/30 hover:shadow-indigo-500/50'}`}
                    >
                        {loading ? (
                            <>
                                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Executing Pipeline...
                            </>
                        ) : (
                            <span className="flex items-center">
                                Compute Rankings
                                <svg className="w-4 h-4 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                                </svg>
                            </span>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}
