import React, { createContext, useContext, useState, useCallback } from 'react'
import * as XLSX from 'xlsx'

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

            // Backend now returns:
            //   top_100              → the ranked submission slice
            //   all_above_threshold  → full cleaned pool
            //   honeypots_removed    → count of discarded profiles
            //   honeypot_ids         → their IDs
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
                // full pool for potential "show all" feature
                all_above_threshold: data.all_above_threshold || [],
            })
        } catch (err) {
            await progressDone
            setError(err.message || 'Something went wrong while ranking candidates.')
        } finally {
            setLoading(false)
        }
    }, [jdFile, candidateFile, topK, animateProgress])

    // ── Excel download ───────────────────────────────────────────────
    const downloadExcel = useCallback(() => {
        if (!results?.candidates?.length) return

        const rows = results.candidates.map((c) => ({
            'Rank':                c.rank,
            'Candidate ID':        c.id,
            'Name':                c.name,
            'Final Score':         c.score,
            'TF-IDF Score':        c.tfidf_score,
            'Skill Match Score':   c.skill_score,
            'Experience Score':    c.exp_score,
            'Platform Score':      c.platform_score,
            'Notice Bonus':        c.notice_bonus,
            'Title':               c.title,
            'Company':             c.company,
            'Location':            c.location,
            'Experience':          c.experience,
            'Availability (days)': c.availability,
            'Open to Work':        c.open_to_work != null ? String(c.open_to_work) : '—',
            'Salary Min (LPA)':    c.salary_min ?? '—',
            'Salary Max (LPA)':    c.salary_max ?? '—',
            'Top Skills':          c.skills.join(', '),
            'GitHub Score':        c.github_score,
            'Interview Rate':      c.interview_rate,
            'Reasoning':           c.reasoning,
        }))

        const wb = XLSX.utils.book_new()

        // Sheet 1 — Top candidates
        const ws1 = XLSX.utils.json_to_sheet(rows)
        // column widths
        ws1['!cols'] = [
            { wch: 6 },  // Rank
            { wch: 16 }, // ID
            { wch: 20 }, // Name
            { wch: 13 }, // Score
            { wch: 13 }, // TF-IDF
            { wch: 15 }, // Skill
            { wch: 16 }, // Exp
            { wch: 15 }, // Platform
            { wch: 13 }, // Bonus
            { wch: 28 }, // Title
            { wch: 24 }, // Company
            { wch: 18 }, // Location
            { wch: 13 }, // Experience
            { wch: 18 }, // Availability
            { wch: 12 }, // Open to Work
            { wch: 15 }, // Salary Min
            { wch: 15 }, // Salary Max
            { wch: 40 }, // Skills
            { wch: 13 }, // GitHub
            { wch: 14 }, // Interview
            { wch: 60 }, // Reasoning
        ]
        XLSX.utils.book_append_sheet(wb, ws1, 'Top Candidates')

        // Sheet 2 — Summary stats
        const stats = [
            ['Metric', 'Value'],
            ['Total candidates received',   results.total_candidates],
            ['Candidates above threshold',  results.candidates_above_threshold],
            ['Honeypots removed',           results.honeypots_removed],
            ['Candidates skipped',          results.candidates_skipped],
            ['Final ranked count',          results.ranked],
        ]
        if (results.honeypot_ids?.length) {
            stats.push(['', ''])
            stats.push(['Removed honeypot IDs', results.honeypot_ids.join(', ')])
        }
        const ws2 = XLSX.utils.aoa_to_sheet(stats)
        ws2['!cols'] = [{ wch: 30 }, { wch: 50 }]
        XLSX.utils.book_append_sheet(wb, ws2, 'Summary')

        XLSX.writeFile(wb, 'redrob_ranking.xlsx')
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
        downloadExcel,
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