import { SiteFooter } from '@/components/layout/site-footer';

/** Adds the marketing footer to every route inside this group. */
export default function FooterLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      {children}
      <SiteFooter />
    </>
  );
}
