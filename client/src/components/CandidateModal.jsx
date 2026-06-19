import React, { useEffect } from 'react'
import { useAppContext } from '../context/AppContext'
import { IconX, IconAward, IconFile, IconClock } from './icons'

export default function CandidateModal() {
  const { selected, setSelected } = useAppContext()

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setSelected(null)
      }
    }
    if (selected) {
      window.addEventListener('keydown', handleKeyDown)
    }
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [selected, setSelected])

  if (!selected) return null

  const handleClose = () => setSelected(null)

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 20,
        background: 'rgba(0,0,0,0.6)',
        backdropFilter: 'blur(4px)',
        animation: 'fadeIn 0.2s ease',
      }}
      onClick={handleClose}
    >
      <style>{`
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes scaleIn { from { transform: scale(0.95); opacity: 0; } to { transform: scale(1); opacity: 1; } }
      `}</style>
      
      <div
        style={{
          width: '100%',
          maxWidth: 600,
          maxHeight: '90vh',
          background: '#0a0a0a',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: 16,
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)',
          animation: 'scaleIn 0.2s ease',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ padding: '20px 24px', borderBottom: '1px solid rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(255,255,255,0.02)' }}>
          <div>
            <h2 style={{ margin: '0 0 4px', fontSize: 18, fontWeight: 600, color: '#fff' }}>Candidate Details</h2>
            <p style={{ margin: 0, fontSize: 13, color: 'rgba(255,255,255,0.5)' }}>ID: {selected.id}</p>
          </div>
          <button
            onClick={handleClose}
            style={{ width: 32, height: 32, borderRadius: 8, background: 'rgba(255,255,255,0.05)', border: 'none', color: 'rgba(255,255,255,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', transition: 'all 0.2s' }}
            onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.1)'; e.currentTarget.style.color = '#fff' }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.05)'; e.currentTarget.style.color = 'rgba(255,255,255,0.6)' }}
          >
            <IconX />
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: 24, overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: 20 }}>
          
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16 }}>
            <div style={{ width: 48, height: 48, borderRadius: 12, background: 'rgba(96,165,250,0.1)', border: '1px solid rgba(96,165,250,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#60a5fa', flexShrink: 0 }}>
              <IconAward size={24} />
            </div>
            <div>
              <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600, marginBottom: 4 }}>Match Score</div>
              <div style={{ fontSize: 32, fontWeight: 700, color: '#60a5fa', lineHeight: 1 }}>
                {typeof selected.score === 'number' ? (selected.score).toFixed(1) : '—'}
                <span style={{ fontSize: 16, fontWeight: 500, color: 'rgba(96,165,250,0.5)', marginLeft: 4 }}>/ 100</span>
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
             <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 10, padding: 12 }}>
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600, marginBottom: 6 }}>Title/Role</div>
                <div style={{ fontSize: 14, color: 'rgba(255,255,255,0.85)' }}>{selected.title || '—'}</div>
             </div>
             <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 10, padding: 12 }}>
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600, marginBottom: 6 }}>Experience</div>
                <div style={{ fontSize: 14, color: 'rgba(255,255,255,0.85)' }}>{selected.experience || '—'}</div>
             </div>
          </div>

          <div>
            <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
              <IconFile size={14} /> Reasoning
            </div>
            <div style={{ background: 'rgba(96,165,250,0.05)', border: '1px solid rgba(96,165,250,0.15)', borderRadius: 12, padding: 16, fontSize: 13, color: 'rgba(255,255,255,0.8)', lineHeight: 1.6 }}>
              {selected.reasoning || 'No explanation provided.'}
            </div>
          </div>

          {Array.isArray(selected.skills) && selected.skills.length > 0 && (
            <div>
              <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600, marginBottom: 10 }}>Matched Skills</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {selected.skills.map((skill, idx) => (
                  <span key={idx} style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', padding: '4px 10px', borderRadius: 999, fontSize: 12, color: 'rgba(255,255,255,0.8)' }}>
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div>
             <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
              <IconClock size={14} /> Availability
            </div>
            <div style={{ fontSize: 14, color: 'rgba(255,255,255,0.85)' }}>{selected.availability || '—'}</div>
          </div>

        </div>
      </div>
    </div>
  )
}
