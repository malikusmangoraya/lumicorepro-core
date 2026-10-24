import { Outlet } from 'react-router-dom';

export default function AuthLayout() {
  return (
    <div className="min-h-screen bg-background text-foreground selection:bg-primary/20 selection:text-primary">
      <main id="main-content" role="main" aria-label="Authentication" className="px-4 py-12">
        <Outlet />
      </main>
    </div>
  );
}
