import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

import { lintWorkflow } from '../../../scripts/check-workflows.mjs';

/**
 * `secrets.*` is not available in any `if:`, and a job-level `if:` also cannot
 * read `env.*` / `steps.*`. GitHub does not warn - it rejects the whole file and
 * reports "workflow file issue" with no log, which is how deploy.yml silently
 * stopped running. These tests pin the guard that catches it.
 */
describe('workflow if-context guard', () => {
  it('flags a job-level secrets condition', () => {
    const violations = lintWorkflow(
      [
        'jobs:',
        '  deploy:',
        '    if: ${{ secrets.VPS_HOST != \'\' }}',
        '    steps:',
        '      - run: echo ok',
      ].join('\n')
    );

    expect(violations).toHaveLength(1);
    expect(violations[0]).toMatchObject({ line: 3, context: 'secrets', jobLevel: true });
  });

  it('flags a step-level secrets condition', () => {
    const violations = lintWorkflow(
      [
        'jobs:',
        '  deploy:',
        '    steps:',
        '      - name: gate',
        '        if: ${{ secrets.TOKEN != \'\' }}',
        '        run: echo ok',
      ].join('\n')
    );

    expect(violations).toHaveLength(1);
    expect(violations[0]).toMatchObject({ line: 5, context: 'secrets', jobLevel: false });
  });

  it('flags job-level env/steps contexts but allows them on a step', () => {
    const violations = lintWorkflow(
      [
        'jobs:',
        '  a:',
        '    if: ${{ env.FLAG == \'1\' }}',
        '    steps:',
        '      - name: fine',
        '        if: ${{ env.FLAG == \'1\' }}',
        '        run: echo ok',
      ].join('\n')
    );

    expect(violations.map((v) => v.context)).toEqual(['env']);
    expect(violations[0].jobLevel).toBe(true);
  });

  it('ignores a shell if inside a run block', () => {
    const violations = lintWorkflow(
      [
        'jobs:',
        '  a:',
        '    steps:',
        '      - name: shell',
        '        run: |',
        '          if [ -n "${TOKEN}" ]; then',
        '            echo "secrets.NOT_A_CONTEXT"',
        '          fi',
      ].join('\n')
    );

    expect(violations).toEqual([]);
  });

  it('ignores a secret that is mapped into env', () => {
    const violations = lintWorkflow(
      [
        'jobs:',
        '  a:',
        '    steps:',
        '      - name: gate',
        '        env:',
        '          HOST: ${{ secrets.VPS_HOST }}',
        '        run: echo "$HOST"',
      ].join('\n')
    );

    expect(violations).toEqual([]);
  });

  it('finds no violation in the workflows this repo actually ships', () => {
    const dir = join(process.cwd(), '.github', 'workflows');
    const files = readdirSync(dir).filter((name) => /\.ya?ml$/i.test(name));

    expect(files.length).toBeGreaterThan(0);
    const violations = files.flatMap((name) =>
      lintWorkflow(readFileSync(join(dir, name), 'utf8'), name)
    );
    expect(violations).toEqual([]);
  });
});
