import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

export default function TextMorph({
  phrases = ['Innovate', 'Build', 'Scale', 'Succeed'],
  className = '',
  interval = 2000,
  typeSpeed = 80,
  deleteSpeed = 50,
  pauseTime = 1500,
  ...props
}) {
  const [phraseIndex, setPhraseIndex] = useState(0);
  const [text, setText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    let timeout;

    const type = () => {
      const currentPhrase = phrases[phraseIndex];

      if (isDeleting) {
        setText(currentPhrase.substring(0, text.length - 1));
      } else {
        setText(currentPhrase.substring(0, text.length + 1));
      }

      if (!isDeleting && text === currentPhrase) {
        setIsDeleting(true);
        timeout = setTimeout(() => setIsDeleting(true), pauseTime);
      } else if (isDeleting && text === '') {
        setIsDeleting(false);
        setPhraseIndex((prev) => (prev + 1) % phrases.length);
      }

      const speed = isDeleting ? deleteSpeed : typeSpeed;
      timeout = setTimeout(type, speed);
    };

    timeout = setTimeout(type, isDeleting ? deleteSpeed : typeSpeed);
    return () => clearTimeout(timeout);
  }, [text, isDeleting, phraseIndex, phrases, interval, typeSpeed, deleteSpeed, pauseTime]);

  return (
    <span
      className={`font-bold bg-gradient-to-r from-cyan-400 via-blue-500 to-violet-500 bg-clip-text text-transparent ${className}`}
      {...props}
    >
      <motion.span
        key={text}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        transition={{ duration: 0.2 }}
      >
        {text}
      </motion.span>
    </span>
  );
}
