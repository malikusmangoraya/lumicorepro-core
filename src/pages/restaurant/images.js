/**
 * Restaurant image assets — real food photography downloaded to
 * src/assets/restaurant/ (AGENTS.md: real images, no placeholders).
 */
export const IMAGES = {
  hero: new URL('../assets/restaurant/hero.jpg', import.meta.url).href,
  pizza: new URL('../assets/restaurant/pizza.jpg', import.meta.url).href,
  burger: new URL('../assets/restaurant/burger.jpg', import.meta.url).href,
  pasta: new URL('../assets/restaurant/pasta.jpg', import.meta.url).href,
  salad: new URL('../assets/restaurant/salad.jpg', import.meta.url).href,
  sushi: new URL('../assets/restaurant/sushi.jpg', import.meta.url).href,
  dessert: new URL('../assets/restaurant/dessert.jpg', import.meta.url).href,
  coffee: new URL('../assets/restaurant/coffee.jpg', import.meta.url).href,
  fallback:
    'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=600&q=80',
};
