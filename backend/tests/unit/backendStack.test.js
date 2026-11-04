import { describe, it, expect } from '@jest/globals';
import * as aiAgentUtils from '../../utils/aiAgent.js';

describe('backend stack payload validation', () => {
  it('accepts valid selections and rejects malformed payloads', () => {
    const stack = { mode: 'manual', language: 'python', framework: 'fastapi' };

    expect(aiAgentUtils.validateBackendStackPayload(stack)).toEqual(stack);
    expect(aiAgentUtils.validateBackendStackPayload(undefined)).toBeUndefined();
    expect(() => aiAgentUtils.validateBackendStackPayload([])).toThrow(/backend_stack must be an object/);
    expect(() => aiAgentUtils.validateBackendStackPayload({ mode: 'automatic' })).toThrow(/backend_stack.mode/);
    expect(() => aiAgentUtils.validateBackendStackPayload({ language: '' })).toThrow(/backend_stack.language/);
    expect(() => aiAgentUtils.validateBackendStackPayload({ unknown: 'value' })).toThrow(/Unknown backend_stack field/);
  });
});

describe('technology choices payload validation', () => {
  it('accepts known fields and omits an absent selection', () => {
    const choices = {
      frontend_framework: 'nextjs',
      testing_tools: ['vitest', 'playwright'],
      quality_tools: [],
    };

    expect(aiAgentUtils.validateTechnologyChoicesPayload(choices)).toEqual(choices);
    expect(aiAgentUtils.validateTechnologyChoicesPayload(undefined)).toBeUndefined();
  });

  it.each([
    [],
    { unknown_field: 'nextjs' },
    { frontend_framework: '' },
    { frontend_framework: ['nextjs'] },
    { testing_tools: 'playwright' },
    { testing_tools: ['playwright', 42] },
    { quality_tools: [null] },
  ])('rejects malformed choices %j', (choices) => {
    expect(() => aiAgentUtils.validateTechnologyChoicesPayload(choices)).toThrow(
      /technology_choices/
    );
  });
});
