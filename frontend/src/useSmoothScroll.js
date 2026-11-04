import { useEffect } from 'react'

// Rolagem por seções na página inicial (inspirada no exemplo enviado):
// cada giro da rodinha leva a página até a próxima seção, num movimento
// que começa devagar, acelera e desacelera até parar alinhado no topo.
const DURATION = 950 // ms
const easeInOutCubic = (t) => (t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2)

/**
 * - Rodinha do mouse: cada giro leva à próxima seção.
 * - Touchpad: cada deslize com dois dedos leva à próxima seção; o "embalo"
 *   que o touchpad continua mandando depois do deslize é ignorado.
 * - Celular (toque): rolagem nativa do aparelho.
 * - A opção "Remover animações" do painel de acessibilidade desliga o efeito.
 * - Com "reduzir movimento" ativado no sistema, a rolagem fica normal.
 * - Seções mais altas que a tela são percorridas em etapas, sem pular conteúdo.
 * - Teclado (setas, Page Down, espaço) continua com a rolagem normal.
 * - Links #historia, #bastidores e #topo deslizam com o mesmo movimento.
 */
export default function useSmoothScroll() {
  useEffect(() => {
    if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return undefined

    let animating = false
    let frame = 0
    let lastWheelAt = 0
    let gestureMode = null // 'mouse' | 'touchpad' — decidido no início de cada gesto
    let gestureStepped = false // touchpad: este deslize já gerou um passo?
    let accumulated = 0 // touchpad: quanto o deslize andou antes de virar passo
    let lastAbs = 0 // touchpad: intensidade do último evento (para perceber um novo deslize)
    let animationEndedAt = 0

    const motionDisabled = () => document.documentElement.dataset.reduceMotion === 'true'

    // Um gesto termina quando a roda/touchpad fica parado por este tempo.
    const GESTURE_IDLE = 250

    // Decidido só pelo PRIMEIRO evento do gesto: a rodinha começa com um "degrau"
    // grande e inteiro (ex.: 100, 120) ou usa o modo de linhas; o touchpad começa
    // com movimentos pequenos/fracionados. O gesto inteiro mantém a decisão, para
    // nunca alternar entre animação e rolagem nativa no meio (o que dá trancos).
    function classify(event) {
      if (event.deltaMode !== 0) return 'mouse'
      const dy = Math.abs(event.deltaY)
      if (Number.isInteger(event.deltaY) && dy >= 50 && event.deltaX === 0) return 'mouse'
      return 'touchpad'
    }

    function maxScroll() {
      return document.documentElement.scrollHeight - window.innerHeight
    }

    function snapPoints() {
      const sections = document.querySelectorAll('.landing main > section, .landing-footer')
      const points = [0, ...[...sections].map((el) => Math.round(el.getBoundingClientRect().top + window.scrollY)), maxScroll()]
      return [...new Set(points.map((p) => Math.min(Math.max(p, 0), maxScroll())))].sort((a, b) => a - b)
    }

    function animateTo(target) {
      cancelAnimationFrame(frame)
      const start = window.scrollY
      const distance = target - start
      if (Math.abs(distance) < 2) return
      const startedAt = performance.now()
      animating = true
      const step = (now) => {
        const progress = Math.min((now - startedAt) / DURATION, 1)
        window.scrollTo({ top: start + distance * easeInOutCubic(progress), behavior: 'instant' })
        if (progress < 1) frame = requestAnimationFrame(step)
        else {
          animating = false
          animationEndedAt = performance.now()
        }
      }
      frame = requestAnimationFrame(step)
    }

    function nextTarget(direction) {
      const current = window.scrollY
      const viewport = window.innerHeight
      const points = snapPoints()
      // Paradas muito próximas (menos de 1/4 da tela) são puladas, para não dar "passinhos".
      const minStep = viewport * 0.25
      if (direction > 0) {
        const next = points.find((p) => p > current + minStep) ?? maxScroll()
        // Seção mais alta que a tela: avança no máximo uma tela por vez.
        return Math.min(next, current + viewport, maxScroll())
      }
      const previous = [...points].reverse().find((p) => p < current - minStep) ?? 0
      return Math.max(previous, current - viewport, 0)
    }

    function handleWheel(event) {
      if (event.ctrlKey) return // zoom do navegador
      if (event.target.closest?.('.a11y-widget')) return // painel de acessibilidade rola normalmente
      if (motionDisabled()) return
      if (Math.abs(event.deltaX) > Math.abs(event.deltaY) || event.deltaY === 0) return

      const now = performance.now()
      const newGesture = now - lastWheelAt > GESTURE_IDLE
      lastWheelAt = now
      if (newGesture || !gestureMode) {
        gestureMode = classify(event)
        gestureStepped = false
        accumulated = 0
        lastAbs = 0
      }

      if (gestureMode === 'touchpad') {
        event.preventDefault()
        const abs = Math.abs(event.deltaY)
        // Novo deslize emendado no embalo do anterior: o embalo só diminui,
        // então um aumento forte de intensidade depois da animação é um novo gesto.
        if (gestureStepped && !animating && now - animationEndedAt > 120 && abs > 12 && abs > lastAbs * 1.8) {
          gestureStepped = false
          accumulated = 0
        }
        lastAbs = abs
        if (gestureStepped || animating) return
        accumulated += event.deltaY
        // Pequenos toques sem intenção não viram passo.
        if (Math.abs(accumulated) < 24) return
        gestureStepped = true
        animateTo(nextTarget(Math.sign(accumulated)))
        return
      }

      // Rodinha: um passo por vez. Giros durante a animação são ignorados;
      // se a pessoa continuar girando depois que ela termina, segue para a próxima seção.
      event.preventDefault()
      if (animating) return
      animateTo(nextTarget(Math.sign(event.deltaY)))
    }

    function handleClick(event) {
      if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return
      const link = event.target.closest?.('a[href^="#"]')
      if (!link) return
      const hash = link.getAttribute('href')
      const target = hash.length > 1 ? document.getElementById(decodeURIComponent(hash.slice(1))) : null
      if (!target) return // ex.: #login segue o comportamento normal
      if (motionDisabled()) return // vai direto à seção, sem animação
      event.preventDefault()
      const top = hash === '#topo' ? 0 : target.getBoundingClientRect().top + window.scrollY
      animateTo(Math.min(Math.max(Math.round(top), 0), maxScroll()))
      if (location.hash !== hash) history.pushState(null, '', hash)
    }

    function stopAnimation() {
      // Teclado interrompe a animação em andamento e assume a rolagem normal.
      cancelAnimationFrame(frame)
      animating = false
    }

    window.addEventListener('wheel', handleWheel, { passive: false })
    document.addEventListener('click', handleClick)
    window.addEventListener('keydown', stopAnimation)

    return () => {
      cancelAnimationFrame(frame)
      window.removeEventListener('wheel', handleWheel)
      document.removeEventListener('click', handleClick)
      window.removeEventListener('keydown', stopAnimation)
    }
  }, [])
}
