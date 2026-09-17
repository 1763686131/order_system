const UPPERCASE_DIGITS = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖']
const INTEGER_UNITS = ['', '拾', '佰', '仟']
const SECTION_UNITS = ['', '万', '亿', '兆']
const MAX_SUPPORTED_AMOUNT = 10000000000000000

const sectionToChinese = (section) => {
  let value = section
  let unitIndex = 0
  let needsZero = false
  let result = ''

  while (value > 0) {
    const digit = value % 10

    if (digit === 0) {
      if (!needsZero && result) {
        result = UPPERCASE_DIGITS[0] + result
      }
      needsZero = true
    } else {
      result = UPPERCASE_DIGITS[digit] + INTEGER_UNITS[unitIndex] + result
      needsZero = false
    }

    unitIndex += 1
    value = Math.floor(value / 10)
  }

  return result
}

const integerToChinese = (integer) => {
  let value = integer
  let sectionIndex = 0
  let insertZero = false
  let result = ''

  while (value > 0) {
    const section = value % 10000

    if (section > 0) {
      if (insertZero && result && !result.startsWith(UPPERCASE_DIGITS[0])) {
        result = UPPERCASE_DIGITS[0] + result
      }

      result = `${sectionToChinese(section)}${SECTION_UNITS[sectionIndex]}${result}`
      insertZero = section < 1000
    } else if (result) {
      insertZero = true
    }

    sectionIndex += 1
    value = Math.floor(value / 10000)
  }

  return result
}

const normalizeAmount = (value) => {
  if (typeof value === 'string') {
    const normalized = value.replace(/[,\s￥¥]/g, '')
    if (!normalized) return null
    value = normalized
  }

  const amount = Number(value)
  if (!Number.isFinite(amount) || Math.abs(amount) >= MAX_SUPPORTED_AMOUNT) {
    return null
  }

  return amount
}

export const toChineseMoney = (value) => {
  const amount = normalizeAmount(value)
  if (amount === null) return ''

  const negative = amount < 0
  const absoluteAmount = Math.abs(amount)
  const roundedAmount = Math.round((absoluteAmount + Number.EPSILON) * 100) / 100
  const [integerText, decimalText = '00'] = roundedAmount.toFixed(2).split('.')
  const integer = Number(integerText)
  const jiao = Number(decimalText[0])
  const fen = Number(decimalText[1])

  let result = `${integer === 0 ? UPPERCASE_DIGITS[0] : integerToChinese(integer)}元`

  if (jiao === 0 && fen === 0) {
    result += '整'
  } else {
    if (jiao > 0) {
      result += `${UPPERCASE_DIGITS[jiao]}角`
    } else if (integer > 0 && fen > 0) {
      result += UPPERCASE_DIGITS[0]
    }

    if (fen > 0) {
      result += `${UPPERCASE_DIGITS[fen]}分`
    } else {
      result += '整'
    }
  }

  return negative ? `负${result}` : result
}
