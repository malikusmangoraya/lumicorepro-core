import React, { useEffect, useState } from 'react';
import { cn } from '../../utils';

const Typewriter = ({
  words = [],
  typingSpeed = 90,
  deletingSpeed = 45,
  pauseMs = 1800,
  loop = true,
  cursor = true,
  className = '',
}) => {
  const [text, setText] = useState('');
  const [wordIdx, setWordIdx] = useState(0);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (!words.length) return undefined;
    const word = words[wordIdx % words.length];
    let timer;

    if (!deleting && text === word) {
      if (loop) timer = setTimeout(() => setDeleting(true), pauseMs);
    } else if (deleting && text === '') {
      setDeleting(false);
      setWordIdx((i) => (i + 1) % words.length);
    } else {
      timer = setTimeout(
        () => setText(word.slice(0, text.length + (deleting ? -1 : 1))),
        deleting ? deletingSpeed : typingSpeed
      );
    }
    return () => clearTimeout(timer);
  }, [text, deleting, wordIdx, words, typingSpeed, deletingSpeed, pauseMs, loop]);

  return (
    <span
      className={cn('inline-flex items-center font-mono', className)}
      aria-label={words.join(', ')}
    >
      <span aria-hidden="true">{text}</span>
      {cursor && (
        <span
          aria-hidden="true"
          className="ml-0.5 inline-block h-[1em] w-[2px] animate-pulse self-center bg-current"
        >
          &nbsp;
        </span>
      )}
    </span>
  );
};

Typewriter.displayName = 'Typewriter';

export default Typewriter;
