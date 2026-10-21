import Decimal from 'decimal.js'

export const dateKey = date => [
  date.getFullYear(),
  String(date.getMonth() + 1).padStart(2, '0'),
  String(date.getDate()).padStart(2, '0')
].join('-')

export function parseDashboardDate(value) {
  if (!value) return null
  const match = String(value).match(/^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?$/)
  if (!match) return null
  const [, yearText, monthText, dayText, hourText, minuteText, secondText] = match
  const [year, month, day, hour, minute, second] = [
    yearText, monthText, dayText, hourText || '0', minuteText || '0', secondText || '0'
  ].map(Number)
  const date = new Date(year, month - 1, day, hour, minute, second)
  return date.getFullYear() === year && date.getMonth() === month - 1
    && date.getDate() === day && date.getHours() === Number(hour)
    && date.getMinutes() === Number(minute) && date.getSeconds() === Number(second)
    ? date : null
}

export function getOrderDate(order) {
  const businessDate = order.order_date || order.orderDate
  const timestamp = parseDashboardDate(order.date)
  if (!businessDate) return timestamp
  const date = parseDashboardDate(businessDate)
  if (date && timestamp && dateKey(date) === dateKey(timestamp)) return timestamp
  return date
}

const amountValue = value => {
  if (value === null || value === undefined || value === '') return null
  try {
    const amount = new Decimal(value)
    return amount.isFinite() ? amount : null
  } catch {
    return null
  }
}

export function getOrderAmount(order) {
  const receivable = amountValue(order.should_receive ?? order.shouldReceive)
  if (receivable !== null) return receivable.toNumber()
  const discounted = amountValue(order.discount_amount ?? order.discountAmount)
  const total = amountValue(order.total_amount ?? order.totalAmount)
  const subtotal = amountValue(order.subtotal_amount ?? order.subtotalAmount)
  const goods = discounted ?? (total?.isZero() && subtotal ? subtotal : total) ?? subtotal ?? new Decimal(0)
  return goods.plus(amountValue(order.other_fees ?? order.otherFees) ?? 0).toNumber()
}

export const sumOrderAmounts = orders => orders.reduce(
  (sum, order) => sum.plus(getOrderAmount(order)), new Decimal(0)
).toDecimalPlaces(2).toNumber()

export function getOrderGroups(orders, now) {
  const today = dateKey(now)
  const month = today.slice(0, 7)
  return {
    today: orders.filter(order => {
      const date = getOrderDate(order)
      return date && dateKey(date) === today
    }),
    pending: orders.filter(order => order.status === 'pending'),
    logistics: orders.filter(order => order.status === 'completed'),
    audit: orders.filter(order => (
      order.status === 'shipped' && Number(order.audit_state) === 0
      && String(order.order_number || '').trim()
      && Array.isArray(order.order_goods) && order.order_goods.length > 0
    )),
    completed: orders.filter(order => {
      if (!['completed', 'shipped'].includes(order.status)) return false
      const date = parseDashboardDate(order.completed_date || order.shipped_date)
      return date && dateKey(date).slice(0, 7) === month && dateKey(date) <= today
    })
  }
}

const calendarDay = date => Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()) / 86400000

export function getOrderTrend(orders, period, now) {
  const start = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  if (period === 'week') start.setDate(start.getDate() - (start.getDay() + 6) % 7)
  if (period === 'month') start.setDate(1)
  const length = period === 'day' ? 24 : calendarDay(now) - calendarDay(start) + 1
  const buckets = Array.from({ length }, (_, index) => {
    const date = new Date(start.getFullYear(), start.getMonth(), start.getDate() + index)
    return {
      key: period === 'day' ? index : dateKey(date),
      label: period === 'day'
        ? `${String(index).padStart(2, '0')}:00`
        : `${date.getMonth() + 1}/${date.getDate()}`,
      count: 0,
      amount: new Decimal(0)
    }
  })
  for (const order of orders) {
    const date = getOrderDate(order)
    if (!date || (period === 'day' && dateKey(date) !== dateKey(now))) continue
    const index = period === 'day' ? date.getHours() : calendarDay(date) - calendarDay(start)
    if (index >= 0 && index < buckets.length) {
      buckets[index].count += 1
      buckets[index].amount = buckets[index].amount.plus(getOrderAmount(order))
    }
  }
  return buckets.map(bucket => ({ ...bucket, amount: bucket.amount.toDecimalPlaces(2).toNumber() }))
}
