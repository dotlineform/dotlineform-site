import { text } from './text.js';

export function readStoredItem(primaryKey, legacyKey) {
  try {
    var primaryValue = window.localStorage.getItem(primaryKey);
    if (primaryValue != null && text(primaryValue) !== '') return primaryValue;
    if (!legacyKey) return null;
    var legacyValue = window.localStorage.getItem(legacyKey);
    return legacyValue != null && text(legacyValue) !== '' ? legacyValue : null;
  } catch (err) {
    return null;
  }
}

export function writeStoredItem(key, value) {
  try {
    window.localStorage.setItem(key, String(value));
  } catch (err) {
  }
}
