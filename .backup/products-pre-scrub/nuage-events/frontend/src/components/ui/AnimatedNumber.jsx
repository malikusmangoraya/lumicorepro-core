import React, { useEffect, useState } from 'react';
import { animate } from 'framer-motion';
import { cn } from '../../utils';

const AnimatedNumber = ({
  value = 0,
  decimals = 0,
  separator = true,
  prefix = '',
  suffix = '',
  duration = 1.4,
  className = '',
  as: Tag = 'span',
}) => {
  const format = (n) => {
    const fixed = Number(n).toFixed(decimals);
    const [int, dec] = fixed.split('.');
    const grouped = separator ? Number(int).toLocaleString('en-US') : int;
    return dec ? `${grouped}.${dec}` : grouped;
  };

  const [display, setDisplay] = useState(format(0));

  useEffect(() => {
    const controls = animate(0, Number(value) || 0, {
      duration,
      ease: [0.22, 1, 0.36, 1],
      onUpdate: (v) => setDisplay(format(v)),
      onComplete: () => setDisplay(format(Number(value) || 0)),
    });
    return () => controls.stop();
  }, [value, decimals, separator, duration]);

  return (
    <Tag className={cn('tabular-nums', className)}>
      {prefix}
      {display}
      {suffix}
    </Tag>
  );
};

AnimatedNumber.displayName = 'AnimatedNumber';

export default AnimatedNumber;
