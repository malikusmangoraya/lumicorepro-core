from __future__ import annotations

from pathlib import Path

ROOTS = [Path("generated-projects"), Path("products")]
FEATURE_NAMES = ["auth", "dashboard", "profile", "payments"]


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def normalize_project(project_dir: Path) -> None:
    frontend_src = project_dir / "frontend" / "src"
    if not frontend_src.exists():
        return

    features_dir = frontend_src / "features"
    features_dir.mkdir(parents=True, exist_ok=True)
    write(
        features_dir / "index.js",
        """export { default as authFeature } from './auth';\nexport { default as dashboardFeature } from './dashboard';\nexport { default as profileFeature } from './profile';\nexport { default as paymentsFeature } from './payments';\n""",
    )

    for name in FEATURE_NAMES:
        feature_dir = features_dir / name
        feature_dir.mkdir(parents=True, exist_ok=True)
        route_map = {
            "auth": "/login",
            "dashboard": "/dashboard",
            "profile": "/profile",
            "payments": "/billing",
        }
        write(
            feature_dir / "index.js",
            f"""export const {name}Feature = {{\n  name: '{name}',\n  defaultRoute: '{route_map[name]}',\n}};\n\nexport default {name}Feature;\n""",
        )

    lib_dir = frontend_src / "lib"
    lib_dir.mkdir(parents=True, exist_ok=True)
    write(
        lib_dir / "paymentProvider.js",
        """export class MockPaymentProvider {\n  async createCheckoutSession({ amount, currency, customerId }) {\n    return {\n      id: 'mock-checkout-session',\n      amount,\n      currency: currency || 'USD',\n      customerId: customerId || 'demo-customer',\n      status: 'pending',\n      provider: 'mock',\n    };\n  }\n\n  async verifyWebhook(event) {\n    return {\n      ok: true,\n      provider: 'mock',\n      eventType: event?.type || 'payment.succeeded',\n      id: event?.id || 'demo-event',\n    };\n  }\n}\n\nexport const paymentProvider = new MockPaymentProvider();\nexport default paymentProvider;\n""",
    )

    # Ensure a root-level app shell wrapper won't fail even if a project doesn't wire all routes yet.
    app_file = project_dir / "frontend" / "src" / "App.jsx"
    if app_file.exists():
        existing = app_file.read_text(encoding="utf-8")
        if "from './features'" not in existing and "feature registry" not in existing:
            if "import './lib/theme';" in existing:
                replacement = existing.replace(
                    "import './lib/theme';",
                    "import './lib/theme';\nimport { authFeature, dashboardFeature, profileFeature, paymentsFeature } from './features';\n",
                )
                if "feature registry" not in replacement:
                    replacement = replacement.replace(
                        "export default function App() {",
                        "const featureRegistry = [authFeature, dashboardFeature, profileFeature, paymentsFeature];\n\nexport default function App() {",
                    )
                app_file.write_text(replacement, encoding="utf-8")


def main() -> None:
    for root in ROOTS:
        if not root.exists():
            continue
        for child in sorted(root.iterdir()):
            if child.is_dir() and not child.name.startswith('.'):
                normalize_project(child)


if __name__ == "__main__":
    main()
