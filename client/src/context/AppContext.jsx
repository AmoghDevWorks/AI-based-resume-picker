import React, { createContext, useContext, useState, useCallback } from 'react'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL

const AppContext = createContext(undefined)

// Pipeline steps shown during a request — purely cosmetic, just tracks
// real elapsed time against a fixed list of labels.
const STEPS = [
    'Encoding Job Description',
    'Retrieving Candidate Embeddings',
    'Feature Extraction',
    'Ranking Model',
    'Honeypot Filtering',
    'Generating Explanations',
    'Top Candidates Ready',
]

export function AppProvider({ children }) {
    const [jdFile, setJdFile] = useState(null)
    const [candidateFile, setCandidateFile] = useState(null)
    const [topK, setTopK] = useState(100)

    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [progress, setProgress] = useState(null) // index into STEPS, or null when idle
    const [results, setResults] = useState(null)
    const [selected, setSelected] = useState(null)

    // Animates the progress list while the real request is in flight.
    // It's decoupled from the actual response — it just gives the user
    // something to look at and settles once the fetch resolves.
    const animateProgress = useCallback(async () => {
        for (let i = 0; i < STEPS.length; i++) {
            await new Promise((r) => setTimeout(r, 450 + Math.random() * 350))
            setProgress(i + 1)
        }
    }, [])

    const reset = useCallback(() => {
        setJdFile(null)
        setCandidateFile(null)
        setTopK(100)
        setError(null)
        setProgress(null)
        setResults(null)
        setSelected(null)
    }, [])

    const rankCandidates = useCallback(async () => {
        if (!jdFile || !candidateFile) {
            setError('Upload both files before ranking.')
            return
        }
        if (!BACKEND_URL) {
            setError('VITE_BACKEND_URL is not set — check your .env file.')
            return
        }

        setError(null)
        setResults(null)
        setProgress(0)
        setLoading(true)

        const progressDone = animateProgress()

        try {
            // Backend expects multipart/form-data with these three fields:
            //   jd: UploadFile, candidates: UploadFile, top_k: int (Form)
            const formData = new FormData()
            formData.append('jd', jdFile)
            formData.append('candidates', candidateFile)
            formData.append('top_k', String(topK))

            const res = await fetch(`${BACKEND_URL}/rank`, {
                method: 'POST',
                body: formData,
            })

            if (!res.ok) {
                let detail = `Server responded ${res.status}`
                try {
                    const body = await res.json()
                    detail = body?.detail ? `${detail}: ${JSON.stringify(body.detail)}` : detail
                } catch {
                    // response wasn't JSON — keep the generic message
                }
                throw new Error(detail)
            }

            const data = await res.json()
            await progressDone

            // rank_candidates() returns `results`, not `candidates` — normalize
            // the shape here so the UI only ever deals with one field name.
            setResults({
                total_candidates: data.total_candidates_received,
                ranked: data.candidates_returned,
                candidates_above_threshold: data.candidates_above_threshold,
                candidates_skipped: data.candidates_skipped,
                message: data.message,
                candidates: (data.results || []).map((r) => ({
                    id: r.candidate_id,
                    score: r.final_score,
                    reasoning: `Matched via TF-IDF (${r.tfidf_score}), Skills (${r.skill_match_score}), and Platform Signals (${r.platform_score}). Experience Score: ${r.exp_score}. Notice Bonus: ${r.notice_bonus || 0}`,
                    skills: r.top_skills ? r.top_skills.split(', ') : [],
                    experience: r.years_of_experience ? `${r.years_of_experience} years` : '—',
                    title: r.current_title || r.latest_title || '—',
                    availability: r.notice_period_days !== '' && r.notice_period_days !== null ? `${r.notice_period_days} days` : '—',
                })),
            })
        } catch (err) {
            await progressDone
            setError(err.message || 'Something went wrong while ranking candidates.')
        } finally {
            setLoading(false)
        }
    }, [jdFile, candidateFile, topK, animateProgress])

    const value = {
        // files
        jdFile, setJdFile,
        candidateFile, setCandidateFile,
        topK, setTopK,
        // request lifecycle
        loading,
        error,
        progress,
        results,
        // table selection (modal)
        selected, setSelected,
        // actions
        rankCandidates,
        reset,
        // constants
        STEPS,
    }

    return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useAppContext() {
    const ctx = useContext(AppContext)
    if (ctx === undefined) {
        throw new Error('useAppContext must be used within an AppProvider')
    }
    return ctx
}