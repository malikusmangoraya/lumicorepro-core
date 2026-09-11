/**
 * Shared animation maps for pro components.
 * Pass `animate="fade-up"` (or similar) on components that support it.
 */

export const ANIMATIONS = {
  none: '',
  fade: 'animate-fade-in',
  'fade-up': 'animate-fade-in-up',
  'fade-down': 'animate-fade-in-down',
  'fade-left': 'animate-fade-in-left',
  'fade-right': 'animate-fade-in-right',
  scale: 'animate-scale-in',
  'bounce-in': 'animate-bounce-in',
  'slide-up': 'animate-slide-in-up',
  'slide-left': 'animate-slide-in-left',
  'slide-right': 'animate-slide-in-right',
  shake: 'animate-shake',
  float: 'animate-float',
};

export const ANIMATION_DELAYS = {
  0: '',
  75: 'delay-75',
  100: 'delay-100',
  150: 'delay-150',
  200: 'delay-200',
  300: 'delay-300',
  500: 'delay-500',
  700: 'delay-700',
  1000: 'delay-1000',
};

/**
 * Resolve animation + optional delay into class names.
 * @param {keyof typeof ANIMATIONS | false | null} animate
 * @param {keyof typeof ANIMATION_DELAYS | number} [delay]
 */
export function getAnimationClass(animate, delay = 0) {
  if (!animate || animate === 'none') return '';
  const anim = ANIMATIONS[animate] || '';
  const delayClass = ANIMATION_DELAYS[delay] || '';
  return [anim, delayClass].filter(Boolean).join(' ');
}
