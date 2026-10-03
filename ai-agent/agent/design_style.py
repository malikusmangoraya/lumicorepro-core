"""
Design Style Engine — LumicorePro AI Agent
===========================================
Named, art-directed design style system for generated websites.

Every LumicorePro site until now used one generic glassmorphism theme. This
engine gives each generated project an intentional, named visual identity:

  1. Resolves a design style — user-chosen (spec["design_style"]) or auto-
     suggested from the detected industry / website type.
  2. Writes a central `design-tokens.json` (palette, typography, radius,
     shadow, border, effects) that the whole project can consume.
  3. Injects style-matched CSS custom properties + utilities into the
     frontend `index.css` (non-destructive append) so tokens theme the site.
  4. Generates 100% original, deterministic SVG art — hero banners, icon set,
     backgrounds, illustrations, and UI mockups — for the style's palette/DNA.
     No stock, no scraped, no copyrighted images (off-line requirement: local
     SVG generation is the built-in fallback; a local model / provider hook can
     slot in behind the same interface later).
  5. Writes `assets/manifest.json` with style, generation prompt, and license
     (self-generated / public-domain) for compliance & audit.

Styles are pluggable: `DesignStyleEngine.register_style(style_dict)` adds a new
style pack without touching the core.
"""

import os
import re
import json
import time
import hashlib
import random
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from utils.logger import agent_logger
from utils.file_manager import FileManager


# ── Colour helpers ───────────────────────────────────────────────────────────
def _hex_to_rgb(value: str) -> Tuple[int, int, int]:
    value = value.strip().lstrip('#')
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore


def _fg_for(value: str) -> str:
    """Pick a WCAG-ish readable foreground for a hex background."""
    r, g, b = _hex_to_rgb(value)
    lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
    return '#0f172a' if lum > 0.5 else '#f8fafc'


def _hex_to_hsl(value: str) -> str:
    """Hex → 'h s% l%' string ready for `hsl(var(--token) / <alpha-value>)`."""
    r, g, b = (c / 255.0 for c in _hex_to_rgb(value))
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2.0
    d = mx - mn
    if d == 0:
        h = s = 0.0
    else:
        s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
        if mx == r:
            h = (g - b) / d + (6 if g < b else 0)
        elif mx == g:
            h = (b - r) / d + 2
        else:
            h = (r - g) / d + 4
        h /= 6.0
    return f'{round(h * 360)} {round(s * 100, 1)}% {round(l * 100, 1)}%'


def _hex_rgb(value: str) -> str:
    r, g, b = _hex_to_rgb(value)
    return f'{r} {g} {b}'


# ── Design style catalog (plug-in list) ─────────────────────────────────────
_STYLE_CATALOG: Dict[str, Dict[str, Any]] = {
    'minimalism': {
        'id': 'minimalism', 'name': 'Minimalism',
        'dna': 'White space, simple typography, 1-2 accent colors, content-first.',
        'best_for': ['product', 'portfolio', 'personal', 'consulting', 'professional', 'resume'],
        'color': {
            'primary': '#111827', 'secondary': '#0ea5e9', 'accent': '#0284c7',
            'bg': '#ffffff', 'card': '#f8fafc', 'surface': '#f1f5f9',
            'text': '#0f172a', 'muted': '#64748b', 'border': '#e2e8f0',
        },
        'fonts': {'display': 'Inter', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '16px', 'button': '9999px'},
        'shadow': {'card': '0 1px 3px rgba(15,23,42,0.08)', 'button': '0 1px 2px rgba(15,23,42,0.1)'},
        'border': {'card': '1px solid #e2e8f0', 'button': '1px solid #e2e8f0'},
        'effects': {'blur': '0px', 'glow': 'none'},
        'composition': 'blocks', 'weight': 'thin',
    },
    'glassmorphism': {
        'id': 'glassmorphism', 'name': 'Glassmorphism',
        'dna': 'Frosted glass, backdrop blur, translucent overlapping cards.',
        'best_for': ['saas', 'dashboard', 'crypto', 'fintech', 'web3', 'os', 'platform'],
        'color': {
            'primary': '#22d3ee', 'secondary': '#818cf8', 'accent': '#a78bfa',
            'bg': '#0b1220', 'card': 'rgba(255,255,255,0.06)', 'surface': 'rgba(255,255,255,0.04)',
            'text': '#f8fafc', 'muted': '#94a3b8', 'border': 'rgba(255,255,255,0.12)',
        },
        'fonts': {'display': 'Outfit', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '20px', 'button': '12px'},
        'shadow': {'card': '0 8px 32px rgba(0,0,0,0.35)', 'button': '0 4px 16px rgba(0,0,0,0.25)'},
        'border': {'card': '1px solid rgba(255,255,255,0.14)', 'button': '1px solid rgba(255,255,255,0.2)'},
        'effects': {'blur': '24px', 'glow': '0 0 24px rgba(34,211,238,0.25)'},
        'composition': 'glass', 'weight': 'medium',
    },
    'neo_brutalism': {
        'id': 'neo_brutalism', 'name': 'Neo-Brutalism',
        'dna': 'Neon colors, thick black borders, hard offset shadows, raw bold type.',
        'best_for': ['ecommerce', 'creator', 'fashion', 'freelance', 'media', 'streetwear'],
        'color': {
            'primary': '#3b82f6', 'secondary': '#facc15', 'accent': '#ef4444',
            'bg': '#fef3c7', 'card': '#ffffff', 'surface': '#bfdbfe',
            'text': '#0f172a', 'muted': '#475569', 'border': '#0f172a',
        },
        'fonts': {'display': 'Space Grotesk', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '0px', 'button': '0px'},
        'shadow': {'card': '6px 6px 0 #0f172a', 'button': '4px 4px 0 #0f172a'},
        'border': {'card': '3px solid #0f172a', 'button': '3px solid #0f172a'},
        'effects': {'blur': '0px', 'glow': 'none'},
        'composition': 'neo', 'weight': 'bold',
    },
    'bento_grid': {
        'id': 'bento_grid', 'name': 'Bento Grid UI',
        'dna': 'Rounded grid cards, bento-box layout, feature-per-card.',
        'best_for': ['tech', 'saas', 'product', 'startup', 'mobile', 'ai'],
        'color': {
            'primary': '#6366f1', 'secondary': '#ec4899', 'accent': '#22d3ee',
            'bg': '#f8fafc', 'card': '#ffffff', 'surface': '#eef2ff',
            'text': '#0f172a', 'muted': '#64748b', 'border': '#e2e8f0',
        },
        'fonts': {'display': 'Outfit', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '24px', 'button': '12px'},
        'shadow': {'card': '0 10px 30px rgba(15,23,42,0.08)', 'button': '0 4px 12px rgba(99,102,241,0.2)'},
        'border': {'card': '1px solid #e2e8f0', 'button': '0'},
        'effects': {'blur': '0px', 'glow': '0 0 20px rgba(99,102,241,0.15)'},
        'composition': 'bento', 'weight': 'medium',
    },
    'neumorphism': {
        'id': 'neumorphism', 'name': 'Neumorphism (Soft UI)',
        'dna': 'Soft inset/outset shadows, monochrome base, tactile depth.',
        'best_for': ['smart home', 'iot', 'music', 'audio', 'control', 'utility'],
        'color': {
            'primary': '#e0e5ec', 'secondary': '#8b93a7', 'accent': '#a3b2e0',
            'bg': '#e0e5ec', 'card': '#e0e5ec', 'surface': '#d6dbe2',
            'text': '#3b4156', 'muted': '#8b93a7', 'border': '#e0e5ec',
        },
        'fonts': {'display': 'Inter', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '24px', 'button': '9999px'},
        'shadow': {'card': '12px 12px 28px #b8bec7, -12px -12px 28px #ffffff', 'button': '6px 6px 14px #b8bec7, -6px -6px 14px #ffffff'},
        'border': {'card': '1px solid rgba(255,255,255,0.5)', 'button': '1px solid rgba(255,255,255,0.5)'},
        'effects': {'blur': '0px', 'glow': 'none'},
        'composition': 'neumorph', 'weight': 'medium',
    },
    'flat_design': {
        'id': 'flat_design', 'name': 'Flat Design',
        'dna': 'Solid colors, 2D icons, minimal shadow/gradient, fast loading.',
        'best_for': ['web service', 'productivity', 'tool', 'utility', 'government'],
        'color': {
            'primary': '#2563eb', 'secondary': '#16a34a', 'accent': '#f59e0b',
            'bg': '#f9fafb', 'card': '#ffffff', 'surface': '#eff6ff',
            'text': '#111827', 'muted': '#6b7280', 'border': '#e5e7eb',
        },
        'fonts': {'display': 'Inter', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '12px', 'button': '8px'},
        'shadow': {'card': '0 1px 2px rgba(0,0,0,0.04)', 'button': '0 0 0 0'},
        'border': {'card': '1px solid #e5e7eb', 'button': '0'},
        'effects': {'blur': '0px', 'glow': 'none'},
        'composition': 'flat', 'weight': 'medium',
    },
    'claymorphism': {
        'id': 'claymorphism', 'name': 'Claymorphism (3D Clay UI)',
        'dna': 'Inflated soft 3D shapes, bubble buttons, playful inner shadows.',
        'best_for': ['edtech', 'kids', 'learning', 'playful', 'nft', 'games'],
        'color': {
            'primary': '#f472b6', 'secondary': '#38bdf8', 'accent': '#fbbf24',
            'bg': '#fdf2f8', 'card': '#ffffff', 'surface': '#ffe4e6',
            'text': '#3f1d38', 'muted': '#9f6d8a', 'border': 'rgba(63,29,56,0.08)',
        },
        'fonts': {'display': 'Baloo 2', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '28px', 'button': '9999px'},
        'shadow': {'card': '0 18px 40px rgba(244,114,182,0.28), inset 0 -6px 12px rgba(191,64,126,0.25)', 'button': '0 10px 24px rgba(244,114,182,0.3), inset 0 -4px 8px rgba(191,64,126,0.3)'},
        'border': {'card': '1px solid rgba(255,255,255,0.7)', 'button': '0'},
        'effects': {'blur': '0px', 'glow': '0 0 24px rgba(244,114,182,0.2)'},
        'composition': 'clay', 'weight': 'bold',
    },
    'skeuomorphism': {
        'id': 'skeuomorphism', 'name': 'Skeuomorphism',
        'dna': 'Real-world texture mimicry (metal, leather, paper), realistic controls.',
        'best_for': ['audio', 'daw', 'vintage', 'instruments', 'utility'],
        'color': {
            'primary': '#b87333', 'secondary': '#8b5a2b', 'accent': '#c2926a',
            'bg': '#3d3527', 'card': '#54493a', 'surface': '#40382b',
            'text': '#f1e7d8', 'muted': '#b8a98f', 'border': '#6a5e4c',
        },
        'fonts': {'display': 'Georgia', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '10px', 'button': '9999px'},
        'shadow': {'card': 'inset 0 2px 6px rgba(0,0,0,0.55), 0 2px 2px rgba(255,255,255,0.12)', 'button': 'inset 0 -4px 8px rgba(0,0,0,0.5), 0 1px 1px rgba(255,255,255,0.2)'},
        'border': {'card': '1px solid #6a5e4c', 'button': '1px solid #6a5e4c'},
        'effects': {'blur': '0px', 'glow': 'none'},
        'composition': 'metal', 'weight': 'medium',
    },
    'cyberpunk': {
        'id': 'cyberpunk', 'name': 'Dark Cyberpunk / Neon',
        'dna': 'Deep dark backgrounds, neon accent glows, tech/mono type.',
        'best_for': ['gaming', 'web3', 'cybersecurity', 'developer', 'esports'],
        'color': {
            'primary': '#22d3ee', 'secondary': '#f472b6', 'accent': '#a3e635',
            'bg': '#0a0a0f', 'card': '#111118', 'surface': '#1a1a24',
            'text': '#f4f4f5', 'muted': '#71717a', 'border': 'rgba(34,211,238,0.25)',
        },
        'fonts': {'display': 'Space Grotesk', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '14px', 'button': '8px'},
        'shadow': {'card': '0 0 0 1px rgba(34,211,238,0.2), 0 0 24px rgba(34,211,238,0.12)', 'button': '0 0 16px rgba(34,211,238,0.35)'},
        'border': {'card': '1px solid rgba(34,211,238,0.35)', 'button': '1px solid #22d3ee'},
        'effects': {'blur': '0px', 'glow': '0 0 18px rgba(34,211,238,0.5)'},
        'composition': 'neon', 'weight': 'bold',
    },
    'animaster': {
        'id': 'animaster', 'name': 'Animaster Motion UI',
        'dna': 'Kinetic typography, text morphing, magnetic buttons, glowing border beams, fluid micro-interactions.',
        'best_for': ['creative', 'agency', 'marketing', 'interactive', 'startup', 'saas', 'modern'],
        'color': {
            'primary': '#06b6d4', 'secondary': '#8b5cf6', 'accent': '#ec4899',
            'bg': '#030712', 'card': 'rgba(15,23,42,0.7)', 'surface': 'rgba(30,41,59,0.5)',
            'text': '#f8fafc', 'muted': '#94a3b8', 'border': 'rgba(6,182,212,0.25)',
        },
        'fonts': {'display': 'Outfit', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '20px', 'button': '12px'},
        'shadow': {'card': '0 10px 40px rgba(0,0,0,0.5), 0 0 20px rgba(6,182,212,0.15)', 'button': '0 4px 20px rgba(6,182,212,0.3)'},
        'border': {'card': '1px solid rgba(6,182,212,0.25)', 'button': '1px solid rgba(6,182,212,0.4)'},
        'effects': {'blur': '20px', 'glow': '0 0 30px rgba(6,182,212,0.3)'},
        'composition': 'motion', 'weight': 'bold',
    },
    'skipper': {
        'id': 'skipper', 'name': 'Skipper Minimalist Dark',
        'dna': 'Refined spotlight grids, dark bento boxes, subtle specular reflections, border beams, clean typography.',
        'best_for': ['developer', 'ai', 'cloud', 'fintech', 'productivity', 'api', 'infrastructure'],
        'color': {
            'primary': '#38bdf8', 'secondary': '#64748b', 'accent': '#a855f7',
            'bg': '#020617', 'card': 'rgba(15,23,42,0.85)', 'surface': 'rgba(30,41,59,0.6)',
            'text': '#f8fafc', 'muted': '#94a3b8', 'border': 'rgba(51,65,85,0.7)',
        },
        'fonts': {'display': 'Inter', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '16px', 'button': '10px'},
        'shadow': {'card': '0 4px 24px rgba(0,0,0,0.4)', 'button': '0 2px 8px rgba(56,189,248,0.2)'},
        'border': {'card': '1px solid rgba(51,65,85,0.8)', 'button': '1px solid rgba(56,189,248,0.3)'},
        'effects': {'blur': '16px', 'glow': '0 0 24px rgba(56,189,248,0.15)'},
        'composition': 'spotlight', 'weight': 'medium',
    },
    'vengeance': {
        'id': 'vengeance', 'name': 'Vengeance Cyber-Brutalism',
        'dna': '3D holographic tilt, deep obsidian darkness, sharp neon edge glows, HUD grid lines, cyber aesthetic.',
        'best_for': ['gaming', 'crypto', 'defi', 'security', 'hardware', 'luxury tech', 'autonomous'],
        'color': {
            'primary': '#00f0ff', 'secondary': '#ff0055', 'accent': '#7000ff',
            'bg': '#050508', 'card': 'rgba(10,10,18,0.9)', 'surface': 'rgba(20,20,35,0.7)',
            'text': '#ffffff', 'muted': '#8888aa', 'border': 'rgba(0,240,255,0.3)',
        },
        'fonts': {'display': 'Space Grotesk', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '12px', 'button': '6px'},
        'shadow': {'card': '0 0 30px rgba(0,240,255,0.15), inset 0 0 15px rgba(0,240,255,0.05)', 'button': '0 0 20px rgba(0,240,255,0.4)'},
        'border': {'card': '1px solid rgba(0,240,255,0.35)', 'button': '1px solid #00f0ff'},
        'effects': {'blur': '12px', 'glow': '0 0 40px rgba(0,240,255,0.35)'},
        'composition': 'holographic', 'weight': 'bold',
    },
    'corporate_memphis': {
        'id': 'corporate_memphis', 'name': 'Corporate Memphis',
        'dna': 'Flat character illustrations, rounded shapes, pastel palettes.',
        'best_for': ['onboarding', 'startup', 'wellness', 'people', 'community'],
        'color': {
            'primary': '#f472b6', 'secondary': '#60a5fa', 'accent': '#fbbf24',
            'bg': '#fff7ed', 'card': '#ffffff', 'surface': '#fef3c7',
            'text': '#1f2937', 'muted': '#9ca3af', 'border': '#fde68a',
        },
        'fonts': {'display': 'Outfit', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '18px', 'button': '9999px'},
        'shadow': {'card': '0 4px 12px rgba(251,146,60,0.12)', 'button': '0 2px 6px rgba(0,0,0,0.06)'},
        'border': {'card': '0', 'button': '0'},
        'effects': {'blur': '0px', 'glow': 'none'},
        'composition': 'people', 'weight': 'medium',
    },
    'editorial': {
        'id': 'editorial', 'name': 'Editorial / Magazine',
        'dna': 'Large serif headlines, multi-column text, print whitespace.',
        'best_for': ['blog', 'news', 'media', 'journalism', 'thought leadership'],
        'color': {
            'primary': '#7f1d1d', 'secondary': '#78350f', 'accent': '#0f766e',
            'bg': '#fafaf8', 'card': '#ffffff', 'surface': '#f4f1ea',
            'text': '#1c1917', 'muted': '#78716c', 'border': '#e7e5e4',
        },
        'fonts': {'display': 'Playfair Display', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '4px', 'button': '4px'},
        'shadow': {'card': '0 1px 2px rgba(0,0,0,0.05)', 'button': '0 0 0 0'},
        'border': {'card': '1px solid #e7e5e4', 'button': '1px solid #1c1917'},
        'effects': {'blur': '0px', 'glow': 'none'},
        'composition': 'editorial', 'weight': 'serif',
    },
    'swiss': {
        'id': 'swiss', 'name': 'Swiss / International Typographic',
        'dna': 'Strict grid, sans-serif type, high contrast, asymmetric balance.',
        'best_for': ['design agency', 'architecture', 'portfolio', 'museum'],
        'color': {
            'primary': '#dc2626', 'secondary': '#000000', 'accent': '#2563eb',
            'bg': '#ffffff', 'card': '#ffffff', 'surface': '#f3f4f6',
            'text': '#000000', 'muted': '#4b5563', 'border': '#d1d5db',
        },
        'fonts': {'display': 'Helvetica Neue', 'sans': 'Helvetica Neue', 'mono': 'JetBrains Mono'},
        'radius': {'card': '0px', 'button': '0px'},
        'shadow': {'card': '0 0 0 0', 'button': '0 0 0 0'},
        'border': {'card': '1px solid #d1d5db', 'button': '2px solid #000000'},
        'effects': {'blur': '0px', 'glow': 'none'},
        'composition': 'grid', 'weight': 'bold',
    },
    'aurora': {
        'id': 'aurora', 'name': 'Gradient Mesh / Aurora',
        'dna': 'Soft blurred multi-color gradients, glowing orbs, dreamy.',
        'best_for': ['ai product', 'ai', 'machine learning', 'modern saas', 'creative tech'],
        'color': {
            'primary': '#8b5cf6', 'secondary': '#ec4899', 'accent': '#22d3ee',
            'bg': '#0d0a1f', 'card': '#151134', 'surface': '#1d1742',
            'text': '#f5f3ff', 'muted': '#a5b4fc', 'border': 'rgba(139,92,246,0.25)',
        },
        'fonts': {'display': 'Outfit', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '22px', 'button': '9999px'},
        'shadow': {'card': '0 20px 50px rgba(139,92,246,0.22)', 'button': '0 8px 24px rgba(236,72,153,0.3)'},
        'border': {'card': '1px solid rgba(139,92,246,0.2)', 'button': '0'},
        'effects': {'blur': '40px', 'glow': '0 0 40px rgba(139,92,246,0.45)'},
        'composition': 'aurora', 'weight': 'medium',
    },
    'organic': {
        'id': 'organic', 'name': 'Organic / Blob Shapes',
        'dna': 'Rounded blob backgrounds, soft curves, nature-inspired palette.',
        'best_for': ['wellness', 'health', 'eco', 'sustainability', 'yoga', 'food'],
        'color': {
            'primary': '#10b981', 'secondary': '#84cc16', 'accent': '#0d9488',
            'bg': '#ecfdf5', 'card': '#ffffff', 'surface': '#d1fae5',
            'text': '#14532d', 'muted': '#6b7280', 'border': '#a7f3d0',
        },
        'fonts': {'display': 'Quicksand', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '32px', 'button': '9999px'},
        'shadow': {'card': '0 12px 32px rgba(16,185,129,0.16)', 'button': '0 6px 16px rgba(16,185,129,0.25)'},
        'border': {'card': '0', 'button': '0'},
        'effects': {'blur': '0px', 'glow': '0 0 20px rgba(16,185,129,0.2)'},
        'composition': 'blob', 'weight': 'medium',
    },
    'retro_futurism': {
        'id': 'retro_futurism', 'name': 'Retro-Futurism / Y2K',
        'dna': 'Chrome text, glossy gradients, 90s-2000s nostalgia.',
        'best_for': ['fashion', 'gen z', 'consumer', 'music', 'gaming lifestyle'],
        'color': {
            'primary': '#e11d48', 'secondary': '#8b5cf6', 'accent': '#38bdf8',
            'bg': '#fdf2f8', 'card': '#ffffff', 'surface': '#fce7f3',
            'text': '#3b0764', 'muted': '#a21caf', 'border': '#f0abfc',
        },
        'fonts': {'display': 'Orbitron', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '12px', 'button': '9999px'},
        'shadow': {'card': '0 8px 24px rgba(225,29,72,0.18)', 'button': '0 6px 16px rgba(225,29,72,0.3)'},
        'border': {'card': '1px solid #f0abfc', 'button': '0'},
        'effects': {'blur': '0px', 'glow': '0 0 24px rgba(139,92,246,0.3)'},
        'composition': 'chrome', 'weight': 'bold',
    },
    'maximalism': {
        'id': 'maximalism', 'name': 'Maximalism',
        'dna': 'Bold clashing colors, high density, rich layered textures, expressive energy.',
        'best_for': ['creative', 'fashion', 'festivals', 'arts', 'youth culture'],
        'color': {
            'primary': '#ff0055', 'secondary': '#ffe600', 'accent': '#00f0ff',
            'bg': '#1a0033', 'card': '#2a0845', 'surface': '#3d0c63',
            'text': '#ffffff', 'muted': '#ff77aa', 'border': '#ffe600',
        },
        'fonts': {'display': 'Syne', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '16px', 'button': '9999px'},
        'shadow': {'card': '0 10px 30px rgba(255,0,85,0.35)', 'button': '0 4px 15px rgba(255,230,0,0.4)'},
        'border': {'card': '2px solid #ffe600', 'button': '2px solid #ff0055'},
        'effects': {'blur': '0px', 'glow': '0 0 30px rgba(255,0,85,0.4)'},
        'composition': 'bold', 'weight': 'bold',
    },
    'retro': {
        'id': 'retro', 'name': 'Retro Vintage (70s/80s)',
        'dna': 'Warm mustard/rust hues, chunky serif typography, analog warmth.',
        'best_for': ['vinyl', 'vintage cafe', 'diner', 'apparel', 'photography'],
        'color': {
            'primary': '#d97706', 'secondary': '#b45309', 'accent': '#059669',
            'bg': '#fef3c7', 'card': '#fffbeb', 'surface': '#fde68a',
            'text': '#451a03', 'muted': '#78350f', 'border': '#d97706',
        },
        'fonts': {'display': 'Playfair Display', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '8px', 'button': '4px'},
        'shadow': {'card': '4px 4px 0px #b45309', 'button': '2px 2px 0px #b45309'},
        'border': {'card': '2px solid #d97706', 'button': '2px solid #b45309'},
        'effects': {'blur': '0px', 'glow': 'none'},
        'composition': 'retro', 'weight': 'bold',
    },
    'collage': {
        'id': 'collage', 'name': 'Collage / Scrapbook',
        'dna': 'Torn paper edges, mixed media textures, scrapbook aesthetic, tactile cutouts.',
        'best_for': ['art', 'design studio', 'zines', 'musicians', 'portfolios'],
        'color': {
            'primary': '#4f46e5', 'secondary': '#ec4899', 'accent': '#eab308',
            'bg': '#f5f5f4', 'card': '#ffffff', 'surface': '#e7e5e4',
            'text': '#1c1917', 'muted': '#78716c', 'border': '#d6d3d1',
        },
        'fonts': {'display': 'Fraunces', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '2px', 'button': '4px'},
        'shadow': {'card': '0 10px 25px rgba(0,0,0,0.1)', 'button': '0 2px 5px rgba(0,0,0,0.08)'},
        'border': {'card': '1px dashed #78716c', 'button': '1px solid #1c1917'},
        'effects': {'blur': '0px', 'glow': 'none'},
        'composition': 'collage', 'weight': 'medium',
    },
    'vector': {
        'id': 'vector', 'name': 'Vector & Flat Art',
        'dna': 'Clean crisp SVG geometric shapes, isometric illustrations, vibrant flat gradients.',
        'best_for': ['software', 'saas', 'fintech', 'apps', 'tech blogs'],
        'color': {
            'primary': '#3b82f6', 'secondary': '#10b981', 'accent': '#8b5cf6',
            'bg': '#f8fafc', 'card': '#ffffff', 'surface': '#f1f5f9',
            'text': '#0f172a', 'muted': '#64748b', 'border': '#cbd5e1',
        },
        'fonts': {'display': 'Outfit', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '16px', 'button': '10px'},
        'shadow': {'card': '0 4px 16px rgba(59,130,246,0.08)', 'button': '0 2px 8px rgba(59,130,246,0.2)'},
        'border': {'card': '1px solid #e2e8f0', 'button': '0'},
        'effects': {'blur': '0px', 'glow': 'none'},
        'composition': 'flat', 'weight': 'medium',
    },
    'futuristic': {
        'id': 'futuristic', 'name': 'Futuristic Sci-Fi',
        'dna': 'Sleek carbon tones, cyan data feeds, holographic HUD rings, ultra-modern tech.',
        'best_for': ['aerospace', 'ai', 'robotics', 'autonomous vehicles', 'quantum'],
        'color': {
            'primary': '#00e5ff', 'secondary': '#7c4dff', 'accent': '#00b0ff',
            'bg': '#070913', 'card': '#0d1322', 'surface': '#121b2f',
            'text': '#e0f2fe', 'muted': '#64748b', 'border': 'rgba(0,229,255,0.3)',
        },
        'fonts': {'display': 'Orbitron', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '8px', 'button': '4px'},
        'shadow': {'card': '0 0 25px rgba(0,229,255,0.15)', 'button': '0 0 15px rgba(0,229,255,0.3)'},
        'border': {'card': '1px solid rgba(0,229,255,0.35)', 'button': '1px solid #00e5ff'},
        'effects': {'blur': '12px', 'glow': '0 0 30px rgba(0,229,255,0.35)'},
        'composition': 'holographic', 'weight': 'bold',
    },
    'handwritten': {
        'id': 'handwritten', 'name': 'Handwritten & Organic',
        'dna': 'Organic sketch lines, notebook paper warmth, cursive script accents, human touch.',
        'best_for': ['craft', 'artisanal', 'recipes', 'personal memoirs', 'organic goods'],
        'color': {
            'primary': '#292524', 'secondary': '#b45309', 'accent': '#0284c7',
            'bg': '#fdfbf7', 'card': '#ffffff', 'surface': '#fef9ee',
            'text': '#1c1917', 'muted': '#78716c', 'border': '#e7e5e4',
        },
        'fonts': {'display': 'Caveat', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '12px', 'button': '8px'},
        'shadow': {'card': '0 2px 8px rgba(0,0,0,0.06)', 'button': '0 1px 3px rgba(0,0,0,0.1)'},
        'border': {'card': '1px solid #e7e5e4', 'button': '1px solid #292524'},
        'effects': {'blur': '0px', 'glow': 'none'},
        'composition': 'organic', 'weight': 'medium',
    },
    'bohemian': {
        'id': 'bohemian', 'name': 'Bohemian & Earthy',
        'dna': 'Earthy terracotta, olive greens, botanical motifs, relaxed warm sanctuary.',
        'best_for': ['boutique', 'interior design', 'yoga', 'sustainable living', 'wellness'],
        'color': {
            'primary': '#c2410c', 'secondary': '#65a30d', 'accent': '#d97706',
            'bg': '#faf5ef', 'card': '#ffffff', 'surface': '#f4ede4',
            'text': '#431407', 'muted': '#78716c', 'border': '#e2d9cd',
        },
        'fonts': {'display': 'Cinzel', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '20px', 'button': '9999px'},
        'shadow': {'card': '0 8px 24px rgba(194,65,12,0.08)', 'button': '0 2px 8px rgba(194,65,12,0.15)'},
        'border': {'card': '1px solid #e2d9cd', 'button': '0'},
        'effects': {'blur': '0px', 'glow': 'none'},
        'composition': 'blob', 'weight': 'medium',
    },
    'graffiti': {
        'id': 'graffiti', 'name': 'Graffiti & Urban Street',
        'dna': 'Street art spray paint splatters, bold stencil lettering, high-energy counterculture.',
        'best_for': ['skate', 'hiphop', 'urban apparel', 'extreme sports', 'music festivals'],
        'color': {
            'primary': '#f43f5e', 'secondary': '#eab308', 'accent': '#06b6d4',
            'bg': '#111827', 'card': '#1f2937', 'surface': '#374151',
            'text': '#f9fafb', 'muted': '#9ca3af', 'border': '#f43f5e',
        },
        'fonts': {'display': 'Space Grotesk', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '4px', 'button': '0px'},
        'shadow': {'card': '5px 5px 0px #f43f5e', 'button': '3px 3px 0px #eab308'},
        'border': {'card': '2px solid #f43f5e', 'button': '2px solid #eab308'},
        'effects': {'blur': '0px', 'glow': '0 0 15px rgba(244,63,94,0.3)'},
        'composition': 'neo', 'weight': 'bold',
    },
    'victorian': {
        'id': 'victorian', 'name': 'Victorian & Vintage Luxury',
        'dna': 'Intricate filigree, deep emerald & royal burgundy, gold leaf accents, heritage elegance.',
        'best_for': ['luxury hotel', 'antique', 'fine jewelry', 'heritage whiskey', 'premium tailoring'],
        'color': {
            'primary': '#d4af37', 'secondary': '#800020', 'accent': '#1a4d2e',
            'bg': '#0c0a08', 'card': '#17130e', 'surface': '#231c15',
            'text': '#f7f1e5', 'muted': '#a89f91', 'border': 'rgba(212,175,55,0.35)',
        },
        'fonts': {'display': 'Playfair Display', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '6px', 'button': '4px'},
        'shadow': {'card': '0 10px 30px rgba(0,0,0,0.6), 0 0 15px rgba(212,175,55,0.15)', 'button': '0 2px 10px rgba(212,175,55,0.2)'},
        'border': {'card': '1px solid rgba(212,175,55,0.4)', 'button': '1px solid #d4af37'},
        'effects': {'blur': '0px', 'glow': '0 0 20px rgba(212,175,55,0.25)'},
        'composition': 'editorial', 'weight': 'serif',
    },
    'pixel_art': {
        'id': 'pixel_art', 'name': 'Pixel Art (8-Bit / 16-Bit)',
        'dna': 'Retro arcade raster grids, chiptune energy, crisp pixel borders.',
        'best_for': ['indie games', 'retro gaming', 'web3', 'developer fun', 'collectibles'],
        'color': {
            'primary': '#38bdf8', 'secondary': '#4ade80', 'accent': '#f43f5e',
            'bg': '#0f172a', 'card': '#1e293b', 'surface': '#334155',
            'text': '#f8fafc', 'muted': '#94a3b8', 'border': '#38bdf8',
        },
        'fonts': {'display': 'Space Grotesk', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '0px', 'button': '0px'},
        'shadow': {'card': '4px 4px 0px #000000', 'button': '2px 2px 0px #000000'},
        'border': {'card': '3px solid #38bdf8', 'button': '3px solid #4ade80'},
        'effects': {'blur': '0px', 'glow': 'none'},
        'composition': 'neo', 'weight': 'bold',
    },
    'pop_art': {
        'id': 'pop_art', 'name': 'Pop Art (Comic / Halftone)',
        'dna': 'Ben-Day halftone dots, bold speech lines, primary color punch, comic energy.',
        'best_for': ['pop culture', 'comic', 'creative marketing', 'beverage', 'modern art'],
        'color': {
            'primary': '#ef4444', 'secondary': '#eab308', 'accent': '#3b82f6',
            'bg': '#ffffff', 'card': '#fffbeb', 'surface': '#fee2e2',
            'text': '#000000', 'muted': '#475569', 'border': '#000000',
        },
        'fonts': {'display': 'Space Grotesk', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '0px', 'button': '0px'},
        'shadow': {'card': '6px 6px 0px #000000', 'button': '3px 3px 0px #000000'},
        'border': {'card': '3px solid #000000', 'button': '3px solid #000000'},
        'effects': {'blur': '0px', 'glow': 'none'},
        'composition': 'neo', 'weight': 'bold',
    },
    'surreal': {
        'id': 'surreal', 'name': 'Surrealism & Dreamscape',
        'dna': 'Dreamscapes, unexpected juxtaposition, deep violet nebulae, floating geometric forms.',
        'best_for': ['immersive 3d', 'creative labs', 'digital art', 'metaverse', 'perfumes'],
        'color': {
            'primary': '#c084fc', 'secondary': '#38bdf8', 'accent': '#f472b6',
            'bg': '#090514', 'card': '#140b2b', 'surface': '#1e113f',
            'text': '#fdf4ff', 'muted': '#a855f7', 'border': 'rgba(192,132,252,0.3)',
        },
        'fonts': {'display': 'Outfit', 'sans': 'Inter', 'mono': 'JetBrains Mono'},
        'radius': {'card': '24px', 'button': '9999px'},
        'shadow': {'card': '0 20px 50px rgba(192,132,252,0.2)', 'button': '0 4px 20px rgba(244,114,182,0.3)'},
        'border': {'card': '1px solid rgba(192,132,252,0.3)', 'button': '0'},
        'effects': {'blur': '30px', 'glow': '0 0 35px rgba(192,132,252,0.35)'},
        'composition': 'aurora', 'weight': 'medium',
    },
}

STYLE_ALIASES = {
    'y2k': 'retro_futurism',
    'clay': 'claymorphism',
    'clay_style': 'claymorphism',
    'swiss_design': 'swiss',
    'vintage': 'retro',
    'urban': 'graffiti',
    'street': 'graffiti',
    'streetwear': 'graffiti',
    'scrapbook': 'collage',
    '8bit': 'pixel_art',
    '16bit': 'pixel_art',
    'arcade': 'pixel_art',
    'comic': 'pop_art',
    'warhol': 'pop_art',
    'dreamscape': 'surreal',
    'scifi': 'futuristic',
    'sci-fi': 'futuristic',
    'luxury': 'victorian',
    'craft': 'handwritten',
    'sketch': 'handwritten',
    'earthy': 'bohemian',
    'botanical': 'bohemian',
}

# Industry / website type → auto-suggested style (Lovable-style defaults)
_INDUSTRY_STYLE_MAP: List[Tuple[str, str]] = [
    ('edtech', 'claymorphism'), ('education', 'claymorphism'), ('elearning', 'claymorphism'),
    ('crypto', 'glassmorphism'), ('web3', 'glassmorphism'), ('fintech', 'glassmorphism'),
    ('saas', 'glassmorphism'), ('dashboard', 'glassmorphism'), ('platform', 'glassmorphism'),
    ('creator', 'neo_brutalism'), ('ecommerce', 'neo_brutalism'), ('fashion', 'retro_futurism'),
    ('streetwear', 'graffiti'), ('skate', 'graffiti'), ('media', 'neo_brutalism'), ('gaming', 'cyberpunk'),
    ('esports', 'cyberpunk'), ('cybersecurity', 'cyberpunk'), ('security', 'cyberpunk'),
    ('developer', 'cyberpunk'),
    ('ai', 'aurora'), ('machine learning', 'aurora'), ('ml', 'aurora'), ('artificial intelligence', 'aurora'),
    ('wellness', 'organic'), ('eco', 'organic'), ('sustainability', 'organic'), ('yoga', 'bohemian'),
    ('health', 'organic'), ('fitness', 'organic'),
    ('design agency', 'swiss'), ('architecture', 'swiss'), ('agency', 'swiss'),
    ('blog', 'editorial'), ('news', 'editorial'), ('media', 'editorial'), ('journalism', 'editorial'),
    ('portfolio', 'minimalism'), ('personal', 'minimalism'), ('resume', 'minimalism'), ('product', 'minimalism'),
    ('startup', 'corporate_memphis'), ('onboarding', 'corporate_memphis'), ('community', 'corporate_memphis'),
    ('audio', 'skeuomorphism'), ('daw', 'skeuomorphism'), ('music', 'retro'), ('vintage', 'retro'),
    ('smart home', 'neumorphism'), ('iot', 'neumorphism'), ('control', 'neumorphism'),
    ('productivity', 'flat_design'), ('tool', 'flat_design'), ('utility', 'flat_design'),
    ('luxury', 'victorian'), ('jewelry', 'victorian'), ('hotel', 'victorian'),
    ('arcade', 'pixel_art'), ('indie game', 'pixel_art'),
    ('aerospace', 'futuristic'), ('robotics', 'futuristic'),
    ('comic', 'pop_art'), ('festival', 'maximalism'), ('art', 'collage'),
]

_DEFAULT_STYLE = 'minimalism'


class DesignStyleEngine:
    """Applies a named design style + original art to a generated project."""

    DEFAULT_STYLE = _DEFAULT_STYLE
    STYLES: Dict[str, Dict[str, Any]] = dict(_STYLE_CATALOG)

    @classmethod
    def register_style(cls, style: Dict[str, Any]) -> None:
        """Add a plug-in style pack (keeps the catalog extensible)."""
        assert style.get('id'), 'style needs an id'
        assert style.get('color'), 'style needs a color palette'
        cls.STYLES[style['id']] = style
        agent_logger.info(f"DesignStyleEngine: registered style pack '{style['id']}'")

    # ── Style resolution ───────────────────────────────────────────────────
    def resolve_style(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """User-selected style wins; otherwise auto-suggest from industry."""
        raw_requested = str(spec.get('design_style') or '').strip().lower().replace('-', '_').replace(' ', '_')
        requested = STYLE_ALIASES.get(raw_requested, raw_requested)
        if requested in self.STYLES:
            style = self.STYLES[requested]
        else:
            look = ' '.join(
                str(spec.get(k) or '')
                for k in ('industry', 'website_type', 'template', 'category', 'design_style')
            ).lower()
            style_id = self.DEFAULT_STYLE
            for alias_k, target_style in STYLE_ALIASES.items():
                if alias_k in look:
                    style_id = target_style
                    break
            else:
                for keyword, candidate in _INDUSTRY_STYLE_MAP:
                    if keyword in look:
                        style_id = candidate
                        break
            style = self.STYLES.get(style_id, self.STYLES[self.DEFAULT_STYLE])
        return style

    # ── Tokens ─────────────────────────────────────────────────────────────
    def build_tokens(self, style: Dict[str, Any], project_name: str) -> Dict[str, Any]:
        """Central design tokens consumed across the whole project."""
        palette = style['color']
        return {
            'style': style['id'],
            'name': style['name'],
            'dna': style['dna'],
            'project_name': project_name,
            'palette': palette,
            'palette_hsl': {
                k: (_hex_to_hsl(v) if v.startswith('#') else v)
                for k, v in palette.items()
            },
            'typography': {
                'display': style['fonts']['display'],
                'sans': style['fonts']['sans'],
                'mono': style['fonts']['mono'],
                'scale': [12, 14, 16, 18, 24, 30, 36, 48, 64],
            },
            'radius': style['radius'],
            'shadow': style['shadow'],
            'border': style['border'],
            'effects': style['effects'],
            'weight': style.get('weight', 'medium'),
            'composition': style.get('composition', 'blocks'),
            'generated_by': 'lumicorepro-design-engine',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        }

    def _abbr(self, name: str, limit: int = 42) -> str:
        cleaned = re.sub(r'[^a-zA-Z0-9]+', ' ', name).strip().title()
        return cleaned[:limit] if cleaned else 'Original Artwork'

    def apply(self, project_dir: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Apply the resolved design style + generate original style-matched art."""
        style = self.resolve_style(spec)
        style_id = style['id']
        project_name = spec.get('project_name') or os.path.basename(project_dir) or 'site'
        tokens = self.build_tokens(style, project_name)

        frontend = Path(project_dir) / 'frontend'
        public_assets = frontend / 'public' / 'assets'
        base_dir = public_assets / style_id
        seed = int(hashlib.sha1(f'{project_name}::{style_id}'.encode('utf-8')).hexdigest()[:8], 16)
        rng = random.Random(seed)
        written: List[Dict[str, Any]] = []
        manifest_entries: List[Dict[str, Any]] = []

        specs: List[Tuple[str, str, int]] = [
            ('hero', 'hero', 4),
            ('icons', 'icons', 12),
            ('backgrounds', 'backgrounds', 3),
            ('illustrations', 'illustrations', 5),
            ('mockups', 'mockups', 3),
        ]
        for category, folder, count in specs:
            for idx in range(count):
                rel, content, title = self._render(category, style, rng, idx, project_name)
                full = base_dir / folder / rel
                FileManager.write_file(str(full), content)
                manifest_entries.append({
                    'file': f'assets/{style_id}/{folder}/{rel}',
                    'category': category,
                    'style': style_id,
                    'title': title,
                    'prompt': self._prompt_for(category, style, idx),
                    'license': 'Self-generated original vector art - free for commercial use',
                    'palette': list(dict.fromkeys(v for v in style['color'].values())),
                    'seed': seed,
                })
                written.append(str(full))

        manifest_path = public_assets / 'manifest.json'
        FileManager.write_json(
            str(manifest_path),
            {
                'generator': 'lumicorepro-design-engine',
                'project': project_name,
                'style': style_id,
                'generated_at': tokens['timestamp'],
                'license': 'All assets are self-generated original vector artwork (public-domain equivalent). '
                           'No stock, no scraped, and no copyrighted material.',
                'count': len(manifest_entries),
                'assets': manifest_entries,
            }
        )

        tokens_paths = self._write_tokens(frontend, tokens)
        css_path = self._inject_css(frontend, style, tokens)
        md_path = self._write_design_doc(project_dir, style, tokens, manifest_entries)

        report = {
            'style': style_id,
            'name': style['name'],
            'dna': style['dna'],
            'accent': style['color'].get('accent', style['color'].get('primary')),
            'palette': style['color'],
            'typography': style['fonts'],
            'selected_by': 'user' if spec.get('design_style') else 'auto-suggested (industry match)',
            'tokens_json': tokens_paths[0],
            'css_file': css_path,
            'assets_dir': str(public_assets / style_id),
            'assets_generated': len(written),
            'manifest_path': str(manifest_path),
            'design_doc': md_path,
        }
        agent_logger.info(
            f"DesignStyleEngine: style='{style_id}' assets={len(written)} "
            f"tokens={tokens_paths[0]} manifest={manifest_path}"
        )
        return report
    # ── Files ──────────────────────────────────────────────────────────────
    def _write_tokens(self, frontend: Path, tokens: Dict[str, Any]) -> List[str]:
        """Central design-tokens.json — project-root copy + frontend/src copy."""
        paths = [str(frontend / 'design-tokens.json'), str(frontend / 'src' / 'styles' / 'design-tokens.json')]
        for path in paths:
            FileManager.write_json(path, tokens)
        return paths

    def _inject_css(self, frontend: Path, style: Dict[str, Any], tokens: Dict[str, Any]) -> str:
        """Append style-matched :root tokens + utilities to index.css (non-destructive)."""
        css_path = frontend / 'src' / 'index.css'
        existing = FileManager.read_file(str(css_path)).rstrip()
        palette = tokens['palette_hsl']
        hsl = lambda key: palette.get(key) or '0 0% 100%'

        vars_block = [':root {']
        raw = palette
        color = style['color']
        fg_primary = _fg_for(color['primary']) if color['primary'].startswith('#') else '#ffffff'
        fg_secondary = _fg_for(color['secondary']) if color['secondary'].startswith('#') else '#0f172a'
        fg_card = _fg_for(color.get('card', color['bg'])) if color['card'].startswith('#') else '#0f172a'
        fg_accent = _fg_for(color['accent']) if color['accent'].startswith('#') else '#0f172a'
        fg_muted = _fg_for(color.get('muted', color['secondary'])) \
            if color.get('muted', '').startswith('#') else '#64748b'

        # Tailwind token contract (see monorepo tailwind.config.js):
        # hsl(var(--X) / <alpha-value>) — vars hold bare 'h s% l%' triplets.
        contract = [
            ('--background', '@bg'),
            ('--foreground', '@text'),
            ('--primary', '@primary'),
            ('--primary-foreground', None),
            ('--secondary', '@secondary'),
            ('--secondary-foreground', None),
            ('--card', '@card'),
            ('--card-foreground', None),
            ('--accent', '@accent'),
            ('--accent-foreground', None),
            ('--muted', '@muted'),
            ('--muted-foreground', None),
            ('--destructive', '@destructive'),
            ('--destructive-foreground', '#f8fafc'),
            ('--border', '@border'),
            ('--ring', '@primary'),
        ]
        var_lookup = {
            '@bg': raw['bg'], '@text': raw['text'], '@primary': hsl('primary'),
            '@secondary': hsl('secondary'), '@card': hsl('card'), '@accent': hsl('accent'),
            '@muted': hsl('muted'), '@border': hsl('border'), '@surface': hsl('surface'),
            '@destructive': _hex_to_hsl('#ef4444'),
        }
        fg_map = {
            '--primary-foreground': fg_primary, '--secondary-foreground': fg_secondary,
            '--card-foreground': fg_card, '--accent-foreground': fg_accent,
            '--muted-foreground': fg_muted,
        }
        for token, src in contract:
            if src is None:
                value = fg_map[token]
            elif src.startswith('@'):
                value = var_lookup[src]
            else:
                value = src
            vars_block.append(f'  {token}: {value};')
        vars_block.append(f'  --radius: {style["radius"]["card"]};')
        vars_block.append(f'  --font-sans: {style["fonts"]["sans"]}, system-ui, sans-serif;')
        vars_block.append(f'  --font-display: {style["fonts"]["display"]}, system-ui, sans-serif;')
        vars_block.append(f'  --font-mono: {style["fonts"]["mono"]}, monospace;')
        vars_block.append(f'  --shadow-sm: {style["shadow"]["button"]};')
        vars_block.append(f'  --shadow-md: {style["shadow"]["card"]};')
        vars_block.append(f'  --shadow-lg: {style["shadow"]["card"]};')
        vars_block.append(f'  --shadow-xl: {style["shadow"]["card"]};')
        vars_block.append('}')
        vars_block.append(f'[data-style="{style["id"]}"] {{')
        vars_block.append(f'  --primary: {hsl("primary")};')
        vars_block.append(f'  --secondary: {hsl("secondary")};')
        vars_block.append(f'  --accent: {hsl("accent")};')
        vars_block.append('}')
        vars_block.append('body { color: hsl(var(--foreground) / 1); }')

        utility_css = {
            'glassmorphism': (
                '.glass-panel { background: rgba(255,255,255,0.06); backdrop-filter: blur(24px); '
                'border: 1px solid rgba(255,255,255,0.14); }'
            ),
            'neo_brutalism': (
                '.glass-panel { background: #ffffff; border: 3px solid #0f172a; '
                'box-shadow: 6px 6px 0 #0f172a; border-radius: 0; }'
            ),
            'neumorphism': (
                '.glass-panel { border-radius: 24px; '
                'box-shadow: 12px 12px 28px #b8bec7, -12px -12px 28px #ffffff; }'
            ),
            'claymorphism': (
                '.glass-panel { border-radius: 28px; '
                'box-shadow: 0 18px 40px rgba(244,114,182,0.28), inset 0 -6px 12px rgba(191,64,126,0.25); }'
            ),
            'cyberpunk': (
                '.glass-panel { background: #111118; border: 1px solid rgba(34,211,238,0.35); '
                'box-shadow: 0 0 24px rgba(34,211,238,0.12); }'
            ),
            'aurora': (
                '.glass-panel { background: linear-gradient(135deg, rgba(139,92,246,0.18), rgba(236,72,153,0.12)); '
                'border: 1px solid rgba(139,92,246,0.25); backdrop-filter: blur(40px); }'
            ),
            'organic': (
                '.glass-panel { border-radius: 32px; border: none; '
                'box-shadow: 0 12px 32px rgba(16,185,129,0.16); }'
            ),
        }
        additions = '\n'.join(vars_block)
        for key, rule in utility_css.items():
            if key == style['id']:
                additions += '\n' + rule
        additions += (
            '\n/* Design System: %s - %s */\n'
            '/* Tokens: frontend/design-tokens.json */\n' % (style['name'], style['dna'])
        )

        try:
            FileManager.write_file(str(css_path), existing + '\n\n' + additions + '\n')
        except Exception as e:
            agent_logger.warning(f'DesignStyleEngine: css inject failed: {e}')
        return str(css_path)

    def _write_design_doc(
        self, project_dir: str, style: Dict[str, Any], tokens: Dict[str, Any],
        manifest_entries: List[Dict[str, Any]],
    ) -> str:
        md_path = os.path.join(project_dir, 'DESIGN-STYLE.md')
        asset_names = ', '.join(e['file'] for e in manifest_entries[:8])
        body = (
            f'# Design Style — {style["name"]}\n\n'
            f'- **Project:** `{tokens.get("project_name", "—")}`\n'
            f'- **Style id:** `{style["id"]}`\n'
            f'- **DNA:** {style["dna"]}\n'
            f'- **Typography:** {style["fonts"]["display"]} / {style["fonts"]["sans"]}\n'
            f'- **Tokens:** `frontend/design-tokens.json`, applied via CSS custom properties in '
            f'`frontend/src/index.css`\n'
            f'- **Original assets:** `frontend/public/assets/{style["id"]}/` (hero, icons, backgrounds, '
            f'illustrations, mockups) — 100% self-generated vector art. See `frontend/public/assets/manifest.json`.'
            f'\n- **Sample assets:** {asset_names}\n'
        )
        FileManager.write_file(md_path, body)
        return md_path

    def _prompt_for(self, category: str, style: Dict[str, Any], idx: int) -> str:
        return (
            f'Abstract {category.replace("_", " ")} for a {style["name"]} styled website; '
            f'palette {", ".join(style["color"].values())}; {style["dna"].lower()}'
        )

    # ── SVG helpers ────────────────────────────────────────────────────────
    @staticmethod
    def _svg(w: int, h: int, inner: str, extra_attrs: str = '') -> str:
        attrs = (f'xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" ' + extra_attrs).strip() + ' '
        return f'<svg {attrs}fill="none">{inner}</svg>'

    @staticmethod
    def _rect(x: int, y: int, w: int, h: int, fill: str, rx: int = 0, extra: str = '') -> str:
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" {extra}/>'

    @staticmethod
    def _circle(cx: int, cy: int, r: int, fill: str, extra: str = '') -> str:
        return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" {extra}/>'

    @staticmethod
    def _path(d: str, fill: str = 'none', stroke: str = 'none', sw: str = '1', extra: str = '') -> str:
        return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'

    def _pick(self, rng: random.Random, *values: str) -> str:
        return rng.choice(list(values))

    def _blur(self, did: str, std: str) -> str:
        return f'<filter id="{did}"><feGaussianBlur stdDeviation="{std}"/></filter>'

    def _hard_shadow(self, did: str, dx: str, dy: str) -> str:
        return (
            f'<filter id="{did}" x="-30%" y="-30%" width="160%" height="160%">'
            f'<feDropShadow dx="{dx}" dy="{dy}" stdDeviation="0" flood-color="#0f172a"/></filter>'
        )

    def _shadow(self, did: str, dx: str, dy: str, blur: str, color: str) -> str:
        return (
            f'<filter id="{did}" x="-40%" y="-40%" width="180%" height="180%">'
            f'<feDropShadow dx="{dx}" dy="{dy}" stdDeviation="{blur}" flood-color="{color}"/></filter>'
        )

    def _defs(self, *nodes: str) -> str:
        return f'<defs>{"".join(nodes)}</defs>' if nodes else '<defs></defs>'

    def _linear(self, did: str, stops: List[Tuple[str, str]]) -> str:
        stop_nodes = ''.join(
            f'<stop offset="{off}" stop-color="{col}"/>' for off, col in stops
        )
        return f'<linearGradient id="{did}" x1="0%" y1="0%" x2="100%" y2="100%">{stop_nodes}</linearGradient>'

    def _radial(self, did: str, stops: List[Tuple[str, str]]) -> str:
        stop_nodes = ''.join(
            f'<stop offset="{off}" stop-color="{col}"/>' for off, col in stops
        )
        return f'<radialGradient id="{did}" cx="50%" cy="50%" r="70%">{stop_nodes}</radialGradient>'

    def _bg(self, w: int, h: int, color: str) -> str:
        return self._rect(0, 0, w, h, color)

    # ── Render dispatcher ──────────────────────────────────────────────────
    def _render(self, category: str, style: Dict[str, Any], rng: random.Random, idx: int, project: str) -> Tuple[str, str, str]:
        p = style['color']
        pid = f'{style["id"]}_{category}_{idx}'
        title = self._abbr(project) + ' ' + category.title()

        if category == 'hero':
            rel = f'hero-{idx + 1}.svg'
            return rel, self._hero(style, rng, pid), title
        if category == 'icons':
            rel = f'icon-{idx + 1}.svg'
            return rel, self._icon(style, rng, pid, idx), f'{title} Icon {idx + 1}'
        if category == 'backgrounds':
            rel = f'bg-{idx + 1}.svg'
            return rel, self._background(style, rng, pid, idx), f'{title} Background {idx + 1}'
        if category == 'illustrations':
            rel = f'illustration-{idx + 1}.svg'
            return rel, self._illustration(style, rng, pid, idx), f'{title} Illustration {idx + 1}'
        rel = f'mockup-{idx + 1}.svg'
        return rel, self._mockup(style, rng, pid), f'{title} UI Mockup {idx + 1}'
    # ── Heroes (1600×900) ─────────────────────────────────────────────────—
    def _hero(self, style: Dict[str, Any], rng: random.Random, pid: str) -> str:
        p = style['color']
        comp = style.get('composition', 'blocks')
        W, H = 1600, 900
        bg = self._bg(W, H, p['bg'])
        if comp == 'glass':
            return self._hero_glass(style, p, pid, W, H, bg)
        if comp == 'neo':
            return self._hero_neo(style, p, pid, W, H, bg)
        if comp == 'bento':
            return self._hero_bento(style, p, pid, W, H, bg)
        if comp == 'neumorph':
            return self._hero_neumorph(style, p, pid, W, H, bg)
        if comp == 'clay':
            return self._hero_clay(style, p, pid, W, H, bg)
        if comp == 'metal':
            return self._hero_metal(style, p, pid, W, H, bg)
        if comp == 'neon':
            return self._hero_neon(style, p, pid, W, H, bg)
        if comp == 'people':
            return self._hero_people(style, p, pid, W, H, bg)
        if comp == 'editorial':
            return self._hero_editorial(style, p, pid, W, H, bg)
        if comp == 'grid':
            return self._hero_grid(style, p, pid, W, H, bg)
        if comp == 'aurora':
            return self._hero_aurora(style, p, pid, W, H, bg)
        if comp == 'blob':
            return self._hero_blob(style, p, pid, W, H, bg)
        if comp == 'chrome':
            return self._hero_chrome(style, p, pid, W, H, bg)
        return self._hero_blocks(style, p, pid, W, H, bg)

    def _hero_blocks(self, style, p, pid, W, H, bg):
        b = self._rect(120, 160, 640, 560, p['card'], 28)
        a = self._rect(900, 240, 120, 120, p['secondary'], 60)
        c = self._rect(900, 420, 420, 120, p['surface'], 24)
        line = self._rect(120, 740, 520, 8, p['accent'], 4)
        return self._svg(W, H, self._defs() + bg + b + a + c + line)

    def _hero_glass(self, style, p, pid, W, H, bg):
        g1 = self._radial(f'{pid}g1', [('0%', p['primary']), ('100%', '#0b1220')])
        blob = self._circle(1250, 220, 340, f'url(#{pid}g1)', 'opacity="0.6" filter="blur(40px)"')
        blur = self._blur(f'{pid}b', '36')
        c1 = self._rect(240, 180, 640, 540, 'rgba(255,255,255,0.06)', 20, f'filter="url(#{pid}b)"')
        c2 = self._rect(760, 120, 560, 300, 'rgba(255,255,255,0.08)', 20, f'filter="url(#{pid}b)"')
        c3 = self._rect(760, 460, 400, 300, 'rgba(255,255,255,0.05)', 20, f'filter="url(#{pid}b)"')
        stroke = self._path('M 240 200 L 1320 760', stroke=p['border'], sw='2')
        return self._svg(
            W, H,
            self._defs(g1, blur) + bg + blob + stroke + c1 + c2 + c3,
            'width="1600" height="900"',
        )

    def _hero_neo(self, style, p, pid, W, H, bg):
        shadow = self._hard_shadow(f'{pid}s', '18', '18')
        b1 = self._rect(200, 180, 560, 520, p['card'], 0, f'filter="url(#{pid}s)"')
        b2 = self._rect(860, 220, 260, 180, p['secondary'], 0, f'filter="url(#{pid}s)"')
        b3 = self._rect(860, 440, 420, 260, p['surface'], 0, f'filter="url(#{pid}s)"')
        chip = self._rect(300, 540, 160, 60, p['accent'], 0)
        return self._svg(W, H, self._defs(shadow) + bg + b1 + b2 + b3 + chip)

    def _hero_bento(self, style, p, pid, W, H, bg):
        grid = [
            (120, 140, 560, 620, p['card'], 28),
            (720, 140, 760, 240, p['surface'], 28),
            (720, 400, 360, 360, p['card'], 28),
            (1100, 400, 380, 360, p['surface'], 28),
        ]
        return self._svg(W, H, self._defs() + bg + ''.join(
            self._rect(*g) for g in grid
        ) + self._circle(1480, 180, 40, p['accent']))

    def _hero_neumorph(self, style, p, pid, W, H, bg):
        base = self._rect(0, 0, W, H, p['bg'])
        soft = self._shadow(f'{pid}s', '18', '18', '34', '#b8bec7')
        light = self._shadow(f'{pid}l', '-18', '-18', '34', '#ffffff')
        orb = self._circle(800, 450, 260, p['card'], f'filter="url(#{pid}s) url(#{pid}l)"')
        inner = self._circle(800, 450, 150, p['surface'], f'filter="url(#{pid}s) url(#{pid}l)"')
        return self._svg(W, H, self._defs(soft, light) + base + orb + inner)

    def _hero_clay(self, style, p, pid, W, H, bg):
        g1 = self._radial(f'{pid}g1', [('0%', p['secondary']), ('100%', '#f9a8d4')])
        g2 = self._radial(f'{pid}g2', [('0%', p['accent']), ('100%', '#fcd34d')])
        a = self._circle(1100, 260, 300, f'url(#{pid}g1)')
        b = self._circle(320, 560, 240, f'url(#{pid}g2)')
        c = self._rect(230, 220, 460, 320, p['card'], 60)
        return self._svg(W, H, self._defs(g1, g2) + bg + a + b + c)

    def _hero_metal(self, style, p, pid, W, H, bg):
        g = self._linear(f'{pid}g', [('0%', '#8a6a38'), ('50%', '#d9b98a'), ('100%', '#6a5030')])
        bar = self._rect(220, 180, 760, 300, f'url(#{pid}g)', 60)
        ring = self._circle(1100, 420, 180, 'none', extra=f'stroke="{p["accent"]}" stroke-width="28"')
        knob = self._circle(1180, 500, 60, g, extra='stroke="#6a5e4c" stroke-width="6"')
        return self._svg(W, H, self._defs(g) + bg + bar + ring + knob)

    def _hero_neon(self, style, p, pid, W, H, bg):
        bg = self._bg(W, H, p['bg'])
        glow = self._blur(f'{pid}b', '14')
        grid = self._path(f'M 0 180 L 1600 180 M 0 360 L 1600 360 M 0 540 L 1600 540 M 0 720 L 1600 720',
                          stroke=p['border'], sw='1', extra='opacity="0.5"')
        panel = self._rect(320, 240, 960, 420, p['card'], 14, f'filter="url(#{pid}b)"')
        neon = self._rect(360, 280, 480, 80, 'none', extra=f'stroke="{p["primary"]}" stroke-width="4" filter="url(#{pid}b)"')
        dot = self._circle(1180, 320, 36, p['secondary'], f'filter="url(#{pid}b)"')
        return self._svg(W, H, self._defs(glow) + bg + grid + panel + neon + dot)

    def _hero_people(self, style, p, pid, W, H, bg):
        parts = []
        for i, (x, y, s) in enumerate([(300, 420, 220), (500, 460, 190), (1020, 400, 250), (1240, 470, 180)]):
            col = [p['secondary'], p['accent'], p['primary']][i % 3]
            parts.append(self._circle(x, y, s, col))
            parts.append(self._circle(x + s // 5, y - s // 4, s // 4, p['bg']))
        banner = self._rect(760, 140, 320, 96, 'none', extra=f'stroke="{p["primary"]}" stroke-width="10"')
        return self._svg(W, H, self._defs() + bg + ''.join(parts[2:]) + banner)

    def _hero_editorial(self, style, p, pid, W, H, bg):
        col = ''
        for i, y in enumerate(range(140, 700, 52)):
            w = [780, 560, 900, 680, 420, 620][i % 6]
            col += self._rect(140, y, w, 26, p['text'], extra='opacity="0.85"')
        drop = self._rect(900, 300, 30, 380, p['accent'])
        return self._svg(W, H, self._defs() + bg + col + drop)

    def _hero_grid(self, style, p, pid, W, H, bg):
        diag = self._path(f'M 0 900 L 1600 0', stroke=p['primary'], sw='120', extra='opacity="0.9"')
        line = self._path(f'M 0 450 L 1600 450 M 800 0 L 800 900', stroke=p['border'], sw='2')
        block = self._rect(1040, 260, 320, 300, p['card'], extra=f'stroke="{p["text"]}" stroke-width="4"')
        dot = self._circle(1200, 410, 18, p['accent'])
        return self._svg(W, H, self._defs() + bg + diag + line + block + dot)

    def _hero_aurora(self, style, p, pid, W, H, bg):
        blur = self._blur(f'{pid}b', '80')
        orbs = ''
        for i, (cx, cy, r, col) in enumerate([
            (500, 300, 320, p['primary']), (900, 560, 360, p['secondary']), (1300, 240, 300, p['accent']),
        ]):
            orbs += self._circle(cx, cy, r, col, 'opacity="0.5" filter="blur(80px)"')
        panel = self._rect(260, 220, 1080, 460, p['card'], 28, f'filter="url(#{pid}b)"')
        return self._svg(W, H, self._defs(blur) + bg + orbs + panel)

    def _hero_blob(self, style, p, pid, W, H, bg):
        blob = self._path(
            'M 400 200 C 700 80 980 220 1050 480 C 1120 720 820 820 560 760 '
            'C 320 700 200 460 400 200 Z', fill=p['secondary'], extra='opacity="0.7"'
        )
        leaf = self._path('M 1180 300 C 1280 240 1380 260 1420 360 C 1320 420 1220 400 1180 300 Z', fill=p['accent'])
        card = self._rect(180, 420, 460, 220, p['card'], 32)
        return self._svg(W, H, self._defs() + bg + blob + leaf + card)

    def _hero_chrome(self, style, p, pid, W, H, bg):
        g = self._linear(f'{pid}g', [('0%', '#fda4af'), ('35%', '#ffffff'), ('70%', '#e879f9'), ('100%', '#7c3aed')])
        bar = self._rect(260, 300, 700, 140, f'url(#{pid}g)', 70)
        pill = self._rect(1040, 320, 300, 70, p['secondary'], 999)
        spark = self._path('M 1180 120 l 10 24 l 24 10 l -24 10 l -10 24 l -10 -24 l -24 -10 l 24 -10 Z', fill=p['accent'])
        return self._svg(W, H, self._defs(g) + bg + bar + pill + spark)
    # ── Icons (400×400) ─────────────────────────────────────────────────────
    _GLYPHS: Dict[str, str] = {
        'star': 'M12 2l2.9 6.6 7.1.6-5.4 4.7 1.6 7-6.2-3.6L5.8 21l1.6-7L2 9.2l7.1-.6L12 2z',
        'bolt': 'M13 2L4 14h6l-1 8 9-12h-6l1-8z',
        'heart': 'M12 21s-7.5-4.7-9.7-9C.7 8.6 2.6 4.5 6.6 4.5c2.2 0 3.6 1.3 4.4 2.6.8-1.3 2.2-2.6 4.4-2.6 4 0 5.9 4.1 4.3 7.5C19.5 16.3 12 21 12 21z',
        'chart': 'M4 20V10M10 20V4M16 20v-8M22 20H2',
        'shield': 'M12 2l8 3.5v5.2c0 5.4-3.4 9.5-8 11.3-4.6-1.8-8-5.9-8-11.3V5.5L12 2z',
        'globe': 'M12 2a10 10 0 100 20 10 10 0 000-20zm0 0c3 3 3 17 0 20m0-20c-3 3-3 17 0 20M2.5 8h19M2.5 16h19',
        'spark': 'M12 2l1.4 5.7 5.6-1.6-1.6 5.6L23 12l-5.6 4.2 1.6 5.6-5.6-1.6L12 26l-1.4-5.8-5.6 1.6 1.6-5.6L1 12l5.6-2.3L5 4.1l5.6 1.6L12 2z',
        'gear': 'M12 2l1.6 3 3.6-.4 1.2 3.4 3 2.2-1 3.6 1 3.6-3 2.2-1.2 3.4-3.6-.4-1.6 3-1.6-3-3.6.4-1.2-3.4-3-2.2 1-3.6-1-3.6 3-2.2L6.8 5l3.6.4L12 2zm0 7.5a2.5 2.5 0 100 5 2.5 2.5 0 000-5z',
        'rocket': 'M5 18s3-1 4-3l5-5c.5-2 .4-5 3-8-3 2.6-6 3.5-8 3l-5 5c-2 1-3 4-3 4zm0 0l-3 4m6-9l3 3',
        'box': 'M3 7l9-5 9 5-9 5-9-5zm0 5v7l9 5 9-5v-7M12 12v7',
        'smile': 'M12 2a10 10 0 100 20 10 10 0 000-20zM8.5 10h.01M15.5 10h.01M8 14.5s1.6 2.2 4 2.2 4-2.2 4-2.2',
        'leaf': 'M4 20C4 10 10 4 20 4c0 10-6 16-16 16zm0 0c2-6 6-10 11-13',
    }
    _ICON_NAMES: List[str] = ['star', 'bolt', 'heart', 'chart', 'shield', 'globe', 'spark', 'gear', 'rocket', 'box', 'smile', 'leaf']

    def _icon(self, style: Dict[str, Any], rng: random.Random, pid: str, idx: int) -> str:
        p = style['color']
        name = self._ICON_NAMES[idx % len(self._ICON_NAMES)]
        d = self._GLYPHS[name]
        chip_fill = p.get('card', p['bg'])
        glyph_col = p['primary']
        sw = {'thin': '2', 'medium': '3', 'bold': '4'}.get(style.get('weight', 'medium'), '3')

        glow = ''
        glow_nodes = ''
        if style.get('composition') in ('neon', 'aurora', 'glass'):
            glow = self._blur(f'{pid}glow', '6')
            glow_nodes = self._path(d, stroke=glyph_col, sw=sw, extra=f'filter="url(#{pid}glow)" opacity="0.7"')
        glyph = self._path(d, stroke=glyph_col, sw=sw, extra='stroke-linecap="round" stroke-linejoin="round"')
        inner = (
            self._rect(30, 30, 340, 340, chip_fill, 24 if style.get('composition') != 'neo' else 0)
            + self._circle(345, 55, 10, p['accent'])
            + glow_nodes
            + glyph
        )
        if style.get('composition') == 'neo':
            shadow = self._hard_shadow(f'{pid}sh', '10', '10')
            return self._svg(400, 400, self._defs(glow, shadow) + self._rect(30, 30, 340, 340, chip_fill, 0, f'filter="url(#{pid}sh)"') + glow_nodes + glyph)
        if style.get('composition') == 'neon':
            return self._svg(400, 400, self._defs(glow) + self._rect(30, 30, 340, 340, chip_fill, 12) + glyph + glow_nodes)
        return self._svg(400, 400, self._defs(glow) + inner)

    # ── Backgrounds (800×800) ─────────────────────────────────────────────
    def _background(self, style: Dict[str, Any], rng: random.Random, pid: str, idx: int) -> str:
        p = style['color']
        W = H = 800
        bg = self._bg(W, H, p['bg'])
        kind = idx % 3
        if kind == 0:
            dots = ''
            color = p['border'] if isinstance(p['border'], str) and p['border'].startswith('#') else p['accent']
            for x in range(40, W, 64):
                for y in range(40, H, 64):
                    dots += self._circle(x, y, 6, color, 'opacity="0.55"')
            return self._svg(W, H, self._defs() + bg + dots)
        if kind == 1:
            lines = ''
            for i in range(0, H, 56):
                y = i + (rng.randint(0, 8))
                lines += self._path(f'M 0 {y} L {W} {y}', stroke=p['border'] if p['border'].startswith('#') else p['muted'], sw='2', extra='opacity="0.35"')
            return self._svg(W, H, self._defs() + bg + lines)
        g = self._radial(f'{pid}g', [('0%', p['secondary']), ('100%', p['bg'])])
        orb = self._circle(400, 400, 340, f'url(#{pid}g)', 'opacity="0.5"')
        soft = self._circle(200, 180, 140, p['accent'], 'opacity="0.4"')
        return self._svg(W, H, self._defs(g) + bg + orb + soft)

    # ── Illustrations (800×600) ───────────────────────────────────────────
    def _illustration(self, style: Dict[str, Any], rng: random.Random, pid: str, idx: int) -> str:
        p = style['color']
        W, H = 800, 600
        bg = self._bg(W, H, p['bg'])
        comp = style.get('composition', 'blocks')
        scene = idx % 5
        if scene == 0:
            sun = self._circle(640, 140, 90, p['accent'])
            wave = self._path(f'M 40 430 C 180 360 320 460 460 400 C 600 340 700 390 760 420 L 760 560 L 40 560 Z', fill=p['secondary'], extra='opacity="0.7"')
            crest = self._path(f'M 40 470 C 200 400 360 500 520 430 C 640 380 700 430 760 450 L 760 560 L 40 560 Z', fill=p['primary'], extra='opacity="0.55"')
            return self._svg(W, H, self._defs() + bg + sun + wave + crest)
        if scene == 1:
            m1 = self._path(f'M 40 520 L 240 240 L 440 520 Z', fill=p['surface'])
            m2 = self._path(f'M 320 520 L 540 180 L 760 520 Z', fill=p['secondary'], extra='opacity="0.8"')
            dot = self._circle(540, 140, 26, p['accent'])
            return self._svg(W, H, self._defs() + bg + m1 + m2 + dot)
        if scene == 2:
            nodes = ''
            for i, (cx, cy) in enumerate([(220, 200), (540, 160), (400, 380), (640, 420)]):
                radius = [140, 100, 80, 60][i]
                nodes += self._circle(cx, cy, radius, [p['secondary'], p['accent'], p['primary'], p['surface']][i], 'opacity="0.85"')
            return self._svg(W, H, self._defs() + bg + nodes)
        if scene == 3:
            card = self._rect(180, 160, 440, 280, p['card'], 24, f'stroke="{p["border"]}" stroke-width="2"')
            bar = self._rect(220, 220, 200, 24, p['secondary'], 12)
            line = self._rect(220, 280, 340, 16, p['surface'], 8)
            btn = self._rect(220, 340, 140, 48, p['primary'], 12)
            return self._svg(W, H, self._defs() + bg + card + bar + line + btn)
        g = self._linear(f'{pid}g', [('0%', p['secondary']), ('100%', p['accent'])])
        pill = self._rect(160, 230, 480, 160, f'url(#{pid}g)', 80)
        ring = self._circle(680, 120, 60, 'none', extra=f'stroke="{p["primary"]}" stroke-width="12"')
        return self._svg(W, H, self._defs(g) + bg + pill + ring)

    # ── UI mockups (900×600) ───────────────────────────────────────────────
    def _mockup(self, style: Dict[str, Any], rng: random.Random, pid: str) -> str:
        p = style['color']
        W, H = 900, 600
        frame_col = p.get('card', '#ffffff')
        comp = style.get('composition', 'blocks')
        radius = 0 if comp in ('neo', 'grid', 'editorial') else 16
        frame = self._rect(70, 70, 760, 460, frame_col, radius)
        chrome = self._rect(70, 70, 760, 56, p['surface'], radius)
        dots = (self._circle(110, 98, 9, p['accent']) + self._circle(135, 98, 9, p['muted'])
                + self._circle(160, 98, 9, p['muted']))
        url = self._rect(210, 84, 480, 28, p['bg'], 14)
        hero = self._rect(110, 150, 540, 260, p['secondary'], radius, 'opacity="0.85"')
        side = self._rect(680, 150, 110, 120, p['accent'], 12, 'opacity="0.9"')
        side2 = self._rect(680, 290, 110, 120, p['primary'], 12, 'opacity="0.7"')
        btn = self._rect(150, 300, 200, 44, p['primary'], 10)
        return self._svg(W, H, self._defs() + frame + chrome + dots + url + hero + side + side2 + btn)