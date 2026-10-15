import { onScopeDispose, ref } from 'vue'
import { getLocalPrinters } from '@/utils/lodopPrint'
import { getPrintClientConfig, normalizePrintClientConfig } from '@/utils/printClientConfig'

export const usePrintAvailability = (getPrinter = () => null) => {
  const printConfig = ref(getPrintClientConfig())
  const checkingPrintService = ref(false)
  const printAvailable = ref(false)
  const printUnavailableReason = ref('')
  let requestId = 0

  const cancelPrintCheck = () => {
    requestId += 1
    checkingPrintService.value = false
    printAvailable.value = false
    printUnavailableReason.value = ''
  }

  const refreshPrintAvailability = async (config = getPrintClientConfig()) => {
    const currentRequestId = ++requestId
    const currentConfig = normalizePrintClientConfig(config)
    printConfig.value = currentConfig
    printAvailable.value = false
    printUnavailableReason.value = ''
    checkingPrintService.value = currentConfig.mode === 'clodop'

    if (currentConfig.mode === 'browser') {
      printAvailable.value = true
      return true
    }

    try {
      const printers = await getLocalPrinters(currentConfig)
      if (currentRequestId !== requestId) return false

      const printerName = currentConfig.printerName || getPrinter()?.name || ''
      if (!printers.length) {
        printUnavailableReason.value = '未检测到本地打印机，当前仅可预览。'
      } else if (!printerName) {
        printUnavailableReason.value = '尚未选择打印机，当前仅可预览。请在打印设置中选择。'
      } else if (!printers.some(printer => printer.name === printerName)) {
        printUnavailableReason.value = `打印机“${printerName}”不可用，当前仅可预览。请重新选择。`
      } else {
        printAvailable.value = true
      }
    } catch {
      if (currentRequestId !== requestId) return false
      printUnavailableReason.value = '未连接到 C-Lodop 打印插件，当前仅可预览。请安装并启动插件后重新检测。'
    } finally {
      if (currentRequestId === requestId) checkingPrintService.value = false
    }

    return currentRequestId === requestId && printAvailable.value
  }

  onScopeDispose(cancelPrintCheck)

  return {
    printConfig,
    checkingPrintService,
    printAvailable,
    printUnavailableReason,
    refreshPrintAvailability,
    cancelPrintCheck
  }
}
