import request from './request'

export const getLogisticsCopySettings = () => request.get('/settings/logistics-copy')

export const resolveLogisticsCopySettings = target => request.get(
  '/settings/logistics-copy/resolve',
  { params: { target } }
)

export const putLogisticsCopySettings = (fields, templates) => request.put(
  '/settings/logistics-copy',
  { fields, templates }
)
