/**
 * util.mjs — file helpers for the upgrade engine.
 *
 * Lives in `lib/` as a dependency-free leaf so both the engine
 * (`scripts/upgrade/*`) and the rules (`scripts/upgrade/rules/*`) import it
 * downward. Keeping it out of either module breaks the
 * `scripts/upgrade <-> scripts/upgrade/rules` import cycle.
 *
 * Every writer preserves the dominant line ending of the target file, so a
 * generated block never turns into a whole-file CRLF/LF diff.
 */
import fs from 'node:fs';
import path from 'node:path';

export function detectEol(sample) {
  return typeof sample === 'string' && sample.includes('\r\n') ? '\r\n' : '\n';
}

/** Rewrite `text` to use the given line ending. */
export function withEol(text, eol) {
  const normalized = String(text).replace(/\r\n/g, '\n');
  return eol === '\r\n' ? normalized.replace(/\n/g, '\r\n') : normalized;
}

export function readIfExists(absPath) {
  try {
    return fs.readFileSync(absPath, 'utf8');
  } catch {
    return null;
  }
}

export function statIfExists(absPath) {
  try {
    return fs.statSync(absPath);
  } catch {
    return null;
  }
}

/** Append a marker-delimited block, keeping the file's existing line endings. */
export function appendBlock(source, block) {
  const eol = detectEol(source);
  const body = source.replace(/\s*$/, '');
  return `${body}${eol}${eol}${withEol(block.trim(), eol)}${eol}`;
}

/** Insert a block immediately before `anchor`, or append when it is missing. */
export function insertBefore(source, anchor, block) {
  const eol = detectEol(source);
  const at = source.lastIndexOf(anchor);
  if (at === -1) return appendBlock(source, block);
  const head = source.slice(0, at).replace(/\s*$/, '');
  const tail = source.slice(at).replace(/^\s*/, '');
  return `${head}${eol}${eol}${withEol(block.trim(), eol)}${eol}${eol}${tail}`;
}

export function writeFileEnsuringDir(absPath, content) {
  fs.mkdirSync(path.dirname(absPath), { recursive: true });
  fs.writeFileSync(absPath, content, 'utf8');
}
