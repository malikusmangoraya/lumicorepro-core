import React from 'react';
import { cn } from '../../utils';

/**
 * Minimal accessible table primitive. Cells accept primitives or React nodes.
 */
const Table = ({ head = [], rows = [], className = '', caption }) => (
  <div className={cn('w-full overflow-x-auto rounded-xl border border-border', className)}>
    <table className="w-full text-left text-sm">
      {caption && <caption className="sr-only">{caption}</caption>}
      {head.length > 0 && (
        <thead>
          <tr className="border-b border-border bg-muted/40">
            {head.map((h, i) => (
              <th key={i} scope="col" className="px-4 py-2.5 font-semibold text-muted-foreground whitespace-nowrap">
                {h}
              </th>
            ))}
          </tr>
        </thead>
      )}
      <tbody>
        {rows.map((row, i) => (
          <tr key={i} className="border-b border-border last:border-0 hover:bg-muted/30">
            {row.map((cell, j) => (
              <td key={j} className={cn('px-4 py-2.5 align-middle', typeof cell !== 'string' && 'whitespace-nowrap')}>
                {cell}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

export default Table;