import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

export default function ParticleField3D({
  count = 500,
  spread = 8,
  speed = 0.0004,
  color = 'cyan',
  size = 0.03,
  opacity = 0.8,
}) {
  const meshRef = useRef(null);

  const [positions, velocities] = useMemo(() => {
    const pos = new Float32Array(count * 3);
    const vel = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * spread;
      pos[i * 3 + 1] = (Math.random() - 0.5) * spread;
      pos[i * 3 + 2] = (Math.random() - 0.5) * spread;
      vel[i * 3] = (Math.random() - 0.5) * speed;
      vel[i * 3 + 1] = (Math.random() - 0.5) * speed;
      vel[i * 3 + 2] = (Math.random() - 0.5) * speed;
    }
    return [pos, vel];
  }, [count, spread, speed]);

  useFrame(() => {
    if (!meshRef.current) return;
    const p = meshRef.current.geometry.attributes.position.array;
    for (let i = 0; i < count; i++) {
      p[i * 3] += velocities[i * 3];
      p[i * 3 + 1] += velocities[i * 3 + 1];
      p[i * 3 + 2] += velocities[i * 3 + 2];
      if (Math.abs(p[i * 3]) > spread / 2) velocities[i * 3] *= -1;
      if (Math.abs(p[i * 3 + 1]) > spread / 2) velocities[i * 3 + 1] *= -1;
      if (Math.abs(p[i * 3 + 2]) > spread / 2) velocities[i * 3 + 2] *= -1;
    }
    meshRef.current.geometry.attributes.position.needsUpdate = true;
  });

  return (
    <points ref={meshRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={count}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={size}
        color={color}
        transparent
        opacity={opacity}
        sizeAttenuation
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </points>
  );
}
