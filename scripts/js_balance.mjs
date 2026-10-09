#!/usr/bin/env node
/**
 * Locate unbalanced brackets in a JavaScript source file.
 *
 * A naive `text.split('{')` counts braces inside strings, template literals,
 * comments and regex literals, which reports phantom problems. This walks the
 * source with a small state machine that skips all of those, then prints the
 * line where each nesting level returns to zero — which is where a genuinely
 * missing `}` shows up (the tail of the file never closes back to depth 0).
 *
 * Usage: node scripts/js_balance.mjs <file.js>
 * Exit:  0 balanced, 1 unbalanced, 2 usage error.
 */
import { readFileSync } from 'node:fs';
import process from 'node:process';

const OPEN = { '(': ')', '[': ']', '{': '}' };
const CLOSE = new Set([')', ']', '}']);
const PAIR = { ')': '(', ']': '[', '}': '{' };

const file = process.argv[2];
if (!file) {
  console.error('usage: node scripts/js_balance.mjs <file.js>');
  process.exit(2);
}

const src = readFileSync(file, 'utf8');

/** Can a `/` here start a regex literal rather than division? */
function regexAllowed(prevMeaningful) {
  if (!prevMeaningful) return true;
  return /[\)\]\}]/.test(prevMeaningful);
}

const stack = [];
let i = 0;
let line = 1;
let prevMeaningful = '';
let templateDepth = [];

while (i < src.length) {
  const ch = src[i];
  const next = src[i + 1];

  if (ch === '\n') {
    line += 1;
    i += 1;
    continue;
  }

  // Comments
  if (ch === '/' && next === '/') {
    while (i < src.length && src[i] !== '\n') i += 1;
    continue;
  }
  if (ch === '/' && next === '*') {
    i += 2;
    while (i < src.length && !(src[i] === '*' && src[i + 1] === '/')) {
      if (src[i] === '\n') line += 1;
      i += 1;
    }
    i += 2;
    continue;
  }

  // Strings
  if (ch === '"' || ch === "'") {
    const quote = ch;
    i += 1;
    while (i < src.length) {
      if (src[i] === '\\') { i += 2; continue; }
      if (src[i] === quote) { i += 1; break; }
      if (src[i] === '\n') line += 1;
      i += 1;
    }
    prevMeaningful = quote;
    continue;
  }

  // Template literals, including ${ } interpolation
  if (ch === '`') {
    templateDepth.push(line);
    i += 1;
    while (i < src.length) {
      if (src[i] === '\\') { i += 2; continue; }
      if (src[i] === '`') { templateDepth.pop(); i += 1; break; }
      if (src[i] === '$' && src[i + 1] === '{') {
        stack.push({ ch: '{', line });
        i += 2;
        // parse the interpolation expression with the same state machine
        let depth = 1;
        while (i < src.length && depth > 0) {
          const c = src[i];
          if (c === '\n') line += 1;
          if (c === '{') depth += 1;
          else if (c === '}') depth -= 1;
          else if (c === '"' || c === "'" || c === '`') {
            const q = c;
            i += 1;
            while (i < src.length && src[i] !== q) {
              if (src[i] === '\\') i += 1;
              i += 1;
            }
          }
          i += 1;
        }
        stack.pop();
        continue;
      }
      i += 1;
    }
    prevMeaningful = '`';
    continue;
  }

  // Regex literals
  if (ch === '/' && regexAllowed(prevMeaningful)) {
    let j = i + 1;
    let inClass = false;
    let closed = false;
    while (j < src.length) {
      const c = src[j];
      if (c === '\\') { j += 2; continue; }
      if (c === '[') inClass = true;
      else if (c === ']') inClass = false;
      else if (c === '/' && !inClass) { closed = true; break; }
      else if (c === '\n') break;
      j += 1;
    }
    if (closed) {
      j += 1;
      while (j < src.length && /[a-z]/.test(src[j])) j += 1;
      i = j;
      prevMeaningful = '/re/';
      continue;
    }
  }

  if (OPEN[ch]) {
    stack.push({ ch, line });
    prevMeaningful = ch;
    i += 1;
    continue;
  }

  if (CLOSE.has(ch)) {
    const top = stack.pop();
    if (!top) {
      console.error(`unmatched '${ch}' at line ${line}`);
      process.exit(1);
    }
    if (top.ch !== PAIR[ch]) {
      console.error(
        `mismatch: '${top.ch}' opened at line ${top.line} closed by '${ch}' at line ${line}`,
      );
      process.exit(1);
    }
    prevMeaningful = ch;
    i += 1;
    continue;
  }

  if (!/\s/.test(ch)) prevMeaningful = ch;
  i += 1;
}

if (stack.length) {
  console.error(`UNCLOSED: ${stack.length} bracket(s) still open at end of file`);
  for (const s of stack.slice(-6)) {
    console.error(`  '${s.ch}' opened at line ${s.line}`);
  }
  process.exit(1);
}

console.log('BALANCED');