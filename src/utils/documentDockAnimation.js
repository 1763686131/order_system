const runningAnimations = new Set()

export function cancelDocumentDockAnimations() {
  for (const animation of runningAnimations) animation.cancel()
}

export function waitForDocumentReady(element) {
  if (element.getAttribute('aria-busy') !== 'true') return Promise.resolve()
  return new Promise(resolve => {
    let timer
    const finish = () => { clearTimeout(timer); observer.disconnect(); resolve() }
    const observer = new MutationObserver(() => {
      if (element.getAttribute('aria-busy') !== 'true') finish()
    })
    observer.observe(element, { attributes: true, attributeFilter: ['aria-busy'] })
    timer = setTimeout(finish, 1500)
  })
}

export async function animateDocumentDock(element, targetRect, restoring = false) {
  if (!targetRect || !element.animate || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  const rect = element.getBoundingClientRect()
  if (!rect.width || !rect.height) return
  const snapshot = element.cloneNode(true)
  snapshot.classList.add('document-dock-snapshot')
  snapshot.setAttribute('aria-hidden', 'true')
  snapshot.inert = true
  snapshot.removeAttribute('id')
  snapshot.querySelectorAll('[id]').forEach(node => node.removeAttribute('id'))
  const originalInputs = element.querySelectorAll('input, select, textarea')
  snapshot.querySelectorAll('input, select, textarea').forEach((input, index) => {
    input.value = originalInputs[index].value
    if (input.type === 'checkbox') input.checked = originalInputs[index].checked
  })
  Object.assign(snapshot.style, {
    position: 'fixed', left: `${rect.left}px`, top: `${rect.top}px`, width: `${rect.width}px`,
    height: `${rect.height}px`, margin: '0', zIndex: '3000', pointerEvents: 'none', overflow: 'hidden',
    visibility: 'visible', transformOrigin: '0 0', willChange: 'transform, opacity'
  })
  document.body.appendChild(snapshot)
  const dx = targetRect.left - rect.left
  const dy = targetRect.top - rect.top
  const scaleX = targetRect.width / rect.width
  const scaleY = targetRect.height / rect.height
  const frames = [
    { transform: 'translate(0, 0) scale(1, 1)', opacity: 1, borderRadius: '6px' },
    { transform: `translate(${dx * .65}px, ${dy * .65}px) scale(.55, .6)`, opacity: .85, borderRadius: '12px', offset: .55 },
    { transform: `translate(${dx}px, ${dy}px) scale(${scaleX}, ${scaleY})`, opacity: .12, borderRadius: '16px' }
  ]
  if (restoring) frames[1].offset = .45
  const animation = snapshot.animate(restoring ? frames.reverse() : frames, {
    duration: restoring ? 420 : 380, easing: 'cubic-bezier(.22, .7, .25, 1)', fill: 'both'
  })
  runningAnimations.add(animation)
  try { await animation.finished } catch { /* Cancelled during navigation or unmount. */ }
  finally { runningAnimations.delete(animation); snapshot.remove() }
}
