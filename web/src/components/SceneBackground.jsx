import { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

/* ── Floating Particles (Instanced for performance) ─────────────────────── */
function Particles({ count = 180 }) {
  const meshRef = useRef();
  const dummy = useMemo(() => new THREE.Object3D(), []);

  const particles = useMemo(() => {
    const arr = [];
    for (let i = 0; i < count; i++) {
      arr.push({
        position: [
          (Math.random() - 0.5) * 20,
          (Math.random() - 0.5) * 14,
          (Math.random() - 0.5) * 10,
        ],
        speed: 0.1 + Math.random() * 0.3,
        offset: Math.random() * Math.PI * 2,
        scale: 0.015 + Math.random() * 0.03,
      });
    }
    return arr;
  }, [count]);

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    particles.forEach((p, i) => {
      dummy.position.set(
        p.position[0] + Math.sin(t * p.speed + p.offset) * 0.5,
        p.position[1] + Math.cos(t * p.speed * 0.7 + p.offset) * 0.4,
        p.position[2] + Math.sin(t * p.speed * 0.5 + p.offset * 2) * 0.3
      );
      dummy.scale.setScalar(p.scale);
      dummy.updateMatrix();
      meshRef.current.setMatrixAt(i, dummy.matrix);
    });
    meshRef.current.instanceMatrix.needsUpdate = true;
  });

  return (
    <instancedMesh ref={meshRef} args={[null, null, count]}>
      <sphereGeometry args={[1, 8, 8]} />
      <meshBasicMaterial color="#c4b5fd" transparent opacity={0.4} />
    </instancedMesh>
  );
}

/* ── Nebula Blobs — soft ambient color masses ───────────────────────────── */
function NebulaBlob({ position, color, scale = 2, speed = 0.3 }) {
  const meshRef = useRef();

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    meshRef.current.position.x = position[0] + Math.sin(t * speed) * 0.8;
    meshRef.current.position.y = position[1] + Math.cos(t * speed * 0.6) * 0.5;
    meshRef.current.scale.setScalar(scale + Math.sin(t * speed * 0.4) * 0.2);
  });

  return (
    <mesh ref={meshRef} position={position}>
      <sphereGeometry args={[1, 16, 16]} />
      <meshBasicMaterial color={color} transparent opacity={0.035} />
    </mesh>
  );
}

/* ── Scene Contents ─────────────────────────────────────────────────────── */
function Scene() {
  return (
    <>
      <Particles count={180} />
      <NebulaBlob position={[-4, 2, -5]} color="#7c3aed" scale={3} speed={0.2} />
      <NebulaBlob position={[5, -1, -4]} color="#06b6d4" scale={2.5} speed={0.25} />
      <NebulaBlob position={[0, -3, -6]} color="#fbbf24" scale={2} speed={0.15} />
    </>
  );
}

/* ── Exported Canvas Wrapper ────────────────────────────────────────────── */
export default function SceneBackground() {
  return (
    <div
      aria-hidden="true"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 0,
        pointerEvents: "none",
      }}
    >
      <Canvas
        dpr={[1, 1.5]}
        camera={{ position: [0, 0, 8], fov: 45 }}
        gl={{ antialias: false, alpha: true, powerPreference: "low-power" }}
        style={{ background: "transparent" }}
      >
        <Scene />
      </Canvas>
    </div>
  );
}
