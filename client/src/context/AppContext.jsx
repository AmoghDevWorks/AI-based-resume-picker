import React, { createContext, useContext, useState, useCallback } from 'react'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL

const AppContext = createContext(undefined)

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
    const [progress, setProgress] = useState(null)
    const [results, setResults] = useState(null)
    const [selected, setSelected] = useState(null)

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
            const formData = new FormData()
            formData.append('jd', jdFile)
            formData.append('candidates', candidateFile)
            formData.append('top_k', String(topK))

            const res = await fetch(`${BACKEND_URL}rank`, {
                method: 'POST',
                body: formData,
            })

            if (!res.ok) {
                let detail = `Server responded ${res.status}`
                try {
                    const body = await res.json()
                    detail = body?.detail ? `${detail}: ${JSON.stringify(body.detail)}` : detail
                } catch { /* non-JSON error body */ }
                throw new Error(detail)
            }

            const data = await res.json()
            await progressDone

            const top100 = data.top_100 || data.results || []

            const candidates = top100.map((r, i) => ({
                rank: i + 1,
                id: r.candidate_id,
                name: r.name || '—',
                score: typeof r.final_score === 'number' ? r.final_score : 0,
                tfidf_score: r.tfidf_score ?? '—',
                skill_score: r.skill_match_score ?? '—',
                exp_score: r.exp_score ?? '—',
                platform_score: r.platform_score ?? '—',
                notice_bonus: r.notice_bonus ?? 0,
                reasoning: buildReasoning(r),
                skills: r.top_skills ? r.top_skills.split(', ').filter(Boolean) : [],
                experience: r.years_of_experience != null ? `${r.years_of_experience} yrs` : '—',
                title: r.current_title || r.latest_title || '—',
                company: r.current_company || r.latest_company || '—',
                location: r.location || '—',
                availability: r.notice_period_days != null && r.notice_period_days !== ''
                    ? `${r.notice_period_days} days`
                    : '—',
                open_to_work: r.open_to_work,
                salary_min: r.salary_min_lpa,
                salary_max: r.salary_max_lpa,
                github_score: r.github_score ?? '—',
                interview_rate: r.interview_completion ?? '—',
                honeypot_flags: r.honeypot_flags || '',
            }))

            setResults({
                total_candidates: data.total_candidates_received,
                candidates_above_threshold: data.candidates_above_threshold,
                candidates_skipped: data.candidates_skipped,
                honeypots_removed: data.honeypots_removed ?? 0,
                honeypot_ids: data.honeypot_ids ?? [],
                ranked: data.candidates_returned,
                message: data.message,
                candidates,
                all_above_threshold: data.all_above_threshold || [],
            })
        } catch (err) {
            await progressDone
            setError(err.message || 'Something went wrong while ranking candidates.')
        } finally {
            setLoading(false)
        }
    }, [jdFile, candidateFile, topK, animateProgress])

    // ── CSV download (submission format) ────────────────────────────────
    const downloadCSV = useCallback(() => {
        if (!results?.candidates?.length) return

        // Sort by score descending, tiebreak by candidate_id ascending.
        // Doing this in ONE sort (instead of trusting the `rank` already
        // on each candidate) guarantees both validator rules at once:
        // scores end up non-increasing by construction, and any tie is
        // always broken by candidate_id ascending — no separate clamping
        // step needed, and no tie can slip through unbroken.
        const sorted = [...results.candidates].sort((a, b) => {
            const scoreA = typeof a.score === 'number' ? a.score : 0
            const scoreB = typeof b.score === 'number' ? b.score : 0
            if (scoreB !== scoreA) return scoreB - scoreA
            return String(a.id).localeCompare(String(b.id))
        })

        // Reassign ranks 1..N from the sorted order. Don't reuse the
        // original `rank` field — it reflects the API's response order,
        // which is not guaranteed to already be tie-broken by id.
        const rows = sorted.map((c, i) => {
            const score = typeof c.score === 'number' ? c.score : 0
            // Escape double quotes inside reasoning per CSV spec
            const reasoning = (c.reasoning || '').replace(/"/g, '""')
            return {
                candidate_id: c.id,
                rank:         i + 1,
                score,
                reasoning,
            }
        })

        // Build CSV — reasoning wrapped in quotes to allow commas inside
        const header = 'candidate_id,rank,score,reasoning'
        const lines = rows.map(
            (r) => `${r.candidate_id},${r.rank},${r.score},"${r.reasoning}"`
        )
        const csv = [header, ...lines].join('\n')

        // No BOM here: the validator does an exact string match on the
        // header row. A leading U+FEFF gets prepended to the first cell
        // (turning "candidate_id" into "\uFEFFcandidate_id") and fails
        // that check. Plain UTF-8 without BOM is what's required.
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
        const url  = URL.createObjectURL(blob)
        const a    = document.createElement('a')
        a.href     = url
        a.download = 'redrob_submission.csv'
        a.click()
        URL.revokeObjectURL(url)
    }, [results])

    const value = {
        jdFile, setJdFile,
        candidateFile, setCandidateFile,
        topK, setTopK,
        loading,
        error,
        progress,
        results,
        selected, setSelected,
        rankCandidates,
        downloadCSV,
        reset,
        STEPS,
    }

    return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

// Build a readable reasoning string from raw score fields
function buildReasoning(r) {
    const parts = []
    if (r.current_title || r.latest_title)
        parts.push(`${r.current_title || r.latest_title}${r.current_company || r.latest_company ? ` at ${r.current_company || r.latest_company}` : ''}`)
    if (r.years_of_experience != null)
        parts.push(`${r.years_of_experience} yrs experience`)
    if (r.tfidf_score != null)
        parts.push(`JD match ${Number(r.tfidf_score).toFixed(1)}`)
    if (r.skill_match_score != null)
        parts.push(`skills ${Number(r.skill_match_score).toFixed(1)}`)
    if (r.platform_score != null)
        parts.push(`platform ${Number(r.platform_score).toFixed(1)}`)
    if (r.notice_bonus && Number(r.notice_bonus) > 0)
        parts.push(`+${r.notice_bonus} notice bonus`)
    return parts.join(' · ')
}

export function useAppContext() {
    const ctx = useContext(AppContext)
    if (ctx === undefined) throw new Error('useAppContext must be used within an AppProvider')
    return ctx
}