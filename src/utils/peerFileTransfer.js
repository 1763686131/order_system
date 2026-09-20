const CHUNK_SIZE = 32 * 1024
const MAX_BUFFERED_BYTES = 4 * 1024 * 1024
const LOW_BUFFERED_BYTES = 512 * 1024
const CONNECTION_TIMEOUT_MS = 30000

const createPeerConnection = () => new RTCPeerConnection({ iceServers: [] })

const serializeDescription = description => ({
  type: description.type,
  sdp: description.sdp
})

const waitForIceGathering = connection => {
  if (connection.iceGatheringState === 'complete') {
    return Promise.resolve()
  }

  return new Promise((resolve, reject) => {
    const timeout = window.setTimeout(() => {
      cleanup()
      reject(new Error('局域网连接信息生成超时'))
    }, CONNECTION_TIMEOUT_MS)
    const handleStateChange = () => {
      if (connection.iceGatheringState !== 'complete') return
      cleanup()
      resolve()
    }
    const cleanup = () => {
      window.clearTimeout(timeout)
      connection.removeEventListener('icegatheringstatechange', handleStateChange)
    }
    connection.addEventListener('icegatheringstatechange', handleStateChange)
  })
}

const waitForBuffer = channel => {
  if (channel.bufferedAmount <= MAX_BUFFERED_BYTES) return Promise.resolve()

  return new Promise((resolve, reject) => {
    const timeout = window.setTimeout(() => {
      cleanup()
      reject(new Error('文件发送缓冲区等待超时'))
    }, CONNECTION_TIMEOUT_MS)
    const handleLow = () => {
      cleanup()
      resolve()
    }
    const handleClose = () => {
      cleanup()
      reject(new Error('点对点连接已断开'))
    }
    const cleanup = () => {
      window.clearTimeout(timeout)
      channel.removeEventListener('bufferedamountlow', handleLow)
      channel.removeEventListener('close', handleClose)
    }
    channel.addEventListener('bufferedamountlow', handleLow, { once: true })
    channel.addEventListener('close', handleClose, { once: true })
  })
}

const emitError = (callback, error) => {
  callback?.(error instanceof Error ? error : new Error(String(error || '点对点传输失败')))
}

const bindConnectionFailure = (connection, callback) => {
  connection.addEventListener('connectionstatechange', () => {
    if (['failed', 'disconnected'].includes(connection.connectionState)) {
      emitError(callback, new Error('局域网点对点连接失败或已断开'))
    }
  })
}

export const supportsPeerFileTransfer = () => (
  typeof RTCPeerConnection !== 'undefined' && typeof FileReader !== 'undefined'
)

export const canStreamPeerFileToDisk = () => (
  window.isSecureContext && typeof window.showSaveFilePicker === 'function'
)

export const choosePeerFileDestination = async fileName => {
  if (!canStreamPeerFileToDisk()) return null

  const handle = await window.showSaveFilePicker({ suggestedName: fileName })
  return handle.createWritable()
}

export const createPeerFileSender = ({ file, onProgress, onStatus, onComplete, onError }) => {
  const connection = createPeerConnection()
  const channel = connection.createDataChannel('order-system-file', { ordered: true })
  let closed = false
  let sending = false

  channel.binaryType = 'arraybuffer'
  channel.bufferedAmountLowThreshold = LOW_BUFFERED_BYTES
  bindConnectionFailure(connection, error => {
    if (!closed) emitError(onError, error)
  })

  const sendFile = async () => {
    if (sending || closed) return
    sending = true
    onStatus?.('transferring')
    try {
      channel.send(JSON.stringify({
        kind: 'start',
        name: file.name,
        size: file.size,
        type: file.type || 'application/octet-stream'
      }))
      let offset = 0
      while (offset < file.size) {
        if (closed || channel.readyState !== 'open') {
          throw new Error('点对点连接已关闭')
        }
        await waitForBuffer(channel)
        const chunk = await file.slice(offset, offset + CHUNK_SIZE).arrayBuffer()
        channel.send(chunk)
        offset += chunk.byteLength
        onProgress?.(offset, file.size)
      }
      await waitForBuffer(channel)
      channel.send(JSON.stringify({ kind: 'complete', size: file.size }))
      onStatus?.('sent')
      onComplete?.()
    } catch (error) {
      emitError(onError, error)
    }
  }

  channel.addEventListener('open', sendFile)
  channel.addEventListener('error', () => {
    if (!closed) emitError(onError, new Error('文件传输通道发生错误'))
  })

  return {
    async createOffer() {
      const offer = await connection.createOffer()
      await connection.setLocalDescription(offer)
      await waitForIceGathering(connection)
      return serializeDescription(connection.localDescription)
    },
    async applyAnswer(answer) {
      await connection.setRemoteDescription(answer)
    },
    close() {
      closed = true
      try {
        channel.close()
      } finally {
        connection.close()
      }
    }
  }
}

export const createPeerFileReceiver = ({
  metadata,
  writable,
  onProgress,
  onStatus,
  onComplete,
  onError
}) => {
  const connection = createPeerConnection()
  const chunks = []
  let receivedBytes = 0
  let writeChain = Promise.resolve()
  let channel = null
  let closed = false
  let completed = false

  bindConnectionFailure(connection, error => {
    if (!closed && !completed) emitError(onError, error)
  })

  const finishDownload = async () => {
    await writeChain
    if (receivedBytes !== Number(metadata.fileSize)) {
      throw new Error('接收文件大小不完整，请重新发送')
    }
    if (writable) {
      await writable.close()
    } else {
      const blob = new Blob(chunks, {
        type: metadata.mimeType || 'application/octet-stream'
      })
      const downloadUrl = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = metadata.fileName || 'download'
      link.style.display = 'none'
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.setTimeout(() => URL.revokeObjectURL(downloadUrl), 60000)
    }
    completed = true
    onStatus?.('completed')
    onComplete?.()
  }

  connection.addEventListener('datachannel', event => {
    channel = event.channel
    channel.binaryType = 'arraybuffer'
    channel.addEventListener('open', () => onStatus?.('transferring'))
    channel.addEventListener('message', event => {
      if (typeof event.data === 'string') {
        let control = {}
        try {
          control = JSON.parse(event.data)
        } catch {
          emitError(onError, new Error('收到无法识别的传输控制消息'))
          return
        }
        if (control.kind === 'complete') {
          finishDownload().catch(error => emitError(onError, error))
        }
        return
      }

      const chunk = event.data instanceof ArrayBuffer
        ? event.data
        : event.data?.buffer
      if (!chunk) return
      receivedBytes += chunk.byteLength
      if (receivedBytes > Number(metadata.fileSize)) {
        emitError(onError, new Error('接收数据超过声明的文件大小'))
        return
      }
      if (writable) {
        writeChain = writeChain.then(() => writable.write(chunk))
      } else {
        chunks.push(chunk)
      }
      onProgress?.(receivedBytes, Number(metadata.fileSize))
    })
    channel.addEventListener('error', () => {
      if (!completed && !closed) emitError(onError, new Error('文件接收通道发生错误'))
    })
  })

  return {
    async createAnswer(offer) {
      await connection.setRemoteDescription(offer)
      const answer = await connection.createAnswer()
      await connection.setLocalDescription(answer)
      await waitForIceGathering(connection)
      return serializeDescription(connection.localDescription)
    },
    async abort() {
      closed = true
      channel?.close()
      connection.close()
      if (writable && !completed) {
        try {
          await writable.abort()
        } catch {
          // 保存目标可能已经由浏览器关闭。
        }
      }
    },
    close() {
      closed = true
      channel?.close()
      connection.close()
    }
  }
}
