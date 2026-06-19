import React, { useState, useRef, useCallback } from 'react'

const IconCheck = ({ size = 16 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="20 6 9 17 4 12" />
    </svg>
)

export default function DropZone({ label, accept, hint, file, onFile, Icon }) {
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