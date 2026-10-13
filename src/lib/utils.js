import { cn } from './cn';

/**
 * shadcn/ui resolves `@/lib/utils` for its `cn` helper. The implementation
 * lives in `./cn` (clsx + tailwind-merge) so both the CLI-generated components
 * and the existing design system share one class-merge function.
 */
export { cn };
export default cn;
