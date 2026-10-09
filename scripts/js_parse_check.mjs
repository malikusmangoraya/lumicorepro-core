#!/usr/bin/env node
/**
 * Parse-check every JavaScript file passed as an argument using Node's real ESM
 * parser, WITHOUT executing the module. This is the only way to know that a
 * shipped backend actually parses — Python's compile() cannot read JavaScript,
 * and `node --check` rejects top-level `import` in .js files.
 *
 * Usage:  node --experimental-vm-modules scripts/js_parse_check.mjs <file...>
 * Output: one JSON object on stdout: { checked, failed, failures: [{file, line, message}] }
 * Exit:   1 when at least one file fails to parse.
 */
import vm from 'node:vm';
import { readFileSync } from 'node:fs';
import process from 'node:process';

const files = process.argv.slice(2);
const failures = [];

for (const file of files) {
  let source;
  try {
    source = readFileSync(file, 'utf8');
  } catch (err) {
    failures.push({ file, line: 0, message: `unreadable: ${err.message}` });
    continue;
  }
  try {
    // SourceTextModule parses the source and resolves its imports lazily;
    // constructing it performs a full parse and throws SyntaxError on bad
    // syntax, without running a single line of the module.
    new vm.SourceTextModule(source, { identifier: file });
  } catch (err) {
    const line = Number.isInteger(err.lineNumber) ? err.lineNumber : 0;
    failures.push({ file, line, message: err.message });
  }
}

process.stdout.write(
  JSON.stringify({ checked: files.length, failed: failures.length, failures }, null, 2),
);
process.exit(failures.length ? 1 : 0);