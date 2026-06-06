const KEY = "ludus_username";

const ADJECTIVES = [
  "Swift", "Brave", "Clever", "Bold", "Calm", "Fierce", "Gentle", "Jolly",
  "Keen", "Lively", "Mighty", "Noble", "Quick", "Sly", "Witty", "Zesty",
  "Daring", "Epic", "Fuzzy", "Grumpy", "Happy", "Icy", "Jumpy", "Lucky",
  "Nimble", "Odd", "Peppy", "Quirky", "Rusty", "Snappy", "Tiny", "Wavy",
];

const ANIMALS = [
  "Badger", "Bear", "Cat", "Cobra", "Crab", "Crow", "Deer", "Dog",
  "Duck", "Eagle", "Elk", "Fox", "Frog", "Hawk", "Horse", "Lynx",
  "Moose", "Owl", "Panda", "Parrot", "Pike", "Puma", "Raven", "Shark",
  "Sloth", "Snake", "Tiger", "Toad", "Viper", "Wolf", "Wren", "Yak",
];

function generateRandomUsername() {
  const adj = ADJECTIVES[Math.floor(Math.random() * ADJECTIVES.length)];
  const animal = ANIMALS[Math.floor(Math.random() * ANIMALS.length)];
  const num = Math.floor(Math.random() * 90) + 10; // 10–99
  return `${adj}${animal}${num}`;
}

export function getSavedUsername() {
  const saved = localStorage.getItem(KEY);
  if (saved) return saved;
  const generated = generateRandomUsername();
  localStorage.setItem(KEY, generated);
  return generated;
}

export function saveUsername(name) {
  if (name) localStorage.setItem(KEY, name);
}
