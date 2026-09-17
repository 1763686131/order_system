export const PRINT_CLIENT_CONFIG_STORAGE_KEY = 'order-system-print-client-config'

const LEGACY_PRINTER_STORAGE_KEY = 'order-system-selected-printer'

const getLocationProtocol = () => (
  typeof window !== 'undefined' && window.location?.protocol === 'https:'
    ? 'https'
    : 'http'
)

const getEnvironmentService = () => {
  const configuredUrl = String(import.meta.env.VITE_CLODOP_URL || '').trim()
  if (!configuredUrl) return null

  try {
    const url = new URL(configuredUrl)
    return {
      protocol: url.protocol.replace(':', '') || getLocationProtocol(),
      host: url.hostname || 'localhost',
      port: Number(url.port) || (url.protocol === 'https:' ? 8443 : 8000)
    }
  } catch {
    return null
  }
}

export const getDefaultPrintClientConfig = () => {
  const environmentService = getEnvironmentService()
  const protocol = environmentService?.protocol || getLocationProtocol()

  return {
    version: 1,
    mode: 'clodop',
    protocol,
    host: environmentService?.host || 'localhost',
    port: environmentService?.port || (protocol === 'https' ? 8443 : 8000),
    printerName: ''
  }
}

export const normalizePrintClientConfig = (value = {}) => {
  const defaults = getDefaultPrintClientConfig()
  const protocol = String(value.protocol || defaults.protocol).toLowerCase() === 'https'
    ? 'https'
    : 'http'
  const port = Number(value.port)

  return {
    version: 1,
    mode: value.mode === 'browser' ? 'browser' : 'clodop',
    protocol,
    host: String(value.host || defaults.host).trim() || defaults.host,
    port: Number.isInteger(port) && port > 0 && port <= 65535
      ? port
      : protocol === 'https' ? 8443 : 8000,
    printerName: String(value.printerName || '').trim()
  }
}

export const getPrintClientConfig = () => {
  const defaults = getDefaultPrintClientConfig()
  if (typeof window === 'undefined') return defaults

  try {
    const stored = window.localStorage.getItem(PRINT_CLIENT_CONFIG_STORAGE_KEY)
    const parsed = stored ? JSON.parse(stored) : {}
    const legacyPrinterName = window.localStorage.getItem(LEGACY_PRINTER_STORAGE_KEY) || ''
    return normalizePrintClientConfig({
      ...parsed,
      printerName: parsed?.printerName || legacyPrinterName
    })
  } catch {
    return defaults
  }
}

export const savePrintClientConfig = (value = {}) => {
  const normalized = normalizePrintClientConfig(value)

  if (typeof window !== 'undefined') {
    try {
      window.localStorage.setItem(
        PRINT_CLIENT_CONFIG_STORAGE_KEY,
        JSON.stringify(normalized)
      )
      if (normalized.printerName) {
        window.localStorage.setItem(
          LEGACY_PRINTER_STORAGE_KEY,
          normalized.printerName
        )
      }
    } catch {
      // Keep the in-memory configuration usable when localStorage is unavailable.
    }
  }

  return normalized
}

export const getPrintServiceBaseUrl = (value = {}) => {
  const config = normalizePrintClientConfig(value)
  return `${config.protocol}://${config.host}:${config.port}`
}

export const getPrintSdkUrl = (value = {}) => (
  `${getPrintServiceBaseUrl(value)}/CLodopfuncs.js?name=CLODOP`
)

export const getPrintConfigFromSdkUrl = (sdkUrl, fallback = {}) => {
  const normalizedFallback = normalizePrintClientConfig(fallback)

  try {
    const url = new URL(sdkUrl)
    const protocol = url.protocol === 'https:' ? 'https' : 'http'
    return normalizePrintClientConfig({
      ...normalizedFallback,
      protocol,
      host: url.hostname,
      port: Number(url.port) || (protocol === 'https' ? 8443 : 8000)
    })
  } catch {
    return normalizedFallback
  }
}
