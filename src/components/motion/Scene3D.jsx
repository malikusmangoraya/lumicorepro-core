import React from 'react';
import { Canvas } from '@react-three/fiber';
import { cn } from '@/utils';

export default function Scene3D({
  children,
  className = '',
  camera = { position: [0, 0, 6], fov: 45 },
  dpr = [1, 2],
  gl = { antialias: true, alpha: true },
  style = {},
}) {
  return (
    <div className={cn('relative', className)} style={style}>
      <Canvas camera={camera} dpr={dpr} gl={gl}>
        <ambientLight intensity={0.5} />
        <directionalLight position={[5, 5, 5]} intensity={1} />
        <directionalLight position={[-5, -5, -5]} intensity={0.3} />
        {children}
      </Canvas>
    </div>
  );
}
