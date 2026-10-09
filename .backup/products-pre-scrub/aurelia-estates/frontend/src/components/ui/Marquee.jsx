import React, { useRef } from 'react';
import { motion, useAnimationFrame } from 'framer-motion';
import { cn } from '../../utils';

const Marquee = ({
  items = [],
  speed = 40,
  reverse = false,
  pauseOnHover = true,
  className = '',
  renderItem = null,
}) => {
  const trackRef = useRef(null);
  const paused = useRef(false);
  const phase = useRef(0);

  useAnimationFrame((_, delta) => {
    if (!trackRef.current || paused.current) return;
    phase.current -= (reverse ? -1 : 1) * speed * (delta / 1000);
    const half = trackRef.current.scrollWidth / 2 || 1;
    if (Math.abs(phase.current) >= half) {
      phase.current += half * (reverse ? 1 : -1);
    }
    trackRef.current.style.transform = `translate3d(${phase.current}px, 0, 0)`;
  });

  const content = items.map((item, i) => (renderItem ? renderItem(item, i) : item));

  return (
    <div
      className={cn('relative flex w-full overflow-hidden', className)}
      onMouseEnter={() => {
        if (pauseOnHover) paused.current = true;
      }}
      onMouseLeave={() => {
        paused.current = false;
      }}
    >
      <motion.div ref={trackRef} className="flex w-max items-center gap-6 pr-6">
        {content}
        {content}
      </motion.div>
    </div>
  );
};

Marquee.displayName = 'Marquee';

export default Marquee;
