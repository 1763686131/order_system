const runningAnimations = new Set()
const pendingReleases = new Set()

export function cancelDocumentDockAnimations() {
  for (const animation of runningAnimations) animation.cancel()
  for (const release of pendingReleases) release()
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

function getVisibleRect(element, rect) {
  const containerRect = element.closest('.main-content')?.getBoundingClientRect()
  const left = Math.max(0, rect.left, containerRect?.left ?? 0)
  const top = Math.max(0, rect.top, containerRect?.top ?? 0)
  const right = Math.min(window.innerWidth, rect.right, containerRect?.right ?? window.innerWidth)
  const bottom = Math.min(window.innerHeight, rect.bottom, containerRect?.bottom ?? window.innerHeight)
  return { left, top, width: right - left, height: bottom - top }
}

function createSnapshot(element, rect, visibleRect) {
  const layer = document.createElement('div')
  layer.className = 'document-dock-snapshot'
  layer.setAttribute('aria-hidden', 'true')
  layer.inert = true
  const snapshot = element.cloneNode(true)
  snapshot.removeAttribute('id')
  snapshot.querySelectorAll('[id]').forEach(node => node.removeAttribute('id'))
  const originalInputs = element.querySelectorAll('input, select, textarea')
  snapshot.querySelectorAll('input, select, textarea').forEach((input, index) => {
    input.value = originalInputs[index].value
    if (input.type === 'checkbox' || input.type === 'radio') input.checked = originalInputs[index].checked
  })
  // The body-level clone must retain the page's inherited tokens and typography.
  const computedStyle = window.getComputedStyle(element)
  for (const property of computedStyle) {
    if (property.startsWith('--')) snapshot.style.setProperty(property, computedStyle.getPropertyValue(property))
  }
  Object.assign(snapshot.style, {
    position: 'absolute', left: `${rect.left - visibleRect.left}px`, top: `${rect.top - visibleRect.top}px`,
    width: `${rect.width}px`, height: `${rect.height}px`, margin: '0', visibility: 'visible',
    fontFamily: computedStyle.fontFamily, fontSize: computedStyle.fontSize, color: computedStyle.color
  })
  Object.assign(layer.style, {
    position: 'fixed', left: `${visibleRect.left}px`, top: `${visibleRect.top}px`,
    width: `${visibleRect.width}px`, height: `${visibleRect.height}px`,
    zIndex: '3000', pointerEvents: 'none', overflow: 'hidden', borderRadius: '6px',
    transformOrigin: '0 0', willChange: 'transform, opacity',
    boxShadow: '0 16px 40px rgba(15, 23, 42, 0.18)'
  })
  layer.appendChild(snapshot)
  document.body.appendChild(layer)
  const originalTables = element.querySelectorAll('.products-table-wrapper')
  snapshot.querySelectorAll('.products-table-wrapper').forEach((table, index) => {
    table.scrollLeft = originalTables[index].scrollLeft
  })
  return layer
}

function getFlightFrames(rect, targetRect, restoring) {
  const centerX = rect.left + rect.width / 2
  const centerY = rect.top + rect.height / 2
  const dx = targetRect.left + targetRect.width / 2 - centerX
  const dy = targetRect.top + targetRect.height / 2 - centerY
  const scaleX = targetRect.width / rect.width
  const scaleY = targetRect.height / rect.height
  // Keep the card readable through most of the flight; fade only at the receiving icon.
  const stages = [
    { offset: 0, progress: 0, scale: 1, opacity: 1 },
    { offset: .14, progress: .04, scale: .96, opacity: 1 },
    { offset: .42, progress: .36, scale: .72, opacity: 1 },
    { offset: .68, progress: .7, scale: .4, opacity: .98 },
    { offset: .86, progress: .91, scale: .16, opacity: .94 },
    { offset: .96, progress: .99, scale: .06, opacity: .8 },
    { offset: 1, progress: 1, opacity: 0 }
  ]
  const frames = stages.map(({ offset, progress, scale, opacity }) => {
    const sx = scale === undefined ? scaleX : Math.max(scale, scaleX)
    const sy = scale === undefined ? scaleY : Math.max(scale, scaleY)
    const arc = Math.min(60, Math.abs(dy) * .15) * Math.sin(Math.PI * progress)
    const x = dx * progress + rect.width * (1 - sx) / 2
    const y = Math.max(
      targetRect.top - rect.top,
      dy * progress + rect.height * (1 - sy) / 2 + arc
    )
    return {
      offset, opacity, transform: `translate3d(${x}px, ${y}px, 0) scale(${sx}, ${sy})`
    }
  })
  if (restoring) {
    frames.reverse()
    frames.forEach(frame => { frame.offset = 1 - frame.offset })
  }
  return frames
}

// A completed minimize keeps the source hidden until the router has rendered the next page.
// The returned release function (also invoked by cancellation) restores it on aborted navigation.
export async function animateDocumentDock(element, targetRect, restoring = false) {
  if (!targetRect || !element.animate || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return null
  const rect = element.getBoundingClientRect()
  const visibleRect = getVisibleRect(element, rect)
  if (visibleRect.width <= 0 || visibleRect.height <= 0 || targetRect.width <= 0 || targetRect.height <= 0) return null
  const snapshot = createSnapshot(element, rect, visibleRect)
  const previousVisibility = element.style.visibility
  let released = false
  const release = () => {
    if (released) return
    released = true
    pendingReleases.delete(release)
    snapshot.remove()
    if (element.isConnected) element.style.visibility = previousVisibility
  }
  pendingReleases.add(release)
  element.style.visibility = 'hidden'
  let animation
  let completed = false
  try {
    animation = snapshot.animate(getFlightFrames(visibleRect, targetRect, restoring), {
      duration: restoring ? 640 : 820, easing: 'cubic-bezier(.42, 0, .58, 1)', fill: 'both'
    })
    runningAnimations.add(animation)
    await animation.finished
    completed = true
  } catch {
    // Cancellation or an unavailable animation API must never block navigation.
  } finally {
    runningAnimations.delete(animation)
    snapshot.remove()
    if (!completed || restoring) release()
  }
  return completed && !restoring ? release : null
}
