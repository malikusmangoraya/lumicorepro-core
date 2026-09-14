import React from 'react';
import Scene3D from './Scene3D';
import ParticleField3D from './ParticleField3D';

const HeroCanvas = () => (
  <Scene3D className="w-full h-full" camera={{ position: [0, 0, 6], fov: 45 }}>
    <ParticleField3D
      count={300}
      spread={12}
      speed={0.0003}
      color="cyan"
      size={0.025}
      opacity={0.6}
    />
    <ParticleField3D
      count={100}
      spread={10}
      speed={0.0002}
      color="violet"
      size={0.02}
      opacity={0.4}
    />
  </Scene3D>
);

export default HeroCanvas;
