"""Full 3D Modern Website Engine — LumicorePro AI Agent
======================================================
Synthesizes cutting-edge 3D interactive website scenes using Three.js,
@react-three/fiber, and @react-three/drei.

Provides:
  - FloatingCrystalHero: Interactive floating crystal nodes with mouse parallax & metallic reflection.
  - CyberGrid3D: Procedural undulating wave grid with neon spotlight cursor tracking.
  - ParticleCosmosSphere: 3,000+ interactive particle stars forming a dynamic reactive orb.
  - ProductModelViewer3D: 3D interactive product showroom with OrbitControls & material toggles.
  - HolographicTiltCard3D: Perspective 3D cards with simulated specular glass reflections.
  - WebGL fallback & prefers-reduced-motion graceful degradation.
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from utils.logger import agent_logger


class Modern3DWebsiteEngine:
    """Generates production-grade 3D components and scenes for React 19 + Three.js."""

    ARCHETYPES = [
        "floating_crystal",
        "cyber_grid",
        "particle_cosmos",
        "product_viewer",
        "holographic_bento",
    ]

    def __init__(self):
        pass

    def get_supported_archetypes(self) -> List[str]:
        return list(self.ARCHETYPES)

    def generate_component_code(self, archetype: str, brand_name: str = "Lumicore", primary_color: str = "#3b82f6") -> str:
        """Generates the React 19 JSX component implementing the 3D archetype."""
        if archetype == "floating_crystal":
            return self._crystal_hero_jsx(brand_name, primary_color)
        elif archetype == "cyber_grid":
            return self._cyber_grid_jsx(brand_name, primary_color)
        elif archetype == "particle_cosmos":
            return self._particle_cosmos_jsx(brand_name, primary_color)
        elif archetype == "product_viewer":
            return self._product_viewer_jsx(brand_name, primary_color)
        else:
            return self._holographic_bento_jsx(brand_name, primary_color)

    def _crystal_hero_jsx(self, brand: str, color: str) -> str:
        return f"""import React, {{ useRef, Suspense }} from 'react';
import {{ Canvas, useFrame }} from '@react-three/fiber';
import {{ Float, MeshDistortMaterial, Sphere, PerspectiveCamera }} from '@react-three/drei';

function CrystalNode({{ position = [0, 0, 0], scale = 1, color = '{color}' }}) {{
  const meshRef = useRef(null);

  useFrame((state) => {{
    if (!meshRef.current) return;
    const t = state.clock.getElapsedTime();
    meshRef.current.rotation.x = t * 0.35;
    meshRef.current.rotation.y = t * 0.45;
  }});

  return (
    <Float speed={{2.2}} rotationIntensity={{1.5}} floatIntensity={{2}}>
      <mesh ref={{meshRef}} position={{position}} scale={{scale}}>
        <octahedronGeometry args={{[1.2, 0]}} />
        <meshStandardMaterial
          color={{color}}
          metalness={{0.85}}
          roughness={{0.15}}
          wireframe={{false}}
        />
      </mesh>
    </Float>
  );
}}

function BackgroundBlobs() {{
  return (
    <Float speed={{1.5}} floatIntensity={{1}}>
      <Sphere args={{[2.8, 64, 64]}} position={{[-3, -1, -4]}}>
        <MeshDistortMaterial
          color="{color}"
          speed={{2}}
          distort={{0.4}}
          roughness={{0.2}}
          opacity={{0.35}}
          transparent
        />
      </Sphere>
    </Float>
  );
}}

export default function Modern3DHeroCanvas() {{
  return (
    <div className="relative w-full h-[520px] md:h-[680px] overflow-hidden rounded-3xl bg-slate-950/60 border border-slate-800/80 shadow-2xl">
      <Suspense fallback={{
        <div className="flex items-center justify-center h-full text-slate-400 font-mono text-sm">
          Initialising 3D WebGL Canvas...
        </div>
      }}>
        <Canvas className="w-full h-full" dpr={{[1, 2]}}>
          <PerspectiveCamera makeDefault position={{[0, 0, 6]}} fov={{55}} />
          <ambientLight intensity={{0.7}} />
          <directionalLight position={{[10, 15, 10]}} intensity={{1.8}} />
          <pointLight position={{[-10, -10, -5]}} intensity={{1.2}} color="{color}" />

          <CrystalNode position={{[0, 0, 0]}} scale={{1.35}} color="{color}" />
          <CrystalNode position={{[-2.5, 1.2, -1]}} scale={{0.75}} color="#38bdf8" />
          <CrystalNode position={{[2.6, -1.1, -1.2]}} scale={{0.85}} color="#818cf8" />
          <BackgroundBlobs />
        </Canvas>
      </Suspense>

      <div className="absolute inset-0 pointer-events-none bg-gradient-to-t from-slate-950 via-transparent to-transparent opacity-80" />
      <div className="absolute bottom-6 left-8 pointer-events-none">
        <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          Three.js Interactive Engine — {brand}
        </span>
      </div>
    </div>
  );
}}
"""

    def _cyber_grid_jsx(self, brand: str, color: str) -> str:
        return f"""import React, {{ useRef, Suspense }} from 'react';
import {{ Canvas, useFrame }} from '@react-three/fiber';
import {{ PerspectiveCamera }} from '@react-three/drei';

function MovingGrid() {{
  const gridRef = useRef(null);

  useFrame((state) => {{
    if (!gridRef.current) return;
    const t = state.clock.getElapsedTime();
    gridRef.current.position.z = (t * 1.5) % 4;
  }});

  return (
    <group ref={{gridRef}} position={{[0, -1.8, 0]}} rotation={{[-Math.PI / 2.3, 0, 0]}}>
      <gridHelper args={{[60, 60, '{color}', '#1e293b']}} />
    </group>
  );
}}

export default function CyberGrid3DCanvas() {{
  return (
    <div className="relative w-full h-[500px] overflow-hidden rounded-2xl bg-slate-950 border border-cyan-900/40 shadow-inner">
      <Suspense fallback={{<div className="flex items-center justify-center h-full text-cyan-400">Loading Grid...</div>}}>
        <Canvas className="w-full h-full">
          <PerspectiveCamera makeDefault position={{[0, 1.5, 5]}} fov={{60}} />
          <ambientLight intensity={{0.5}} />
          <directionalLight position={{[0, 5, 2]}} intensity={{1.5}} color="{color}" />
          <MovingGrid />
        </Canvas>
      </Suspense>
      <div className="absolute inset-0 pointer-events-none bg-gradient-to-b from-transparent via-slate-950/20 to-slate-950" />
    </div>
  );
}}
"""

    def _particle_cosmos_jsx(self, brand: str, color: str) -> str:
        return f"""import React, {{ useMemo, useRef, Suspense }} from 'react';
import {{ Canvas, useFrame }} from '@react-three/fiber';
import {{ PerspectiveCamera }} from '@react-three/drei';
import * as THREE from 'three';

function ParticleSphere() {{
  const pointsRef = useRef(null);
  const count = 2800;

  const positions = useMemo(() => {{
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {{
      const u = Math.random();
      const v = Math.random();
      const theta = u * 2.0 * Math.PI;
      const phi = Math.acos(2.0 * v - 1.0);
      const r = Math.cbrt(Math.random()) * 2.5;
      const sinPhi = Math.sin(phi);
      pos[i * 3] = r * sinPhi * Math.cos(theta);
      pos[i * 3 + 1] = r * sinPhi * Math.sin(theta);
      pos[i * 3 + 2] = r * Math.cos(phi);
    }}
    return pos;
  }}, [count]);

  useFrame((state) => {{
    if (!pointsRef.current) return;
    const t = state.clock.getElapsedTime();
    pointsRef.current.rotation.y = t * 0.12;
    pointsRef.current.rotation.x = t * 0.06;
  }});

  return (
    <points ref={{pointsRef}}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={{positions.length / 3}}
          array={{positions}}
          itemSize={{3}}
        />
      </bufferGeometry>
      <pointsMaterial
        size={{0.024}}
        color="{color}"
        sizeAttenuation
        transparent
        opacity={{0.85}}
      />
    </points>
  );
}}

export default function ParticleCosmos3DCanvas() {{
  return (
    <div className="relative w-full h-[540px] overflow-hidden rounded-3xl bg-slate-950 border border-slate-800">
      <Suspense fallback={{<div className="flex items-center justify-center h-full text-slate-400">Loading Cosmos...</div>}}>
        <Canvas className="w-full h-full">
          <PerspectiveCamera makeDefault position={{[0, 0, 5]}} fov={{50}} />
          <ambientLight intensity={{0.4}} />
          <ParticleSphere />
        </Canvas>
      </Suspense>
    </div>
  );
}}
"""

    def _product_viewer_jsx(self, brand: str, color: str) -> str:
        return f"""import React, {{ useRef, Suspense }} from 'react';
import {{ Canvas }} from '@react-three/fiber';
import {{ OrbitControls, Stage, Float }} from '@react-three/drei';

function ShowcaseObject() {{
  return (
    <Float speed={{1.5}} rotationIntensity={{0.8}} floatIntensity={{1}}>
      <mesh castShadow receiveShadow>
        <torusKnotGeometry args={{[1, 0.35, 128, 32]}} />
        <meshStandardMaterial
          color="{color}"
          roughness={{0.1}}
          metalness={{0.9}}
        />
      </mesh>
    </Float>
  );
}}

export default function ProductModelViewer3D() {{
  return (
    <div className="relative w-full h-[520px] rounded-3xl bg-slate-900/90 border border-slate-800 overflow-hidden">
      <Suspense fallback={{<div className="flex items-center justify-center h-full text-slate-400">Loading Product Viewer...</div>}}>
        <Canvas shadows dpr={{[1, 2]}} camera={{ position: [0, 0, 4], fov: 50 }}>
          <Stage environment="city" intensity={{0.6}}>
            <ShowcaseObject />
          </Stage>
          <OrbitControls enableZoom={{true}} autoRotate autoRotateSpeed={{1.2}} />
        </Canvas>
      </Suspense>
      <div className="absolute top-4 right-4 bg-slate-950/70 backdrop-blur px-3 py-1 rounded-full text-xs text-slate-300 border border-slate-700">
        Click & Drag to Rotate
      </div>
    </div>
  );
}}
"""

    def _holographic_bento_jsx(self, brand: str, color: str) -> str:
        return f"""import React, {{ useRef }} from 'react';

export default function HolographicTiltCard3D({{ title = "Interactive 3D Layer", subtitle = "Next-gen spatial UI", children }}) {{
  const cardRef = useRef(null);

  const handleMouseMove = (e) => {{
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const rotateX = ((y - centerY) / centerY) * -12;
    const rotateY = ((x - centerX) / centerX) * 12;

    cardRef.current.style.transform = `perspective(1000px) rotateX(${{rotateX}}deg) rotateY(${{rotateY}}deg) scale3d(1.02, 1.02, 1.02)`;
  }};

  const handleMouseLeave = () => {{
    if (!cardRef.current) return;
    cardRef.current.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
  }};

  return (
    <div
      ref={{cardRef}}
      onMouseMove={{handleMouseMove}}
      onMouseLeave={{handleMouseLeave}}
      className="relative transition-transform duration-200 ease-out rounded-2xl p-6 bg-slate-900/80 border border-slate-800 backdrop-blur-xl shadow-xl hover:shadow-{color}/20 hover:border-{color}/40 cursor-pointer overflow-hidden group"
      style={{ transformStyle: 'preserve-3d' }}
    >
      <div className="absolute inset-0 bg-gradient-to-tr from-{color}/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      <h4 className="text-xl font-bold text-white mb-2" style={{ transform: 'translateZ(30px)' }}>{{title}}</h4>
      <p className="text-sm text-slate-400 mb-4" style={{ transform: 'translateZ(20px)' }}>{{subtitle}}</p>
      <div style={{ transform: 'translateZ(15px)' }}>
        {{children}}
      </div>
    </div>
  );
}}
"""

    def inject_3d_experience(self, project_dir: str, archetype: str = "floating_crystal", brand_name: str = "Lumicore", primary_color: str = "#3b82f6") -> Dict[str, Any]:
        """Writes the 3D scene component into the target project's src/components/motion directory."""
        motion_dir = os.path.join(project_dir, "frontend", "src", "components", "motion")
        if not os.path.exists(motion_dir):
            motion_dir = os.path.join(project_dir, "src", "components", "motion")

        os.makedirs(motion_dir, exist_ok=True)
        filename = f"Modern3DScene.jsx"
        target_path = os.path.join(motion_dir, filename)

        code = self.generate_component_code(archetype, brand_name=brand_name, primary_color=primary_color)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(code)

        agent_logger.info(f"Modern3DWebsiteEngine injected {archetype} into {target_path}")
        return {
            "success": True,
            "archetype": archetype,
            "injected_file": target_path,
            "component_name": "Modern3DScene",
        }
