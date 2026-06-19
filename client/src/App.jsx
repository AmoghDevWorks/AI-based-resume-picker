import React from 'react'
import { AppProvider, useAppContext } from './context/AppContext'
import DropZone from './components/DropZone'
import CandidateModal from './components/CandidateModal'
import {
    IconUpload, IconFile, IconJson, IconHash, IconCheck, IconX,
    IconSpark, IconSpinner, IconCircle, IconAward, IconUsers, IconClock, IconShield,
} from './components/icons'

// ── Tiny icon for download ───────────────────────────────────────────
function IconDownload() {
    return (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
        </svg>
    )
}

// ── Score bar + number ───────────────────────────────────────────────
// Scores come from backend as 0–100. Bar width = score/100.
function ScoreCell({ score, max }) {
    const pct = max > 0 ? (score / max) * 100 : 0
    const display = typeof score === 'number' ? score.toFixed(1) : '—'
    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ flex: 1, height: 3, borderRadius: 3, background: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${pct}%`, background: '#60a5fa', borderRadius: 3, transition: 'width 0.5s ease' }} />
            </div>
            <span style={{ fontSize: 11, fontWeight: 700, color: '#60a5fa', minWidth: 36, textAlign: 'right' }}>{display}</span>
        </div>
    )
}

// ── Stat card ────────────────────────────────────────────────────────
function StatCard({ label, value, Icon, accent }) {
    return (
        <div style={{ borderRadius: 12, border: `1px solid ${accent ? 'rgba(239,68,68,0.2)' : 'rgba(255,255,255,0.07)'}`, background: accent ? 'rgba(239,68,68,0.06)' : 'rgba(255,255,255,0.025)', padding: '14px 16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                <span style={{ color: accent ? 'rgba(239,68,68,0.6)' : 'rgba(255,255,255,0.25)' }}><Icon /></span>
                <span style={{ fontSize: 10, fontWeight: 600, color: accent ? 'rgba(239,68,68,0.6)' : 'rgba(255,255,255,0.3)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{label}</span>
            </div>
            <span style={{ fontSize: 22, fontWeight: 700, color: accent ? 'rgb(248,113,113)' : 'rgba(255,255,255,0.88)', letterSpacing: '-0.02em' }}>{value}</span>
        </div>
    )
}

function RankingApp() {
    const {
        jdFile, setJdFile,
        candidateFile, setCandidateFile,
        topK, setTopK,
        loading, error, progress, results,
        setSelected,
        rankCandidates,
        downloadCSV,
        STEPS,
    } = useAppContext()

    const maxScore = results?.candidates?.[0]?.score ?? 100

    return (
        <>
            <style>{`
        @keyframes spin { to { transform: rotate(360deg) } }
        * { box-sizing: border-box }
        body { margin: 0 }
        ::-webkit-scrollbar { width: 4px; height: 4px }
        ::-webkit-scrollbar-track { background: transparent }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px }
        input[type=number]::-webkit-inner-spin-button { opacity: 0.3 }
        tr.row:hover td { background: rgba(255,255,255,0.025) }
        .dl-btn:hover { background: rgba(34,197,94,0.18) !important; border-color: rgba(34,197,94,0.4) !important; }
      `}</style>

            <div style={{ minHeight: '100vh', background: '#000', color: '#fff', fontFamily: '-apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", sans-serif' }}>

                {/* ── Navbar ── */}
                <nav style={{ position: 'sticky', top: 0, zIndex: 40, height: 52, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 24px', borderBottom: '1px solid rgba(255,255,255,0.06)', background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(16px)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div style={{ width: 26, height: 26, borderRadius: 8, background: 'rgba(96,165,250,0.15)', border: '1px solid rgba(96,165,250,0.25)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#60a5fa' }}>
                            <IconSpark />
                        </div>
                        <span style={{ fontSize: 13, fontWeight: 600, color: 'rgba(255,255,255,0.85)', letterSpacing: '-0.01em' }}>Redrob Hackathon v4</span>
                    </div>
                    <div style={{ display: 'flex', gap: 4 }}>
                        {['Docs', 'GitHub'].map((t) => (
                            <a key={t} href="#" style={{ padding: '5px 11px', borderRadius: 7, fontSize: 12, fontWeight: 500, color: 'rgba(255,255,255,0.4)', textDecoration: 'none', transition: 'all 0.15s' }}
                                onMouseEnter={(e) => { e.target.style.color = 'rgba(255,255,255,0.8)'; e.target.style.background = 'rgba(255,255,255,0.06)' }}
                                onMouseLeave={(e) => { e.target.style.color = 'rgba(255,255,255,0.4)'; e.target.style.background = 'transparent' }}>
                                {t}
                            </a>
                        ))}
                    </div>
                </nav>

                <main style={{ maxWidth: 640, margin: '0 auto', padding: '48px 20px 80px' }}>

                    {/* ── Hero ── */}
                    <div style={{ textAlign: 'center', marginBottom: 40 }}>
                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '4px 12px', borderRadius: 999, border: '1px solid rgba(96,165,250,0.2)', background: 'rgba(96,165,250,0.06)', marginBottom: 20 }}>
                            <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#60a5fa', animation: 'spin 2s linear infinite', animationTimingFunction: 'steps(8)' }} />
                            <span style={{ fontSize: 11, fontWeight: 600, color: '#60a5fa', letterSpacing: '0.05em' }}>AI-POWERED · TOP-10 FOCUSED</span>
                        </div>
                        <h1 style={{ margin: '0 0 14px', fontSize: 'clamp(28px, 5vw, 42px)', fontWeight: 700, letterSpacing: '-0.03em', lineHeight: 1.1, color: '#fff' }}>
                            AI Candidate<br /><span style={{ color: 'rgba(255,255,255,0.35)' }}>Ranking System</span>
                        </h1>
                        <p style={{ margin: 0, fontSize: 14, color: 'rgba(255,255,255,0.38)', lineHeight: 1.7, maxWidth: 400, marginLeft: 'auto', marginRight: 'auto' }}>
                            Feature-engineered, explainable, reproducible candidate ranking optimized for top-quality hiring.
                        </p>
                    </div>

                    {/* ── Upload Card ── */}
                    <div style={{ borderRadius: 18, border: '1px solid rgba(255,255,255,0.08)', background: 'rgba(255,255,255,0.02)', padding: 24, marginBottom: 16 }}>
                        <div style={{ marginBottom: 22 }}>
                            <h2 style={{ margin: '0 0 4px', fontSize: 14, fontWeight: 600, color: 'rgba(255,255,255,0.8)' }}>Configure ranking</h2>
                            <p style={{ margin: 0, fontSize: 12, color: 'rgba(255,255,255,0.3)' }}>Upload your JD and candidate pool to begin</p>
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                            <DropZone label="Job Description" accept=".pdf,.docx" hint="PDF or DOCX" file={jdFile} onFile={setJdFile} Icon={IconFile} />
                            <DropZone label="Candidate Dataset" accept=".jsonl,.json" hint="JSONL format" file={candidateFile} onFile={setCandidateFile} Icon={IconJson} />

                            {/* topK */}
                            <div>
                                <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'rgba(255,255,255,0.4)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 8 }}>
                                    Candidates to shortlist
                                </label>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                    <div style={{ position: 'relative', flex: 1 }}>
                                        <span style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'rgba(255,255,255,0.2)', display: 'flex' }}>
                                            <IconHash />
                                        </span>
                                        <input
                                            type="number" value={topK} min={1} max={1000} placeholder="100"
                                            onChange={(e) => setTopK(Math.max(1, Math.min(1000, Number(e.target.value))))}
                                            style={{ width: '100%', paddingLeft: 34, paddingRight: 14, paddingTop: 10, paddingBottom: 10, borderRadius: 10, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.8)', fontSize: 13, outline: 'none', transition: 'border-color 0.15s' }}
                                            onFocus={(e) => e.target.style.borderColor = 'rgba(96,165,250,0.4)'}
                                            onBlur={(e) => e.target.style.borderColor = 'rgba(255,255,255,0.08)'}
                                        />
                                    </div>
                                    <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.2)', whiteSpace: 'nowrap' }}>max 1,000</span>
                                </div>
                            </div>

                            {error && (
                                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, padding: '9px 12px', borderRadius: 9, background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)' }}>
                                    <span style={{ marginTop: 2 }}><IconX /></span>
                                    <span style={{ fontSize: 12, color: 'rgb(248,113,113)', lineHeight: 1.5 }}>{error}</span>
                                </div>
                            )}

                            <button
                                onClick={rankCandidates}
                                disabled={loading}
                                style={{ width: '100%', padding: '12px 0', borderRadius: 12, border: '1px solid rgba(96,165,250,0.3)', background: loading ? 'rgba(96,165,250,0.12)' : 'linear-gradient(135deg,#2563eb,#60a5fa)', color: '#fff', fontSize: 13, fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, boxShadow: loading ? 'none' : '0 0 24px rgba(96,165,250,0.18)', transition: 'all 0.2s', opacity: loading ? 0.7 : 1 }}>
                                {loading ? <><IconSpinner /> Ranking candidates…</> : <><IconUpload /> Rank candidates</>}
                            </button>
                        </div>
                    </div>

                    {/* ── Pipeline Progress ── */}
                    {progress !== null && (
                        <div style={{ borderRadius: 16, border: '1px solid rgba(255,255,255,0.07)', background: 'rgba(255,255,255,0.02)', padding: '18px 20px', marginBottom: 16 }}>
                            <p style={{ margin: '0 0 14px', fontSize: 10, fontWeight: 700, color: 'rgba(255,255,255,0.3)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>Pipeline</p>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                {STEPS.map((step, i) => {
                                    const done = i < progress
                                    const active = i === progress
                                    return (
                                        <div key={step} style={{ display: 'flex', alignItems: 'center', gap: 10, opacity: done || active ? 1 : 0.3, transition: 'opacity 0.3s' }}>
                                            <span style={{ color: done ? '#60a5fa' : active ? 'rgba(96,165,250,0.6)' : 'rgba(255,255,255,0.2)', display: 'flex', flexShrink: 0 }}>
                                                {done ? <IconCheck size={15} /> : active ? <IconSpinner /> : <IconCircle />}
                                            </span>
                                            <span style={{ fontSize: 13, color: done ? 'rgba(255,255,255,0.7)' : active ? 'rgba(255,255,255,0.55)' : 'rgba(255,255,255,0.25)' }}>
                                                {step}
                                            </span>
                                        </div>
                                    )
                                })}
                            </div>
                        </div>
                    )}

                    {/* ── Results ── */}
                    {results && (
                        <>
                            {results.message && results.candidates.length === 0 && (
                                <div style={{ borderRadius: 14, border: '1px solid rgba(255,255,255,0.08)', background: 'rgba(255,255,255,0.02)', padding: '16px 18px', marginBottom: 16 }}>
                                    <p style={{ margin: 0, fontSize: 13, color: 'rgba(255,255,255,0.5)' }}>{results.message}</p>
                                </div>
                            )}

                            {/* ── Stats grid (2×3) ── */}
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10, marginBottom: 16 }}>
                                <StatCard label="Total"           value={results.total_candidates?.toLocaleString() ?? '—'}           Icon={IconUsers}  />
                                <StatCard label="Above Threshold" value={results.candidates_above_threshold?.toLocaleString() ?? '—'} Icon={IconClock}  />
                                <StatCard label="Ranked"          value={results.ranked?.toLocaleString() ?? '—'}                     Icon={IconAward}  />
                                <StatCard label="Skipped"         value={results.candidates_skipped?.toLocaleString() ?? '—'}         Icon={IconShield} />
                                <StatCard
                                    label="Honeypots Removed"
                                    value={results.honeypots_removed?.toLocaleString() ?? '0'}
                                    Icon={IconX}
                                    accent={results.honeypots_removed > 0}
                                />
                                {/* empty cell to keep grid even */}
                                <div />
                            </div>

                            {/* ── Table + download header ── */}
                            {results.candidates?.length > 0 && (
                                <div style={{ borderRadius: 16, border: '1px solid rgba(255,255,255,0.08)', overflow: 'hidden' }}>
                                    {/* table header row with download button */}
                                    <div style={{ padding: '12px 18px', borderBottom: '1px solid rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                        <div>
                                            <p style={{ margin: 0, fontSize: 12, fontWeight: 600, color: 'rgba(255,255,255,0.5)' }}>
                                                Top {results.candidates.length} candidates
                                            </p>
                                            <p style={{ margin: '2px 0 0', fontSize: 11, color: 'rgba(255,255,255,0.22)' }}>
                                                Click a row for full profile
                                            </p>
                                        </div>
                                        <button
                                            className="dl-btn"
                                            onClick={downloadCSV}
                                            style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '7px 14px', borderRadius: 9, border: '1px solid rgba(34,197,94,0.25)', background: 'rgba(34,197,94,0.08)', color: 'rgb(134,239,172)', fontSize: 12, fontWeight: 600, cursor: 'pointer', transition: 'all 0.15s' }}>
                                            <IconDownload />
                                            Export CSV
                                        </button>
                                    </div>

                                    <div style={{ maxHeight: 480, overflowY: 'auto' }}>
                                        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                            <thead style={{ position: 'sticky', top: 0, background: '#050505', zIndex: 1 }}>
                                                <tr>
                                                    {['#', 'Candidate', 'Role', 'Score', 'Skills'].map((h) => (
                                                        <th key={h} style={{ padding: '10px 14px', textAlign: 'left', fontSize: 10, fontWeight: 700, color: 'rgba(255,255,255,0.3)', textTransform: 'uppercase', letterSpacing: '0.08em', borderBottom: '1px solid rgba(255,255,255,0.06)', whiteSpace: 'nowrap' }}>{h}</th>
                                                    ))}
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {results.candidates.map((c, i) => (
                                                    <tr key={c.id ?? i} className="row" onClick={() => setSelected(c)} style={{ cursor: 'pointer', transition: 'background 0.1s' }}>
                                                        {/* rank */}
                                                        <td style={{ padding: '11px 14px', borderBottom: '1px solid rgba(255,255,255,0.04)', fontSize: 11, fontWeight: 700, color: 'rgba(255,255,255,0.25)', whiteSpace: 'nowrap' }}>
                                                            {i < 3
                                                                ? ['🥇', '🥈', '🥉'][i]
                                                                : `#${i + 1}`}
                                                        </td>
                                                        {/* candidate id + availability */}
                                                        <td style={{ padding: '11px 14px', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                                                            <div style={{ fontSize: 12, fontWeight: 600, color: 'rgba(255,255,255,0.75)' }}>{c.id}</div>
                                                            <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.28)', marginTop: 2 }}>
                                                                {c.availability !== '—' ? `${c.availability} notice` : 'notice unknown'}
                                                            </div>
                                                        </td>
                                                        {/* title + experience */}
                                                        <td style={{ padding: '11px 14px', borderBottom: '1px solid rgba(255,255,255,0.04)', maxWidth: 160 }}>
                                                            <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.6)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{c.title}</div>
                                                            <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.28)', marginTop: 2 }}>{c.experience}</div>
                                                        </td>
                                                        {/* score bar */}
                                                        <td style={{ padding: '11px 14px', borderBottom: '1px solid rgba(255,255,255,0.04)', minWidth: 120 }}>
                                                            <ScoreCell score={c.score} max={maxScore} />
                                                        </td>
                                                        {/* top 3 skills */}
                                                        <td style={{ padding: '11px 14px', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                                                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                                                                {c.skills.slice(0, 3).map((sk) => (
                                                                    <span key={sk} style={{ padding: '2px 7px', borderRadius: 5, background: 'rgba(96,165,250,0.1)', border: '1px solid rgba(96,165,250,0.15)', fontSize: 10, color: 'rgba(96,165,250,0.7)', whiteSpace: 'nowrap' }}>{sk}</span>
                                                                ))}
                                                                {c.skills.length > 3 && (
                                                                    <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.2)', alignSelf: 'center' }}>+{c.skills.length - 3}</span>
                                                                )}
                                                            </div>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            )}
                        </>
                    )}
                </main>

                {/* ── Footer ── */}
                <footer style={{ borderTop: '1px solid rgba(255,255,255,0.06)', padding: '24px 20px', textAlign: 'center' }}>
                    <p style={{ margin: '0 0 10px', fontSize: 11, color: 'rgba(255,255,255,0.2)' }}>Built for Redrob Hackathon v4</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: 8 }}>
                        {['CPU-only', 'Reproducible', 'Explainable', 'Feature Engineering'].map((t) => (
                            <span key={t} style={{ padding: '3px 10px', borderRadius: 999, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)', fontSize: 11, color: 'rgba(255,255,255,0.25)' }}>{t}</span>
                        ))}
                    </div>
                </footer>
            </div>

            <CandidateModal />
        </>
    )
}

export default function App() {
    return (
        <AppProvider>
            <RankingApp />
        </AppProvider>
    )
}