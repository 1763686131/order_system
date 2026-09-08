/**
 * Normalize the grouped units response while keeping compatibility with the
 * old flat array response.
 */
export function normalizeUnitGroups(response) {
  if (Array.isArray(response)) {
    return {
      measurements: response,
      packagings: []
    }
  }

  const groups = response?.units && !Array.isArray(response.units)
    ? response.units
    : (response || {})

  return {
    measurements: groups.measurements || groups.units || [],
    packagings: groups.packagings || groups.packaging || []
  }
}

export function getMeasurementUnits(response) {
  return normalizeUnitGroups(response).measurements
}

export function getPackagingUnits(response) {
  return normalizeUnitGroups(response).packagings
}
