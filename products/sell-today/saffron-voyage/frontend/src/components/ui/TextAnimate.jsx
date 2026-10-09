import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../utils';

const EASE = [0.22, 1, 0.36, 1];

const TextAnimate = ({
  text = '',
  as: Tag = 'span',
  delay = 0,
  interval = 0.06,
  variant = 'fade',
  className = '',
}) => {
  const words = String(text).split(' ').filter(Boolean);

  return (
    <Tag className={cn('inline-flex flex-wrap', className)}>
      {words.map((word, i) => (
        <span key={`${word}-${i}`} className="inline-block overflow-hidden pb-[0.12em]">
          <motion.span
            className="inline-block will-change-transform"
            initial={{
              opacity: 0,
              y: variant === 'slide' || variant === 'rise' ? '80%' : 0,
              filter: variant === 'blur' ? 'blur(8px)' : 'blur(0px)',
            }}
            animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
            transition={{ delay: delay + i * interval, duration: 0.5, ease: EASE }}
          >
            {word}
            {'\u00A0'}
          </motion.span>
        </span>
      ))}
    </Tag>
  );
};

TextAnimate.displayName = 'TextAnimate';

export default TextAnimate;
