import { useEffect, useId, useRef, useState } from 'react'
import AccessibilityControls from './AccessibilityControls.jsx'
import './AccessibilityWidget.css'

function AccessibilityIcon() {
  return (
    <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="10.25" />
      <circle cx="12" cy="6.9" r="1.35" fill="currentColor" stroke="none" />
      <path d="M6.9 9.6 12 10.6l5.1-1" />
      <path d="M12 10.6v3.3" />
      <path d="m9.4 18.2 2.6-4.3 2.6 4.3" />
    </svg>
  )
}

/** Botão flutuante que dá acesso às preferências de acessibilidade em qualquer tela. */
export default function AccessibilityWidget() {
  const [open, setOpen] = useState(false)
  const buttonRef = useRef(null)
  const panelRef = useRef(null)
  const titleId = useId()
  const panelId = useId()

  useEffect(() => {
    if (!open) return undefined
    panelRef.current?.focus()

    function handleKeyDown(event) {
      if (event.key === 'Escape') {
        setOpen(false)
        buttonRef.current?.focus()
      }
    }
    function handlePointerDown(event) {
      if (panelRef.current?.contains(event.target) || buttonRef.current?.contains(event.target)) return
      setOpen(false)
    }
    document.addEventListener('keydown', handleKeyDown)
    document.addEventListener('pointerdown', handlePointerDown)
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.removeEventListener('pointerdown', handlePointerDown)
    }
  }, [open])

  function close() {
    setOpen(false)
    buttonRef.current?.focus()
  }

  return (
    <div className="a11y-widget">
      {open && (
        <div
          ref={panelRef}
          id={panelId}
          className="a11y-widget-panel"
          role="dialog"
          aria-labelledby={titleId}
          tabIndex={-1}
        >
          <div className="a11y-widget-heading">
            <div>
              <span className="eyebrow">ACESSIBILIDADE</span>
              <h2 id={titleId}>Do seu jeito, com mais conforto.</h2>
            </div>
            <button type="button" className="a11y-widget-close" onClick={close} aria-label="Fechar acessibilidade">×</button>
          </div>
          <AccessibilityControls />
        </div>
      )}
      <button
        ref={buttonRef}
        type="button"
        className="a11y-widget-button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-controls={open ? panelId : undefined}
        aria-label="Acessibilidade"
        title="Acessibilidade"
      >
        <AccessibilityIcon />
      </button>
    </div>
  )
}
