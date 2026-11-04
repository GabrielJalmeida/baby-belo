export const PREFERENCES_KEY = 'baby-belo.accessibility'
export const defaultPreferences = { dark: false, fontSize: 'normal', contrast: false, underline: false }
export function normalizePreferences(value = {}) {
  return {
    dark: value?.dark === true,
    fontSize: ['normal', 'large', 'larger'].includes(value?.fontSize) ? value.fontSize : 'normal',
    contrast: value?.contrast === true,
    underline: value?.underline === true,
  }
}
export function readPreferences(storage) {
  try { return normalizePreferences(JSON.parse((storage ?? window.localStorage).getItem(PREFERENCES_KEY))) }
  catch { return { ...defaultPreferences } }
}
export function applyPreferences(root, preferences) {
  root.dataset.theme = preferences.dark ? 'dark' : 'light'
  root.dataset.fontSize = preferences.fontSize
  root.dataset.contrast = String(preferences.contrast)
  root.dataset.underline = String(preferences.underline)
}
