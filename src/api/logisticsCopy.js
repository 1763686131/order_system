import request from './request'

export const LOGISTICS_COPY_SETTINGS_CHANGED_EVENT = 'logistics-copy-settings-changed'

export const getLogisticsCopySettings = () => request.get('/settings/logistics-copy')

export const resolveLogisticsCopySettings = target => request.get(
  '/settings/logistics-copy/resolve',
  { params: { target } }
)

export const putLogisticsCopySettings = async (fields, templates) => {
  const response = await request.put('/settings/logistics-copy', { fields, templates })
  if (response?.success && typeof window !== 'undefined') {
    window.dispatchEvent(new Event(LOGISTICS_COPY_SETTINGS_CHANGED_EVENT))
  }
  return response
}
