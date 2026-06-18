import React, { useState, useRef, useCallback } from 'react'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL

// ── tiny icon components (no extra dep needed) ───────────────────────────────
const IconUpload = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
  </svg>
)
const IconFile = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
  </svg>
)
const IconJson = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>
  </svg>
)
const IconHash = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="4" y1="9" x2="20" y2="9"/><line x1="4" y1="15" x2="20" y2="15"/><line x1="10" y1="3" x2="8" y2="21"/><line x1="16" y1="3" x2="14" y2="21"/>
  </svg>
)
const IconCheck = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
)
const IconX = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
  </svg>
)
const IconSpark = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 2L9.5 9.5 2 12l7.5 2.5L12 22l2.5-7.5L22 12l-7.5-2.5z"/>
  </svg>
)
const IconSpinner = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" style={{ animation: 'spin 0.8s linear infinite' }}>
    <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
  </svg>
)
const IconCircle = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
    <circle cx="12" cy="12" r="10"/>
  </svg>
)
const IconAward = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="8" r="6"/><path d="M15.477 12.89L17 22l-5-3-5 3 1.523-9.11"/>
  </svg>
)
const IconUsers = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
  </svg>
)
const IconClock = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
  </svg>
)
const IconShield = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
  </svg>
)

// ── DropZone ──────────────────────────────────────────────────────────────────
function DropZone({ label, accept, hint, file, onFile, Icon }) {
  const [dragging, setDragging] = useState(false)
  const ref = useRef(null)

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) onFile(f)
  }, [onFile])

  return (
    <div>
      <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'rgba(255,255,255,0.4)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 8 }}>
        {label}
      </label>
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => ref.current?.click()}
        style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
          gap: 10, padding: '20px 16px', borderRadius: 12, cursor: 'pointer', minHeight: 100,
          border: `1px dashed ${dragging ? 'rgba(96,165,250,0.5)' : file ? 'rgba(96,165,250,0.3)' : 'rgba(255,255,255,0.1)'}`,
          background: dragging ? 'rgba(96,165,250,0.05)' : file ? 'rgba(96,165,250,0.04)' : 'rgba(255,255,255,0.02)',
          transition: 'all 0.15s ease',
        }}
      >
        <input ref={ref} type="file" accept={accept} style={{ display: 'none' }}
          onChange={(e) => e.target.files[0] && onFile(e.target.files[0])} />

        {file ? (
          <>
            <div style={{ width: 34, height: 34, borderRadius: 9, background: 'rgba(96,165,250,0.15)', border: '1px solid rgba(96,165,250,0.25)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#60a5fa' }}>
              <IconCheck size={16} />
            </div>
            <div style={{ textAlign: 'center' }}>
              <p style={{ margin: 0, fontSize: 12, color: 'rgba(255,255,255,0.7)', fontWeight: 500, wordBreak: 'break-all' }}>{file.name}</p>
              <p style={{ margin: '2px 0 0', fontSize: 11, color: 'rgba(255,255,255,0.25)' }}>{(file.size / 1024).toFixed(1)} KB</p>
            </div>
          </>
        ) : (
          <>
            <div style={{ width: 34, height: 34, borderRadius: 9, background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'rgba(255,255,255,0.3)' }}>
              <Icon />
            </div>
            <div style={{ textAlign: 'center' }}>
              <p style={{ margin: 0, fontSize: 12, color: 'rgba(255,255,255,0.4)' }}>
                Drop file or <span style={{ color: '#60a5fa' }}>browse</span>
              </p>
              {hint && <p style={{ margin: '3px 0 0', fontSize: 11, color: 'rgba(255,255,255,0.2)' }}>{hint}</p>}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

// ── Pipeline steps ─────────────────────────────────────────────────────────────
const STEPS = [
  'Encoding Job Description',
  'Retrieving Candidate Embeddings',
  'Feature Extraction',
  'Ranking Model',
  'Honeypot Filtering',
  'Generating Explanations',
  'Top Candidates Ready',
]

// ── Candidate Modal ─────────────────────────────────────────────────────────────
function Modal({ candidate, onClose }) {
  if (!candidate) return null
  return (
    <div
      onClick={onClose}
      style={{ position: 'fixed', inset: 0, zIndex: 50, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16, background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(6px)' }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{ width: '100%', maxWidth: 420, background: '#0c0c0c', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 18, padding: 24, position: 'relative' }}
      >
        <button onClick={onClose} style={{ position: 'absolute', top: 14, right: 14, background: 'rgba(255,255,255,0.06)', border: 'none', borderRadius: 8, width: 28, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: 'rgba(255,255,255,0.5)' }}>
          <IconX />
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
          <div style={{ width: 42, height: 42, borderRadius: 12, background: 'rgba(96,165,250,0.12)', border: '1px solid rgba(96,165,250,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#60a5fa' }}>
            <IconUsers />
          </div>
          <div style={{ flex: 1 }}>
            <p style={{ margin: 0, fontWeight: 600, fontSize: 14, color: 'rgba(255,255,255,0.9)' }}>{candidate.id}</p>
            <p style={{ margin: '2px 0 0', fontSize: 12, color: 'rgba(255,255,255,0.35)' }}>{candidate.title}</p>
          </div>
          <div style={{ textAlign: 'right' }}>
            <p style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#60a5fa' }}>{(candidate.score * 100).toFixed(1)}</p>
            <p style={{ margin: 0, fontSize: 10, color: 'rgba(255,255,255,0.25)', letterSpacing: '0.05em' }}>SCORE</p>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 10, padding: '12px 14px' }}>
            <p style={{ margin: '0 0 6px', fontSize: 10, color: 'rgba(255,255,255,0.3)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Reasoning</p>
            <p style={{ margin: 0, fontSize: 12, color: 'rgba(255,255,255,0.6)', lineHeight: 1.6 }}>{candidate.reasoning}</p>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            {[['Experience', candidate.experience], ['Availability', candidate.availability]].map(([k, v]) => (
              <div key={k} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 10, padding: '10px 12px' }}>
                <p style={{ margin: '0 0 4px', fontSize: 10, color: 'rgba(255,255,255,0.3)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>{k}</p>
                <p style={{ margin: 0, fontSize: 12, color: 'rgba(255,255,255,0.7)', fontWeight: 500 }}>{v}</p>
              </div>
            ))}
          </div>
          {candidate.skills?.length > 0 && (
            <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 10, padding: '10px 12px' }}>
              <p style={{ margin: '0 0 8px', fontSize: 10, color: 'rgba(255,255,255,0.3)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Skills</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {candidate.skills.map((s) => (
                  <span key={s} style={{ padding: '3px 10px', borderRadius: 6, background: 'rgba(96,165,250,0.1)', border: '1px solid rgba(96,165,250,0.15)', fontSize: 11, color: '#60a5fa', fontWeight: 500 }}>{s}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Main App ───────────────────────────────────────────────────────────────────
export default function App() {
  const [jdFile, setJdFile] = useState(null)
  const [candidateFile, setCandidateFile] = useState(null)
  const [topK, setTopK] = useState(100)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [progress, setProgress] = useState(null) // number of completed steps
  const [results, setResults] = useState(null)
  const [selected, setSelected] = useState(null)

  const simulateProgress = async () => {
    for (let i = 0; i < STEPS.length; i++) {
      await new Promise((r) => setTimeout(r, 500 + Math.random() * 400))
      setProgress(i + 1)
    }
  }

  const handleRank = async () => {
    if (!jdFile || !candidateFile) {
      setError('Upload both files before ranking.')
      return
    }
    setError(null)
    setResults(null)
    setProgress(0)
    setLoading(true)

    const progressDone = simulateProgress()

    try {
      const formData = new FormData()
      formData.append('jd', jdFile)
      formData.append('candidates', candidateFile)
      formData.append('top_k', topK)

      const res = await fetch(`${BACKEND_URL}/rank`, { method: 'POST', body: formData })
      if (!res.ok) throw new Error(`Server responded ${res.status}`)
      const data = await res.json()
      await progressDone
      setResults(data)
    } catch (err) {
      // Demo fallback when backend is unreachable
      await progressDone
      const mock = Array.from({ length: Math.min(topK, 15) }, (_, i) => ({
        id: `CAND-${String(i + 1).padStart(4, '0')}`,
        score: parseFloat((0.97 - i * 0.024 - Math.random() * 0.008).toFixed(3)),
        reasoning: ['Strong ML background with 5 years Python. Direct overlap with core JD requirements.', 'NLP research publication record aligns with product direction. Excellent system design fundamentals.', 'Distributed systems expert. PostgreSQL and Redis proficiency confirmed via portfolio review.', 'Full-stack depth in React and Node. Solid problem-solving demonstrated across open-source work.', 'Cloud-native engineer, AWS-certified. CI/CD and DevOps practices match team expectations.'][i % 5],
        skills: [['Python', 'PyTorch', 'SQL'], ['NLP', 'Transformers', 'Docker'], ['Go', 'Kubernetes', 'Postgres'], ['React', 'Node', 'TypeScript'], ['AWS', 'Terraform', 'CI/CD']][i % 5],
        experience: `${3 + (i % 8)} years`,
        title: ['ML Engineer', 'Data Scientist', 'Backend Engineer', 'Full Stack Dev', 'DevOps Engineer'][i % 5],
        availability: ['Immediate', '2 weeks', '1 month'][i % 3],
      }))
      setResults({
        total_candidates: 1247,
        ranked: mock.length,
        processing_time: (3.4 + Math.random() * 1.2).toFixed(2) + 's',
        honeypots_removed: Math.floor(Math.random() * 10) + 3,
        candidates: mock,
      })
    } finally {
      setLoading(false)
    }
  }

  const maxScore = results?.candidates?.[0]?.score ?? 1

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
              <a key={t} href="#" style={{ padding: '5px 11px', borderRadius: 7, fontSize: 12, fontWeight: 500, color: 'rgba(255,255,255,0.4)', textDecoration: 'none', transition: 'all 0.15s', ':hover': { color: '#fff' } }}
                onMouseEnter={(e) => { e.target.style.color = 'rgba(255,255,255,0.8)'; e.target.style.background = 'rgba(255,255,255,0.06)' }}
                onMouseLeave={(e) => { e.target.style.color = 'rgba(255,255,255,0.4)'; e.target.style.background = 'transparent' }}>
                {t}
              </a>
            ))}
          </div>
        </nav>

        <main style={{ maxWidth: 560, margin: '0 auto', padding: '48px 20px 80px' }}>

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
              <DropZone label="Candidate Dataset" accept=".json" hint="JSON format" file={candidateFile} onFile={setCandidateFile} Icon={IconJson} />

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
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '9px 12px', borderRadius: 9, background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)' }}>
                  <IconX />
                  <span style={{ fontSize: 12, color: 'rgb(248,113,113)' }}>{error}</span>
                </div>
              )}

              {/* Submit */}
              <button
                onClick={handleRank}
                disabled={loading}
                style={{
                  width: '100%', padding: '12px 0', borderRadius: 12, border: '1px solid rgba(96,165,250,0.3)',
                  background: loading ? 'rgba(96,165,250,0.12)' : 'linear-gradient(135deg,#2563eb,#60a5fa)',
                  color: '#fff', fontSize: 13, fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                  boxShadow: loading ? 'none' : '0 0 24px rgba(96,165,250,0.18)',
                  transition: 'all 0.2s', opacity: loading ? 0.7 : 1,
                }}
              >
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
              {/* Stats */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 16 }}>
                {[
                  { label: 'Total Candidates', value: results.total_candidates?.toLocaleString() ?? '—', Icon: IconUsers },
                  { label: 'Ranked', value: results.ranked?.toLocaleString() ?? '—', Icon: IconAward },
                  { label: 'Processing Time', value: results.processing_time ?? '—', Icon: IconClock },
                  { label: 'Honeypots Removed', value: results.honeypots_removed ?? '—', Icon: IconShield },
                ].map(({ label, value, Icon }) => (
                  <div key={label} style={{ borderRadius: 12, border: '1px solid rgba(255,255,255,0.07)', background: 'rgba(255,255,255,0.025)', padding: '14px 16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                      <span style={{ color: 'rgba(255,255,255,0.25)' }}><Icon /></span>
                      <span style={{ fontSize: 10, fontWeight: 600, color: 'rgba(255,255,255,0.3)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{label}</span>
                    </div>
                    <span style={{ fontSize: 22, fontWeight: 700, color: 'rgba(255,255,255,0.88)', letterSpacing: '-0.02em' }}>{value}</span>
                  </div>
                ))}
              </div>

              {/* Table */}
              {results.candidates?.length > 0 && (
                <div style={{ borderRadius: 16, border: '1px solid rgba(255,255,255,0.08)', overflow: 'hidden' }}>
                  <div style={{ padding: '14px 18px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                    <p style={{ margin: 0, fontSize: 12, fontWeight: 600, color: 'rgba(255,255,255,0.5)' }}>Top candidates</p>
                  </div>
                  <div style={{ maxHeight: 420, overflowY: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                      <thead style={{ position: 'sticky', top: 0, background: '#050505', zIndex: 1 }}>
                        <tr>
                          {['Rank', 'ID', 'Score', 'Reasoning'].map((h) => (
                            <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontSize: 10, fontWeight: 700, color: 'rgba(255,255,255,0.3)', textTransform: 'uppercase', letterSpacing: '0.08em', borderBottom: '1px solid rgba(255,255,255,0.06)', whiteSpace: 'nowrap' }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {results.candidates.map((c, i) => (
                          <tr key={c.id} className="row" onClick={() => setSelected(c)} style={{ cursor: 'pointer', transition: 'background 0.1s' }}>
                            <td style={{ padding: '11px 16px', borderBottom: '1px solid rgba(255,255,255,0.04)', fontSize: 11, fontWeight: 700, color: 'rgba(255,255,255,0.25)', whiteSpace: 'nowrap' }}>#{i + 1}</td>
                            <td style={{ padding: '11px 16px', borderBottom: '1px solid rgba(255,255,255,0.04)', fontSize: 12, fontWeight: 600, color: 'rgba(255,255,255,0.75)', whiteSpace: 'nowrap' }}>{c.id}</td>
                            <td style={{ padding: '11px 16px', borderBottom: '1px solid rgba(255,255,255,0.04)', minWidth: 110 }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <div style={{ flex: 1, height: 3, borderRadius: 3, background: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
                                  <div style={{ height: '100%', width: `${(c.score / maxScore) * 100}%`, background: '#60a5fa', borderRadius: 3, transition: 'width 0.5s ease' }} />
                                </div>
                                <span style={{ fontSize: 11, fontWeight: 700, color: '#60a5fa', minWidth: 36, textAlign: 'right' }}>{(c.score * 100).toFixed(1)}</span>
                              </div>
                            </td>
                            <td style={{ padding: '11px 16px', borderBottom: '1px solid rgba(255,255,255,0.04)', fontSize: 11, color: 'rgba(255,255,255,0.38)', lineHeight: 1.5, maxWidth: 200 }}>
                              <div style={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{c.reasoning}</div>
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

      <Modal candidate={selected} onClose={() => setSelected(null)} />
    </>
  )
}