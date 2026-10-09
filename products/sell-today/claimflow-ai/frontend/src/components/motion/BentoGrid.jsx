import React from 'react';
import { motion } from 'framer-motion';

export default function BentoGrid({
  children,
  className = '',
  columns = { base: 1, md: 2, lg: 3 },
  gap = 6,
}) {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.5,
        ease: [0.25, 0.46, 0.45, 0.94],
      },
    },
  };

  return (
    <motion.div
      className={`grid gap-${gap} ${className}`}
      style={{
        gridTemplateColumns: `repeat(${columns.base}, 1fr)`,
      }}
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {React.Children.map(children, (child, index) => (
        <motion.div key={index} variants={itemVariants} className="relative">
          {child}
        </motion.div>
      ))}
    </motion.div>
  );
}

BentoGrid.Item = function BentoGridItem({
  children,
  className = '',
  span = { colSpan: 1, rowSpan: 1 },
  ...props
}) {
  return (
    <div
      className={`relative overflow-hidden rounded-2xl bg-slate-900/60 backdrop-blur border border-slate-800/80 hover:border-cyan-500/50 transition-all duration-300 ${className}`}
      style={{
        gridColumn: `span ${span.colSpan}`,
        gridRow: `span ${span.rowSpan}`,
      }}
      {...props}
    >
      {children}
    </div>
  );
};
