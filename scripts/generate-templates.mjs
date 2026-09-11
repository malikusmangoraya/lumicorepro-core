/**
 * Generates Phase 4 templates (run once): node scripts/generate-templates.mjs
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, '..', 'src', 'templates');

function write(file, content) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, content.trimStart());
}

const catalog = [
  // Dashboard
  {
    cat: 'dashboard',
    id: 'DashboardOverview',
    path: 'dashboard/DashboardOverview',
    title: 'Dashboard Overview',
    description: 'Key metrics, activity, and quick actions.',
    category: 'Dashboard',
  },
  {
    cat: 'dashboard',
    id: 'UsersManagement',
    path: 'dashboard/UsersManagement',
    title: 'Users Management',
    description: 'Search, filter, and manage team members.',
    category: 'Dashboard',
  },
  {
    cat: 'dashboard',
    id: 'Analytics',
    path: 'dashboard/Analytics',
    title: 'Analytics',
    description: 'Traffic and conversion at a glance.',
    category: 'Dashboard',
  },
  {
    cat: 'dashboard',
    id: 'Settings',
    path: 'dashboard/Settings',
    title: 'Settings',
    description: 'General, security, and notifications.',
    category: 'Dashboard',
  },
  {
    cat: 'dashboard',
    id: 'Profile',
    path: 'dashboard/Profile',
    title: 'Profile',
    description: 'Your identity, security, and activity.',
    category: 'Dashboard',
  },
  // Ecommerce
  {
    cat: 'ecommerce',
    id: 'ProductListing',
    path: 'ecommerce/ProductListing',
    title: 'Product Listing',
    description: 'Browse, filter, and sort products.',
    category: 'E-Commerce',
  },
  {
    cat: 'ecommerce',
    id: 'ProductDetails',
    path: 'ecommerce/ProductDetails',
    title: 'Product Details',
    description: 'Gallery, variants, and purchase actions.',
    category: 'E-Commerce',
  },
  {
    cat: 'ecommerce',
    id: 'ShoppingCart',
    path: 'ecommerce/ShoppingCart',
    title: 'Shopping Cart',
    description: 'Review items and totals before checkout.',
    category: 'E-Commerce',
  },
  {
    cat: 'ecommerce',
    id: 'Checkout',
    path: 'ecommerce/Checkout',
    title: 'Checkout',
    description: 'Shipping, payment, and order review.',
    category: 'E-Commerce',
  },
  {
    cat: 'ecommerce',
    id: 'OrdersHistory',
    path: 'ecommerce/OrdersHistory',
    title: 'Orders History',
    description: 'Track and revisit past orders.',
    category: 'E-Commerce',
  },
  // AI
  {
    cat: 'ai',
    id: 'ChatInterface',
    path: 'ai/ChatInterface',
    title: 'AI Chat',
    description: 'Clean conversation UI with typing state.',
    category: 'AI',
  },
  {
    cat: 'ai',
    id: 'AIGenerator',
    path: 'ai/AIGenerator',
    title: 'AI Generator',
    description: 'Prompt in, polished output out.',
    category: 'AI',
  },
  {
    cat: 'ai',
    id: 'UsageDashboard',
    path: 'ai/UsageDashboard',
    title: 'Usage Dashboard',
    description: 'Tokens, requests, and plan limits.',
    category: 'AI',
  },
  {
    cat: 'ai',
    id: 'ModelSelection',
    path: 'ai/ModelSelection',
    title: 'Model Selection',
    description: 'Compare models and pick one.',
    category: 'AI',
  },
  {
    cat: 'ai',
    id: 'GenerationHistory',
    path: 'ai/GenerationHistory',
    title: 'Generation History',
    description: 'Search and reuse past generations.',
    category: 'AI',
  },
  // Business
  {
    cat: 'business',
    id: 'LandingPage',
    path: 'business/LandingPage',
    title: 'Landing Page',
    description: 'Hero, features, pricing teaser, CTA.',
    category: 'Business',
  },
  {
    cat: 'business',
    id: 'ServicesPage',
    path: 'business/ServicesPage',
    title: 'Services',
    description: 'Service cards with clear next steps.',
    category: 'Business',
  },
  {
    cat: 'business',
    id: 'PortfolioPage',
    path: 'business/PortfolioPage',
    title: 'Portfolio',
    description: 'Filterable project grid.',
    category: 'Business',
  },
  {
    cat: 'business',
    id: 'PricingPage',
    path: 'business/PricingPage',
    title: 'Pricing',
    description: 'Simple tiers with monthly/yearly toggle.',
    category: 'Business',
  },
  {
    cat: 'business',
    id: 'ContactPage',
    path: 'business/ContactPage',
    title: 'Contact',
    description: 'Validated inquiry form and contact info.',
    category: 'Business',
  },
];

const bodies = {
  DashboardOverview: `import { TrendingUp, Users, ShoppingBag, Activity } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, CardContent, Badge, Button, Progress } from '@/components/ui';
import { stats, activity } from './data/mockData';

const icons = { users: Users, revenue: TrendingUp, orders: ShoppingBag, growth: Activity };

export default function DashboardOverview() {
  return (
    <TemplateShell
      title="Dashboard Overview"
      description="Key metrics, activity, and quick actions."
      category="Dashboard"
      actions={<Button size="sm">Export</Button>}
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s, i) => {
          const Icon = icons[s.key];
          return (
            <Card key={s.key} animate="fade-up" animationDelay={i * 75} className="hover-lift" padding="md">
              <CardContent className="flex items-start justify-between gap-3 p-0">
                <div>
                  <p className="text-sm text-muted-foreground">{s.label}</p>
                  <p className="mt-1 font-display text-2xl font-bold">{s.value}</p>
                  <Badge variant={s.delta.startsWith('+') ? 'success' : 'danger'} size="sm" className="mt-2">
                    {s.delta}
                  </Badge>
                </div>
                <div className="rounded-lg bg-primary/10 p-2 text-primary">
                  <Icon className="h-5 w-5" />
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
      <div className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2" animate="fade-up" animationDelay={200}>
          <h3 className="font-display font-semibold mb-4">Revenue pace</h3>
          <Progress value={72} showLabel label="Monthly goal" />
          <div className="mt-6 flex h-32 items-end gap-2">
            {[40, 55, 48, 70, 62, 80, 74, 88, 76, 92, 85, 96].map((h, i) => (
              <div key={i} className="flex-1 rounded-t bg-primary/80 transition-all hover:bg-primary" style={{ height: \`\${h}%\` }} />
            ))}
          </div>
        </Card>
        <Card animate="fade-up" animationDelay={250}>
          <h3 className="font-display font-semibold mb-4">Activity</h3>
          <ul className="space-y-3">
            {activity.map((a) => (
              <li key={a.id} className="flex gap-3 text-sm">
                <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-primary shrink-0" />
                <div>
                  <p className="text-foreground">{a.text}</p>
                  <p className="text-xs text-muted-foreground">{a.time}</p>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </TemplateShell>
  );
}
`,

  UsersManagement: `import { useMemo, useState } from 'react';
import { Search, Plus } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Button, Badge, Input, Avatar, Empty } from '@/components/ui';
import { users as seed } from './data/mockData';
import useDebounce from '@/hooks/useDebounce';

export default function UsersManagement() {
  const [query, setQuery] = useState('');
  const [users] = useState(seed);
  const q = useDebounce(query, 200);
  const filtered = useMemo(
    () => users.filter((u) => \`\${u.name} \${u.email}\`.toLowerCase().includes(q.toLowerCase())),
    [users, q]
  );

  return (
    <TemplateShell
      title="Users Management"
      description="Search, filter, and manage team members."
      category="Dashboard"
      actions={<Button size="sm" leftIcon={Plus}>Add user</Button>}
    >
      <Card padding="md">
        <div className="mb-4 max-w-sm">
          <Input leftIcon={Search} placeholder="Search users…" value={query} onChange={(e) => setQuery(e.target.value)} />
        </div>
        {filtered.length === 0 ? (
          <Empty title="No users found" description="Try another search." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-muted-foreground">
                  <th className="pb-3 font-medium">User</th>
                  <th className="pb-3 font-medium">Role</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((u, i) => (
                  <tr key={u.id} className="border-b border-border/60 animate-fade-in-up" style={{ animationDelay: \`\${i * 40}ms\` }}>
                    <td className="py-3">
                      <div className="flex items-center gap-3">
                        <Avatar name={u.name} size="sm" />
                        <div>
                          <p className="font-medium">{u.name}</p>
                          <p className="text-xs text-muted-foreground">{u.email}</p>
                        </div>
                      </div>
                    </td>
                    <td><Badge variant="secondary" size="sm">{u.role}</Badge></td>
                    <td><Badge variant={u.status === 'active' ? 'success' : 'warning'} size="sm" dot>{u.status}</Badge></td>
                    <td className="text-right">
                      <Button variant="ghost" size="sm">Edit</Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </TemplateShell>
  );
}
`,

  Analytics: `import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button } from '@/components/ui';
import { metrics, series } from './data/mockData';
import { Download } from 'lucide-react';

export default function Analytics() {
  const max = Math.max(...series.map((s) => s.value));
  return (
    <TemplateShell
      title="Analytics"
      description="Traffic and conversion at a glance."
      category="Dashboard"
      actions={<Button size="sm" variant="outline" leftIcon={Download}>Export CSV</Button>}
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {metrics.map((m, i) => (
          <Card key={m.label} animate="fade-up" animationDelay={i * 60} className="hover-lift">
            <p className="text-sm text-muted-foreground">{m.label}</p>
            <p className="mt-1 font-display text-2xl font-bold">{m.value}</p>
            <Badge variant="info" size="sm" className="mt-2">{m.change}</Badge>
          </Card>
        ))}
      </div>
      <Card animate="fade-up" animationDelay={200}>
        <h3 className="font-display font-semibold mb-6">Visitors (7 days)</h3>
        <div className="flex h-48 items-end gap-3">
          {series.map((s) => (
            <div key={s.day} className="flex-1 flex flex-col items-center gap-2">
              <div
                className="w-full rounded-t-lg bg-primary/85 transition-all duration-300 hover:bg-primary hover-glow"
                style={{ height: \`\${(s.value / max) * 100}%\` }}
                title={\`\${s.value}\`}
              />
              <span className="text-xs text-muted-foreground">{s.day}</span>
            </div>
          ))}
        </div>
      </Card>
    </TemplateShell>
  );
}
`,

  Settings: `import { useState } from 'react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Button, Input, Switch, Divider } from '@/components/ui';
import { sections } from './data/mockData';

export default function Settings() {
  const [tab, setTab] = useState('general');
  const [emailAlerts, setEmailAlerts] = useState(true);
  return (
    <TemplateShell title="Settings" description="General, security, and notifications." category="Dashboard">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <Card padding="sm" className="h-fit">
          <nav className="flex lg:flex-col gap-1">
            {sections.map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => setTab(s.id)}
                className={\`rounded-lg px-3 py-2 text-sm text-left transition-colors \${
                  tab === s.id ? 'bg-primary text-primary-foreground' : 'hover:bg-muted text-muted-foreground'
                }\`}
              >
                {s.label}
              </button>
            ))}
          </nav>
        </Card>
        <Card className="lg:col-span-3 animate-fade-in" key={tab}>
          {tab === 'general' && (
            <div className="space-y-4 max-w-lg">
              <Input label="Workspace name" defaultValue="LumicorePro" />
              <Input label="Support email" type="email" defaultValue="hello@lumicore.pro" />
              <Button>Save changes</Button>
            </div>
          )}
          {tab === 'security' && (
            <div className="space-y-4 max-w-lg">
              <Input label="Current password" type="password" />
              <Input label="New password" type="password" />
              <Button variant="secondary">Update password</Button>
            </div>
          )}
          {tab === 'notifications' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Email alerts</p>
                  <p className="text-sm text-muted-foreground">Product and billing updates</p>
                </div>
                <Switch checked={emailAlerts} onChange={setEmailAlerts} />
              </div>
              <Divider />
              <Button size="sm">Save preferences</Button>
            </div>
          )}
          {tab === 'danger' && (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">Permanently delete this workspace and all data.</p>
              <Button variant="danger">Delete workspace</Button>
            </div>
          )}
        </Card>
      </div>
    </TemplateShell>
  );
}
`,

  Profile: `import TemplateShell from '../../_shared/TemplateShell';
import { Card, Button, Input, Avatar, Badge } from '@/components/ui';
import { profile, activity } from './data/mockData';

export default function Profile() {
  return (
    <TemplateShell title="Profile" description="Your identity, security, and activity." category="Dashboard">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="text-center" animate="scale">
          <Avatar name={profile.name} size="xl" className="mx-auto" />
          <h2 className="mt-4 font-display text-xl font-semibold">{profile.name}</h2>
          <p className="text-sm text-muted-foreground">{profile.email}</p>
          <Badge className="mt-3" variant="info">{profile.role}</Badge>
          <Button className="mt-6 w-full" variant="outline" size="sm">Change avatar</Button>
        </Card>
        <Card className="lg:col-span-2 space-y-4" animate="fade-up">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="Full name" defaultValue={profile.name} />
            <Input label="Email" type="email" defaultValue={profile.email} />
            <Input label="Title" defaultValue={profile.title} />
            <Input label="Location" defaultValue={profile.location} />
          </div>
          <Button>Save profile</Button>
          <div className="pt-4 border-t border-border">
            <h3 className="font-display font-semibold mb-3">Recent activity</h3>
            <ul className="space-y-2">
              {activity.map((a) => (
                <li key={a.id} className="text-sm text-muted-foreground flex justify-between gap-4">
                  <span>{a.text}</span>
                  <span className="shrink-0">{a.time}</span>
                </li>
              ))}
            </ul>
          </div>
        </Card>
      </div>
    </TemplateShell>
  );
}
`,

  ProductListing: `import { useMemo, useState } from 'react';
import { Search, Star } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Button, Badge, Input } from '@/components/ui';
import { products, categories } from './data/mockData';
import useDebounce from '@/hooks/useDebounce';

export default function ProductListing() {
  const [query, setQuery] = useState('');
  const [cat, setCat] = useState('all');
  const q = useDebounce(query);
  const list = useMemo(
    () =>
      products.filter(
        (p) =>
          (cat === 'all' || p.category === cat) &&
          p.name.toLowerCase().includes(q.toLowerCase())
      ),
    [q, cat]
  );

  return (
    <TemplateShell title="Product Listing" description="Browse, filter, and sort products." category="E-Commerce">
      <div className="flex flex-col md:flex-row gap-6">
        <aside className="md:w-48 shrink-0 space-y-2">
          {categories.map((c) => (
            <button
              key={c.id}
              type="button"
              onClick={() => setCat(c.id)}
              className={\`w-full rounded-lg px-3 py-2 text-left text-sm transition-colors \${
                cat === c.id ? 'bg-primary text-primary-foreground' : 'hover:bg-muted text-muted-foreground'
              }\`}
            >
              {c.label}
            </button>
          ))}
        </aside>
        <div className="flex-1 space-y-4">
          <Input leftIcon={Search} placeholder="Search products…" value={query} onChange={(e) => setQuery(e.target.value)} />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {list.map((p, i) => (
              <Card key={p.id} hoverable animate="fade-up" animationDelay={i * 50} className="overflow-hidden" padding="none">
                <div className="aspect-[4/3] bg-gradient-to-br from-primary/15 to-muted" />
                <div className="p-4">
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-semibold">{p.name}</h3>
                    <Badge size="sm" variant="secondary">{p.category}</Badge>
                  </div>
                  <div className="mt-2 flex items-center gap-1 text-sm text-muted-foreground">
                    <Star className="h-3.5 w-3.5 fill-primary text-primary" />
                    {p.rating}
                  </div>
                  <div className="mt-4 flex items-center justify-between">
                    <span className="font-display text-lg font-bold">\${p.price}</span>
                    <Button size="sm">Add</Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </TemplateShell>
  );
}
`,

  ProductDetails: `import { useState } from 'react';
import { Heart, Star } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Button, Badge } from '@/components/ui';
import { product } from './data/mockData';

export default function ProductDetails() {
  const [qty, setQty] = useState(1);
  const [size, setSize] = useState(product.sizes[0]);
  return (
    <TemplateShell title="Product Details" description="Gallery, variants, and purchase actions." category="E-Commerce">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card padding="none" className="overflow-hidden animate-scale-in">
          <div className="aspect-square bg-gradient-to-br from-primary/20 via-muted to-primary/5" />
        </Card>
        <div className="space-y-5 animate-fade-in-up">
          <Badge variant="info">{product.category}</Badge>
          <h2 className="font-display text-3xl font-bold">{product.name}</h2>
          <div className="flex items-center gap-2 text-sm">
            <Star className="h-4 w-4 fill-primary text-primary" />
            {product.rating} · {product.reviews} reviews
          </div>
          <p className="font-display text-3xl font-bold text-primary">\${product.price}</p>
          <p className="text-muted-foreground leading-relaxed">{product.description}</p>
          <div>
            <p className="text-sm font-medium mb-2">Size</p>
            <div className="flex gap-2">
              {product.sizes.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setSize(s)}
                  className={\`h-10 w-10 rounded-lg border text-sm transition-all \${
                    size === s ? 'border-primary bg-primary text-primary-foreground' : 'border-border hover:border-primary/50'
                  }\`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="inline-flex items-center rounded-lg border border-border">
              <Button variant="ghost" size="sm" onClick={() => setQty(Math.max(1, qty - 1))}>-</Button>
              <span className="w-10 text-center text-sm">{qty}</span>
              <Button variant="ghost" size="sm" onClick={() => setQty(qty + 1)}>+</Button>
            </div>
            <Button className="flex-1">Add to cart</Button>
            <Button variant="outline" aria-label="Wishlist"><Heart className="h-4 w-4" /></Button>
          </div>
        </div>
      </div>
    </TemplateShell>
  );
}
`,

  ShoppingCart: `import { useState } from 'react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Button, Input, Empty } from '@/components/ui';
import { items as seed } from './data/mockData';

export default function ShoppingCart() {
  const [items, setItems] = useState(seed);
  const subtotal = items.reduce((s, i) => s + i.price * i.qty, 0);
  const update = (id, qty) => setItems((prev) => prev.map((i) => (i.id === id ? { ...i, qty: Math.max(1, qty) } : i)));
  const remove = (id) => setItems((prev) => prev.filter((i) => i.id !== id));

  return (
    <TemplateShell title="Shopping Cart" description="Review items and totals before checkout." category="E-Commerce">
      {items.length === 0 ? (
        <Empty title="Cart is empty" description="Add products to continue." action={<Button>Browse products</Button>} />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-3">
            {items.map((item, i) => (
              <Card key={item.id} className="flex gap-4 items-center hover-lift" animate="fade-up" animationDelay={i * 60}>
                <div className="h-16 w-16 rounded-lg bg-muted shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{item.name}</p>
                  <p className="text-sm text-muted-foreground">\${item.price}</p>
                </div>
                <div className="inline-flex items-center rounded-lg border border-border">
                  <Button variant="ghost" size="sm" onClick={() => update(item.id, item.qty - 1)}>-</Button>
                  <span className="w-8 text-center text-sm">{item.qty}</span>
                  <Button variant="ghost" size="sm" onClick={() => update(item.id, item.qty + 1)}>+</Button>
                </div>
                <Button variant="ghost" size="sm" onClick={() => remove(item.id)}>Remove</Button>
              </Card>
            ))}
          </div>
          <Card className="h-fit space-y-4" animate="fade-up" animationDelay={150}>
            <h3 className="font-display font-semibold">Summary</h3>
            <Input placeholder="Coupon code" />
            <div className="flex justify-between text-sm"><span className="text-muted-foreground">Subtotal</span><span>\${subtotal.toFixed(2)}</span></div>
            <div className="flex justify-between text-sm"><span className="text-muted-foreground">Shipping</span><span>$8.00</span></div>
            <div className="flex justify-between font-semibold text-lg border-t border-border pt-3"><span>Total</span><span>\${(subtotal + 8).toFixed(2)}</span></div>
            <Button className="w-full">Checkout</Button>
          </Card>
        </div>
      )}
    </TemplateShell>
  );
}
`,

  Checkout: `import { useState } from 'react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Button, Input, Progress } from '@/components/ui';
import { steps } from './data/mockData';

export default function Checkout() {
  const [step, setStep] = useState(0);
  return (
    <TemplateShell title="Checkout" description="Shipping, payment, and order review." category="E-Commerce">
      <Progress value={((step + 1) / steps.length) * 100} className="mb-6" showLabel label={steps[step]} />
      <Card className="max-w-xl mx-auto space-y-4 animate-fade-in" key={step}>
        {step === 0 && (
          <>
            <Input label="Full name" placeholder="Alex Rivera" />
            <Input label="Address" placeholder="123 Main St" />
            <Input label="City" placeholder="Austin" />
          </>
        )}
        {step === 1 && (
          <>
            <Input label="Card number" placeholder="4242 4242 4242 4242" />
            <div className="grid grid-cols-2 gap-3">
              <Input label="Expiry" placeholder="12/28" />
              <Input label="CVC" placeholder="123" />
            </div>
          </>
        )}
        {step === 2 && (
          <div className="space-y-2 text-sm text-muted-foreground">
            <p>Review your shipping and payment details, then place the order.</p>
            <p className="text-foreground font-medium">Order total: $97.00</p>
          </div>
        )}
        {step === 3 && (
          <div className="text-center py-6 animate-scale-in">
            <p className="font-display text-2xl font-bold text-primary">Order placed</p>
            <p className="mt-2 text-muted-foreground">Confirmation sent to your email.</p>
          </div>
        )}
        <div className="flex justify-between pt-2">
          <Button variant="ghost" disabled={step === 0} onClick={() => setStep((s) => s - 1)}>Back</Button>
          {step < steps.length - 1 ? (
            <Button onClick={() => setStep((s) => s + 1)}>{step === 2 ? 'Place order' : 'Continue'}</Button>
          ) : (
            <Button variant="secondary">Done</Button>
          )}
        </div>
      </Card>
    </TemplateShell>
  );
}
`,

  OrdersHistory: `import { useState } from 'react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button } from '@/components/ui';
import { orders, filters } from './data/mockData';

export default function OrdersHistory() {
  const [filter, setFilter] = useState('all');
  const list = orders.filter((o) => filter === 'all' || o.status === filter);
  const tone = { delivered: 'success', shipped: 'info', pending: 'warning', cancelled: 'danger' };
  return (
    <TemplateShell title="Orders History" description="Track and revisit past orders." category="E-Commerce">
      <div className="flex flex-wrap gap-2 mb-4">
        {filters.map((f) => (
          <Button key={f.id} size="sm" variant={filter === f.id ? 'primary' : 'outline'} onClick={() => setFilter(f.id)}>
            {f.label}
          </Button>
        ))}
      </div>
      <div className="space-y-3">
        {list.map((o, i) => (
          <Card key={o.id} className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover-lift" animate="fade-up" animationDelay={i * 50}>
            <div>
              <p className="font-medium">{o.id}</p>
              <p className="text-sm text-muted-foreground">{o.date} · {o.items} items</p>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant={tone[o.status]}>{o.status}</Badge>
              <span className="font-semibold">\${o.total}</span>
              <Button size="sm" variant="ghost">Details</Button>
            </div>
          </Card>
        ))}
      </div>
    </TemplateShell>
  );
}
`,

  ChatInterface: `import { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Button, Input } from '@/components/ui';
import { messages as seed } from './data/mockData';

export default function ChatInterface() {
  const [messages, setMessages] = useState(seed);
  const [text, setText] = useState('');
  const [typing, setTyping] = useState(false);
  const endRef = useRef(null);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, typing]);

  const send = () => {
    if (!text.trim()) return;
    const userMsg = { id: Date.now(), role: 'user', text };
    setMessages((m) => [...m, userMsg]);
    setText('');
    setTyping(true);
    setTimeout(() => {
      setMessages((m) => [...m, { id: Date.now() + 1, role: 'ai', text: 'Got it. Here is a clear, concise answer based on your prompt.' }]);
      setTyping(false);
    }, 900);
  };

  return (
    <TemplateShell title="AI Chat" description="Clean conversation UI with typing state." category="AI">
      <Card className="flex flex-col h-[560px]" padding="none">
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.map((m) => (
            <div key={m.id} className={\`flex \${m.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in-up\`}>
              <div className={\`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm \${
                m.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted text-foreground'
              }\`}>
                {m.text}
              </div>
            </div>
          ))}
          {typing && (
            <div className="text-sm text-muted-foreground animate-pulse">Lumicore is typing…</div>
          )}
          <div ref={endRef} />
        </div>
        <div className="border-t border-border p-3 flex gap-2">
          <Input
            placeholder="Ask anything…"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && send()}
          />
          <Button onClick={send} aria-label="Send" leftIcon={Send}>Send</Button>
        </div>
      </Card>
    </TemplateShell>
  );
}
`,

  AIGenerator: `import { useState } from 'react';
import { Copy, Sparkles } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Button, Input, Textarea, Badge } from '@/components/ui';
import { models } from './data/mockData';

export default function AIGenerator() {
  const [prompt, setPrompt] = useState('');
  const [model, setModel] = useState(models[0]);
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);

  const generate = () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setTimeout(() => {
      setResult(\`## Result (\\\${model})\\n\\n\${prompt}\\n\\n— Generated with a clean, production-ready tone.\`);
      setLoading(false);
    }, 800);
  };

  return (
    <TemplateShell title="AI Generator" description="Prompt in, polished output out." category="AI">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="space-y-4" animate="fade-up">
          <div className="flex flex-wrap gap-2">
            {models.map((m) => (
              <Badge key={m} variant={model === m ? 'default' : 'outline'} onClick={() => setModel(m)} className="cursor-pointer">{m}</Badge>
            ))}
          </div>
          <Textarea label="Prompt" rows={6} value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="Describe what you need…" />
          <Button loading={loading} leftIcon={Sparkles} onClick={generate} className="w-full">Generate</Button>
        </Card>
        <Card animate="fade-up" animationDelay={100}>
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-display font-semibold">Output</h3>
            <Button size="sm" variant="ghost" leftIcon={Copy} disabled={!result} onClick={() => navigator.clipboard.writeText(result)}>Copy</Button>
          </div>
          <pre className="whitespace-pre-wrap text-sm text-muted-foreground min-h-[200px]">{result || 'Your generation will appear here.'}</pre>
        </Card>
      </div>
    </TemplateShell>
  );
}
`,

  UsageDashboard: `import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button, Progress } from '@/components/ui';
import { metrics, usage } from './data/mockData';

export default function UsageDashboard() {
  return (
    <TemplateShell title="Usage Dashboard" description="Tokens, requests, and plan limits." category="AI" actions={<Button size="sm">Upgrade</Button>}>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        {metrics.map((m, i) => (
          <Card key={m.label} animate="fade-up" animationDelay={i * 60} className="hover-lift">
            <p className="text-sm text-muted-foreground">{m.label}</p>
            <p className="mt-1 font-display text-2xl font-bold">{m.value}</p>
            <Badge size="sm" variant="secondary" className="mt-2">{m.hint}</Badge>
          </Card>
        ))}
      </div>
      <Card animate="fade-up" animationDelay={150}>
        <h3 className="font-display font-semibold mb-4">Monthly allowance</h3>
        <Progress value={usage.percent} showLabel label={\`\${usage.used.toLocaleString()} / \${usage.limit.toLocaleString()} tokens\`} />
      </Card>
    </TemplateShell>
  );
}
`,

  ModelSelection: `import { useState } from 'react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Button, Badge } from '@/components/ui';
import { models } from './data/mockData';
import { Check } from 'lucide-react';

export default function ModelSelection() {
  const [selected, setSelected] = useState(models[1].id);
  return (
    <TemplateShell title="Model Selection" description="Compare models and pick one." category="AI">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {models.map((m, i) => (
          <Card
            key={m.id}
            animate="fade-up"
            animationDelay={i * 75}
            className={\`cursor-pointer transition-all \${selected === m.id ? 'border-primary shadow-md' : 'hover:border-primary/40'}\`}
            onClick={() => setSelected(m.id)}
          >
            <div className="flex items-start justify-between gap-2">
              <h3 className="font-display font-semibold">{m.name}</h3>
              {m.popular && <Badge size="sm">Popular</Badge>}
            </div>
            <p className="mt-2 text-sm text-muted-foreground">{m.blurb}</p>
            <p className="mt-4 font-display text-xl font-bold">\${m.price}<span className="text-sm font-normal text-muted-foreground">/1M tok</span></p>
            <ul className="mt-4 space-y-2">
              {m.features.map((f) => (
                <li key={f} className="flex gap-2 text-sm text-muted-foreground">
                  <Check className="h-4 w-4 text-primary shrink-0" />{f}
                </li>
              ))}
            </ul>
            <Button className="mt-6 w-full" variant={selected === m.id ? 'primary' : 'outline'}>
              {selected === m.id ? 'Selected' : 'Select'}
            </Button>
          </Card>
        ))}
      </div>
    </TemplateShell>
  );
}
`,

  GenerationHistory: `import { useMemo, useState } from 'react';
import { Search } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Button, Input, Badge, Empty } from '@/components/ui';
import { history } from './data/mockData';
import useDebounce from '@/hooks/useDebounce';

export default function GenerationHistory() {
  const [query, setQuery] = useState('');
  const q = useDebounce(query);
  const list = useMemo(() => history.filter((h) => h.prompt.toLowerCase().includes(q.toLowerCase())), [q]);
  return (
    <TemplateShell title="Generation History" description="Search and reuse past generations." category="AI">
      <div className="mb-4 max-w-md">
        <Input leftIcon={Search} placeholder="Search prompts…" value={query} onChange={(e) => setQuery(e.target.value)} />
      </div>
      {list.length === 0 ? (
        <Empty title="No results" />
      ) : (
        <div className="space-y-3">
          {list.map((h, i) => (
            <Card key={h.id} className="flex flex-col sm:flex-row sm:items-center justify-between gap-3" animate="fade-up" animationDelay={i * 40}>
              <div className="min-w-0">
                <p className="font-medium truncate">{h.prompt}</p>
                <p className="text-xs text-muted-foreground mt-1">{h.date} · {h.model}</p>
              </div>
              <div className="flex items-center gap-2">
                <Badge size="sm" variant="secondary">{h.status}</Badge>
                <Button size="sm" variant="ghost">Reuse</Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </TemplateShell>
  );
}
`,

  LandingPage: `import { ArrowRight, Zap, Shield, LayoutDashboard } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Button, Card } from '@/components/ui';
import { features } from './data/mockData';

const icons = [Zap, Shield, LayoutDashboard];

export default function LandingPage() {
  return (
    <TemplateShell title="Landing Page" description="Hero, features, pricing teaser, CTA." category="Business">
      <section className="relative overflow-hidden rounded-2xl border border-border bg-card px-6 py-16 text-center animate-fade-in-up">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,_hsl(var(--primary)/0.12),_transparent_60%)]" />
        <p className="relative text-sm font-semibold uppercase tracking-widest text-primary">LumicorePro</p>
        <h2 className="relative mt-3 font-display text-4xl sm:text-5xl font-bold tracking-tight">Ship products people love</h2>
        <p className="relative mx-auto mt-4 max-w-xl text-muted-foreground">A calm, powerful React core for dashboards, commerce, and AI.</p>
        <div className="relative mt-8 flex justify-center gap-3">
          <Button size="lg" rightIcon={ArrowRight}>Get started</Button>
          <Button size="lg" variant="outline">View demo</Button>
        </div>
      </section>
      <div className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-6">
        {features.map((f, i) => {
          const Icon = icons[i % icons.length];
          return (
            <Card key={f.title} className="hover-lift" animate="fade-up" animationDelay={i * 80}>
              <div className="mb-3 inline-flex rounded-lg bg-primary/10 p-2 text-primary"><Icon className="h-5 w-5" /></div>
              <h3 className="font-display font-semibold">{f.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{f.text}</p>
            </Card>
          );
        })}
      </div>
    </TemplateShell>
  );
}
`,

  ServicesPage: `import TemplateShell from '../../_shared/TemplateShell';
import { Card, Button } from '@/components/ui';
import { services } from './data/mockData';

export default function ServicesPage() {
  return (
    <TemplateShell title="Services" description="Service cards with clear next steps." category="Business">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {services.map((s, i) => (
          <Card key={s.title} className="flex flex-col hover-lift" animate="fade-up" animationDelay={i * 60}>
            <h3 className="font-display text-lg font-semibold">{s.title}</h3>
            <p className="mt-2 flex-1 text-sm text-muted-foreground">{s.text}</p>
            <p className="mt-4 text-sm font-medium text-primary">{s.price}</p>
            <Button className="mt-4" variant="outline">Learn more</Button>
          </Card>
        ))}
      </div>
    </TemplateShell>
  );
}
`,

  PortfolioPage: `import { useState } from 'react';
import TemplateShell from '../../_shared/TemplateShell';
import { Button } from '@/components/ui';
import { projects, filters } from './data/mockData';

export default function PortfolioPage() {
  const [filter, setFilter] = useState('all');
  const list = projects.filter((p) => filter === 'all' || p.tag === filter);
  return (
    <TemplateShell title="Portfolio" description="Filterable project grid." category="Business">
      <div className="flex flex-wrap gap-2 mb-6">
        {filters.map((f) => (
          <Button key={f} size="sm" variant={filter === f ? 'primary' : 'outline'} onClick={() => setFilter(f)}>
            {f}
          </Button>
        ))}
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {list.map((p, i) => (
          <article key={p.id} className="group overflow-hidden rounded-xl border border-border bg-card hover-lift animate-fade-in-up" style={{ animationDelay: \`\${i * 50}ms\` }}>
            <div className="aspect-[4/3] bg-gradient-to-br from-primary/20 to-muted transition-transform duration-500 group-hover:scale-105" />
            <div className="p-4">
              <p className="text-xs uppercase tracking-wide text-primary">{p.tag}</p>
              <h3 className="mt-1 font-display font-semibold">{p.title}</h3>
            </div>
          </article>
        ))}
      </div>
    </TemplateShell>
  );
}
`,

  PricingPage: `import { useState } from 'react';
import TemplateShell from '../../_shared/TemplateShell';
import { PricingGrid, FAQItem } from '@/components/business';
import { Button } from '@/components/ui';
import { plans, faqs } from './data/mockData';

export default function PricingPage() {
  const [yearly, setYearly] = useState(false);
  const mapped = plans.map((p) => ({
    ...p,
    price: yearly ? p.yearly : p.monthly,
    period: yearly ? '/yr' : '/mo',
  }));
  return (
    <TemplateShell
      title="Pricing"
      description="Simple tiers with monthly/yearly toggle."
      category="Business"
      actions={
        <div className="inline-flex rounded-lg border border-border p-1">
          <Button size="sm" variant={!yearly ? 'primary' : 'ghost'} onClick={() => setYearly(false)}>Monthly</Button>
          <Button size="sm" variant={yearly ? 'primary' : 'ghost'} onClick={() => setYearly(true)}>Yearly</Button>
        </div>
      }
    >
      <PricingGrid plans={mapped} />
      <div className="mt-12 max-w-2xl mx-auto">
        {faqs.map((f) => (
          <FAQItem key={f.q} question={f.q} answer={f.a} />
        ))}
      </div>
    </TemplateShell>
  );
}
`,

  ContactPage: `import TemplateShell from '../../_shared/TemplateShell';
import { Card, Button, Input, Textarea, Alert } from '@/components/ui';
import { Mail, MapPin, Phone } from 'lucide-react';
import useForm from '@/hooks/useForm';
import { info } from './data/mockData';

export default function ContactPage() {
  const form = useForm({
    initialValues: { name: '', email: '', subject: '', message: '' },
    validate: (v) => {
      const e = {};
      if (!v.name) e.name = 'Required';
      if (!v.email) e.email = 'Required';
      if (!v.message) e.message = 'Required';
      return e;
    },
    onSubmit: async () => {},
  });

  return (
    <TemplateShell title="Contact" description="Validated inquiry form and contact info." category="Business">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="space-y-4" animate="fade-up">
          <div className="flex gap-3 text-sm"><Mail className="h-4 w-4 text-primary" />{info.email}</div>
          <div className="flex gap-3 text-sm"><Phone className="h-4 w-4 text-primary" />{info.phone}</div>
          <div className="flex gap-3 text-sm"><MapPin className="h-4 w-4 text-primary" />{info.address}</div>
        </Card>
        <Card className="lg:col-span-2 space-y-4" animate="fade-up" animationDelay={80}>
          {form.submitCount > 0 && Object.keys(form.errors).length === 0 && (
            <Alert variant="success" title="Message sent">We will reply within one business day.</Alert>
          )}
          <form onSubmit={form.handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input label="Name" name="name" value={form.values.name} onChange={form.handleChange} onBlur={form.handleBlur} error={form.touched.name && form.errors.name} />
              <Input label="Email" name="email" type="email" value={form.values.email} onChange={form.handleChange} onBlur={form.handleBlur} error={form.touched.email && form.errors.email} />
            </div>
            <Input label="Subject" name="subject" value={form.values.subject} onChange={form.handleChange} />
            <Textarea label="Message" name="message" rows={5} value={form.values.message} onChange={form.handleChange} onBlur={form.handleBlur} error={form.touched.message && form.errors.message} />
            <Button type="submit" loading={form.isSubmitting}>Send message</Button>
          </form>
        </Card>
      </div>
    </TemplateShell>
  );
}
`,
};

const mockData = {
  DashboardOverview: `export const stats = [
  { key: 'users', label: 'Users', value: '12.4k', delta: '+8.2%' },
  { key: 'revenue', label: 'Revenue', value: '$48.2k', delta: '+12.5%' },
  { key: 'orders', label: 'Orders', value: '1,284', delta: '+3.1%' },
  { key: 'growth', label: 'Growth', value: '18%', delta: '-1.2%' },
];
export const activity = [
  { id: 1, text: 'New order #4821 placed', time: '2m ago' },
  { id: 2, text: 'User Maya joined the workspace', time: '14m ago' },
  { id: 3, text: 'Invoice #902 paid', time: '1h ago' },
  { id: 4, text: 'API key rotated', time: '3h ago' },
];
`,
  UsersManagement: `export const users = [
  { id: 1, name: 'Maya Chen', email: 'maya@lumicore.pro', role: 'Admin', status: 'active' },
  { id: 2, name: 'Jordan Lee', email: 'jordan@lumicore.pro', role: 'Editor', status: 'active' },
  { id: 3, name: 'Sam Patel', email: 'sam@lumicore.pro', role: 'Viewer', status: 'invited' },
  { id: 4, name: 'Ava Brooks', email: 'ava@lumicore.pro', role: 'Editor', status: 'active' },
];
`,
  Analytics: `export const metrics = [
  { label: 'Visitors', value: '24.8k', change: '+6.4%' },
  { label: 'Sessions', value: '31.2k', change: '+4.1%' },
  { label: 'Conversion', value: '3.8%', change: '+0.4%' },
  { label: 'Bounce', value: '41%', change: '-2.1%' },
];
export const series = [
  { day: 'Mon', value: 420 }, { day: 'Tue', value: 510 }, { day: 'Wed', value: 480 },
  { day: 'Thu', value: 620 }, { day: 'Fri', value: 700 }, { day: 'Sat', value: 560 }, { day: 'Sun', value: 450 },
];
`,
  Settings: `export const sections = [
  { id: 'general', label: 'General' },
  { id: 'security', label: 'Security' },
  { id: 'notifications', label: 'Notifications' },
  { id: 'danger', label: 'Danger zone' },
];
`,
  Profile: `export const profile = {
  name: 'Alex Rivera', email: 'alex@lumicore.pro', role: 'Founder',
  title: 'Product Lead', location: 'Austin, TX',
};
export const activity = [
  { id: 1, text: 'Updated profile photo', time: 'Yesterday' },
  { id: 2, text: 'Enabled 2FA', time: '3 days ago' },
  { id: 3, text: 'Changed password', time: '2 weeks ago' },
];
`,
  ProductListing: `export const categories = [
  { id: 'all', label: 'All' }, { id: 'ui', label: 'UI Kits' },
  { id: 'dash', label: 'Dashboards' }, { id: 'ai', label: 'AI' },
];
export const products = [
  { id: 1, name: 'Nova UI Kit', price: 79, rating: 4.8, category: 'ui' },
  { id: 2, name: 'Pulse Dashboard', price: 129, rating: 4.9, category: 'dash' },
  { id: 3, name: 'Chat Starter', price: 49, rating: 4.6, category: 'ai' },
  { id: 4, name: 'Commerce Pack', price: 99, rating: 4.7, category: 'ui' },
  { id: 5, name: 'Insight Charts', price: 59, rating: 4.5, category: 'dash' },
  { id: 6, name: 'Prompt Lab', price: 39, rating: 4.4, category: 'ai' },
];
`,
  ProductDetails: `export const product = {
  name: 'Pulse Dashboard Kit', category: 'Dashboard', price: 129, rating: 4.9, reviews: 128,
  description: 'A calm, professional dashboard kit with charts, tables, and settings patterns.',
  sizes: ['S', 'M', 'L', 'XL'],
};
`,
  ShoppingCart: `export const items = [
  { id: 1, name: 'Nova UI Kit', price: 79, qty: 1 },
  { id: 2, name: 'Chat Starter', price: 49, qty: 2 },
];
`,
  Checkout: `export const steps = ['Shipping', 'Payment', 'Review', 'Done'];
`,
  OrdersHistory: `export const filters = [
  { id: 'all', label: 'All' }, { id: 'pending', label: 'Pending' },
  { id: 'shipped', label: 'Shipped' }, { id: 'delivered', label: 'Delivered' },
];
export const orders = [
  { id: 'ORD-1042', date: 'Mar 12, 2026', items: 2, total: 128, status: 'delivered' },
  { id: 'ORD-1048', date: 'Mar 18, 2026', items: 1, total: 79, status: 'shipped' },
  { id: 'ORD-1051', date: 'Mar 20, 2026', items: 3, total: 214, status: 'pending' },
];
`,
  ChatInterface: `export const messages = [
  { id: 1, role: 'ai', text: 'Hi — I am Lumicore. How can I help today?' },
  { id: 2, role: 'user', text: 'Draft a short product update.' },
  { id: 3, role: 'ai', text: 'Sure. Share the feature list and audience, and I will draft it.' },
];
`,
  AIGenerator: `export const models = ['Lumi Fast', 'Lumi Pro', 'Lumi Reason'];
`,
  UsageDashboard: `export const metrics = [
  { label: 'Requests', value: '18.4k', hint: 'This month' },
  { label: 'Tokens', value: '2.1M', hint: '72% of plan' },
  { label: 'Cost', value: '$84', hint: 'Estimated' },
];
export const usage = { used: 2100000, limit: 3000000, percent: 70 };
`,
  ModelSelection: `export const models = [
  { id: 'fast', name: 'Lumi Fast', price: 0.4, blurb: 'Snappy replies for UI copy and chat.', features: ['Low latency', 'Great for chat'], popular: false },
  { id: 'pro', name: 'Lumi Pro', price: 1.2, blurb: 'Balanced quality for product work.', features: ['Strong reasoning', 'Tool use'], popular: true },
  { id: 'reason', name: 'Lumi Reason', price: 2.5, blurb: 'Deep analysis and long context.', features: ['Long context', 'Best quality'], popular: false },
];
`,
  GenerationHistory: `export const history = [
  { id: 1, prompt: 'Landing page headline options', model: 'Lumi Pro', date: 'Mar 18', status: 'saved' },
  { id: 2, prompt: 'Onboarding email sequence', model: 'Lumi Fast', date: 'Mar 17', status: 'done' },
  { id: 3, prompt: 'Pricing FAQ draft', model: 'Lumi Reason', date: 'Mar 15', status: 'saved' },
];
`,
  LandingPage: `export const features = [
  { title: 'Fast by default', text: 'Vite-powered workflows with lean components.' },
  { title: 'Secure patterns', text: 'Auth-friendly defaults and clear states.' },
  { title: 'Ready layouts', text: 'Dashboard, commerce, AI, and business pages.' },
];
`,
  ServicesPage: `export const services = [
  { title: 'Product design', text: 'UI systems and conversion-focused flows.', price: 'From $2.5k' },
  { title: 'Frontend build', text: 'React apps with clean architecture.', price: 'From $4k' },
  { title: 'AI features', text: 'Chat, generation, and usage dashboards.', price: 'From $3k' },
  { title: 'Design systems', text: 'Tokens, components, and docs.', price: 'From $3.5k' },
  { title: 'E-commerce', text: 'Catalog to checkout, done right.', price: 'From $5k' },
  { title: 'Retainers', text: 'Ongoing product partnership.', price: 'Custom' },
];
`,
  PortfolioPage: `export const filters = ['all', 'saas', 'commerce', 'brand'];
export const projects = [
  { id: 1, title: 'Northwind Analytics', tag: 'saas' },
  { id: 2, title: 'Coral Storefront', tag: 'commerce' },
  { id: 3, title: 'Lumen Identity', tag: 'brand' },
  { id: 4, title: 'Orbit Ops', tag: 'saas' },
  { id: 5, title: 'Field Market', tag: 'commerce' },
  { id: 6, title: 'Signal Studio', tag: 'brand' },
];
`,
  PricingPage: `export const plans = [
  { name: 'Starter', monthly: '$19', yearly: '$190', description: 'For solo builders', features: ['Core UI', 'Templates', 'Email support'], highlighted: false },
  { name: 'Pro', monthly: '$49', yearly: '$490', description: 'For product teams', features: ['Everything in Starter', 'AI templates', 'Priority support'], highlighted: true },
  { name: 'Business', monthly: '$99', yearly: '$990', description: 'For growing orgs', features: ['Everything in Pro', 'SSO ready', 'Custom branding'], highlighted: false },
];
export const faqs = [
  { q: 'Can I change plans later?', a: 'Yes. Upgrade or downgrade anytime.' },
  { q: 'Is there a free trial?', a: 'Pro includes a 14-day trial.' },
];
`,
  ContactPage: `export const info = {
  email: 'hello@lumicore.pro',
  phone: '+1 (512) 555-0142',
  address: 'Austin, TX',
};
`,
};

// Check Switch and Textarea exist
for (const t of catalog) {
  const dir = path.join(root, t.path);
  write(path.join(dir, `${t.id}.jsx`), bodies[t.id]);
  write(path.join(dir, 'data', 'mockData.js'), mockData[t.id]);
  write(
    path.join(dir, 'index.js'),
    `export { default } from './${t.id}';\nexport { default as ${t.id} } from './${t.id}';\n`
  );
}

write(
  path.join(root, 'catalog.js'),
  `export const TEMPLATE_CATALOG = ${JSON.stringify(
    catalog.map(({ id, path: p, title, description, category }) => ({
      id,
      path: p,
      route: '/templates/' + p,
      title,
      description,
      category,
    })),
    null,
    2
  )};\n`
);

write(
  path.join(root, 'index.js'),
  `export { TEMPLATE_CATALOG } from './catalog';
export { default as TemplateShell } from './_shared/TemplateShell';

export { default as DashboardOverview } from './dashboard/DashboardOverview';
export { default as UsersManagement } from './dashboard/UsersManagement';
export { default as Analytics } from './dashboard/Analytics';
export { default as Settings } from './dashboard/Settings';
export { default as Profile } from './dashboard/Profile';

export { default as ProductListing } from './ecommerce/ProductListing';
export { default as ProductDetails } from './ecommerce/ProductDetails';
export { default as ShoppingCart } from './ecommerce/ShoppingCart';
export { default as Checkout } from './ecommerce/Checkout';
export { default as OrdersHistory } from './ecommerce/OrdersHistory';

export { default as ChatInterface } from './ai/ChatInterface';
export { default as AIGenerator } from './ai/AIGenerator';
export { default as UsageDashboard } from './ai/UsageDashboard';
export { default as ModelSelection } from './ai/ModelSelection';
export { default as GenerationHistory } from './ai/GenerationHistory';

export { default as LandingPage } from './business/LandingPage';
export { default as ServicesPage } from './business/ServicesPage';
export { default as PortfolioPage } from './business/PortfolioPage';
export { default as PricingPage } from './business/PricingPage';
export { default as ContactPage } from './business/ContactPage';
`
);

console.log('Generated', catalog.length, 'templates');
