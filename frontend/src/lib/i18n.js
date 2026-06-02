import { addMessages, init, getLocaleFromNavigator } from 'svelte-i18n';
import en from './i18n/en.json';
import de from './i18n/de.json';

addMessages('en', en);
addMessages('de', de);

// Auto-import all game translation files (e.g. src/games/*/i18n/*.json)
const gameMsgs = import.meta.glob('../games/*/i18n/*.json', { eager: true });
for (const [path, mod] of Object.entries(gameMsgs)) {
  const loc = path.match(/\/([a-z_]+)\.json$/)[1];
  addMessages(loc, mod.default);
}

export function setupI18n() {
  init({
    fallbackLocale: 'en',
    initialLocale: localStorage.getItem('ludus_locale') || getLocaleFromNavigator(),
  });
}
