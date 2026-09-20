const listeners = new Map()

let eventSource = null

const emit = (eventName, payload = {}) => {
  listeners.get(eventName)?.forEach(listener => {
    try {
      listener(payload)
    } catch (error) {
      console.error(`后台实时事件处理失败: ${eventName}`, error)
    }
  })
}

const parsePayload = event => {
  try {
    return JSON.parse(event.data || '{}')
  } catch {
    return {}
  }
}

const connect = () => {
  if (eventSource || typeof EventSource === 'undefined') return

  eventSource = new EventSource('/api/admin/realtime/events', { withCredentials: true })
  eventSource.addEventListener('connected', event => {
    const payload = parsePayload(event)
    emit('connection', { connected: true })
    emit('messages', payload.messages || {})
    emit('notifications', payload.notifications || {})
  })
  eventSource.addEventListener('message-change', event => {
    emit('messages', parsePayload(event))
  })
  eventSource.addEventListener('notification-change', event => {
    emit('notifications', parsePayload(event))
  })
  eventSource.addEventListener('session-ended', () => {
    emit('connection', { connected: false, sessionEnded: true })
    eventSource?.close()
    eventSource = null
  })
  eventSource.onerror = () => {
    emit('connection', { connected: false, reconnecting: true })
  }
}

const disconnectIfUnused = () => {
  const hasListeners = [...listeners.values()].some(group => group.size > 0)
  if (hasListeners || !eventSource) return
  eventSource.close()
  eventSource = null
}

export const subscribeAdminRealtime = (eventName, listener) => {
  if (!listeners.has(eventName)) listeners.set(eventName, new Set())
  listeners.get(eventName).add(listener)
  connect()

  return () => {
    listeners.get(eventName)?.delete(listener)
    disconnectIfUnused()
  }
}

export const supportsAdminRealtime = () => typeof EventSource !== 'undefined'
