import React, { useEffect, useRef } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { cn } from '../../utils';

const DockItem = ({ item, mouseX, magnification, distance }) => {
  const ref = useRef(null);
  const dist = useMotionValue(distance);
  const scale = useSpring(useTransform(dist, [distance, 0], [1, magnification]), {
    stiffness: 260,
    damping: 18,
    mass: 0.3,
  });

  useEffect(() => {
    const el = ref.current;
    if (!el) return undefined;
    const update = () => {
      const rect = el.getBoundingClientRect();
      const current = Math.abs(mouseX.get() - (rect.left + rect.width / 2));
      dist.set(Math.max(0, current));
    };
    const unsub = mouseX.on('change', update);
    update();
    return unsub;
  }, [mouseX, dist, distance]);

  const Icon = item.icon;

  return (
    <motion.a
      ref={ref}
      href={item.href}
      style={{ scale }}
      className="group relative flex h-12 w-12 items-center justify-center rounded-xl border border-border bg-card text-card-foreground shadow-sm transition-colors hover:text-primary"
      aria-label={item.label}
      title={item.label}
    >
      {Icon ? <Icon className="h-5 w-5" /> : item.children}
      <span className="pointer-events-none absolute -top-9 left-1/2 -translate-x-1/2 rounded-md border border-border bg-popover px-2 py-1 text-xs text-popover-foreground opacity-0 transition-opacity group-hover:opacity-100">
        {item.label}
      </span>
    </motion.a>
  );
};

DockItem.displayName = 'DockItem';

const Dock = ({
  items = [],
  magnification = 22,
  distance = 110,
  className = '',
  panelClassName = '',
}) => {
  const mouseX = useMotionValue(Infinity);

  return (
    <div
      className={cn(
        'pointer-events-none fixed inset-x-0 bottom-4 z-50 flex justify-center',
        className
      )}
    >
      <div
        onMouseMove={(e) => mouseX.set(e.pageX)}
        onMouseLeave={() => mouseX.set(Infinity)}
        className={cn(
          'pointer-events-auto flex items-end gap-2 rounded-2xl border border-border bg-background/70 px-3 pb-2 pt-2 shadow-lg backdrop-blur',
          panelClassName
        )}
      >
        {items.map((item, i) => (
          <DockItem
            key={i}
            item={item}
            mouseX={mouseX}
            magnification={magnification}
            distance={distance}
          />
        ))}
      </div>
    </div>
  );
};

Dock.displayName = 'Dock';

export default Dock;
export { DockItem };
