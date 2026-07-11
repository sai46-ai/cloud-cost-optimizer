import React, { useRef, useMemo, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Environment, Sparkles } from '@react-three/drei';
import * as THREE from 'three';
import useStore from '../../store';

// ─── Subtle idle camera drift ──────────────────────────────────────────────
function CameraDrift() {
  const basePos = useRef(new THREE.Vector3(0, 0, 12));

  useFrame(({ clock, camera }) => {
    const t = clock.elapsedTime;
    camera.position.x = basePos.current.x + Math.sin(t * 0.08) * 0.4;
    camera.position.y = basePos.current.y + Math.cos(t * 0.05) * 0.25;
    camera.position.z = basePos.current.z + Math.sin(t * 0.06) * 0.15;
    camera.lookAt(0, 0, 0);
  });
  return null;
}

// ─── Particle data-node ────────────────────────────────────────────────────
interface DataNodeProps {
  position: [number, number, number];
  radius: number;
  color: string;
  speed: number;
  phaseOffset: number;
}

function DataNode({ position, radius, color, speed, phaseOffset }: DataNodeProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const origin = useRef(new THREE.Vector3(...position));

  useFrame(({ clock }) => {
    if (!meshRef.current) return;
    const t = clock.elapsedTime * speed + phaseOffset;
    meshRef.current.position.x = origin.current.x + Math.sin(t * 0.7) * 0.35;
    meshRef.current.position.y = origin.current.y + Math.cos(t * 0.5) * 0.28;
    meshRef.current.position.z = origin.current.z + Math.sin(t * 0.4) * 0.2;
    // Subtle pulse
    const pulse = 1 + Math.sin(t * 2.1 + phaseOffset) * 0.12;
    meshRef.current.scale.setScalar(pulse);
  });

  const geometry = useMemo(() => new THREE.SphereGeometry(radius, 16, 16), [radius]);
  const material = useMemo(() => new THREE.MeshStandardMaterial({
    color: color,
    roughness: 0.1,
    metalness: 0.3,
    emissive: color,
    emissiveIntensity: 0.35,
    transparent: true,
    opacity: 0.82
  }), [color]);

  useEffect(() => {
    return () => {
      geometry.dispose();
      material.dispose();
    };
  }, [geometry, material]);

  return (
    <mesh ref={meshRef} position={position} geometry={geometry} material={material} />
  );
}

// ─── Connection tube between two node positions ────────────────────────────
function ConnectionLine({
  start,
  end,
  opacity = 0.12,
}: {
  start: [number, number, number];
  end: [number, number, number];
  opacity?: number;
}) {
  const geometry = useMemo(() => {
    const s = new THREE.Vector3(...start);
    const e = new THREE.Vector3(...end);
    const curve = new THREE.LineCurve3(s, e);
    return new THREE.TubeGeometry(curve, 6, 0.008, 4, false);
  }, [start, end]);

  useEffect(() => {
    return () => geometry.dispose();
  }, [geometry]);

  return (
    <mesh geometry={geometry}>
      <meshBasicMaterial color="#3b82f6" transparent opacity={opacity} />
    </mesh>
  );
}

// ─── Large translucent cloud-core sphere ───────────────────────────────────
function CloudCore() {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    if (!meshRef.current) return;
    const t = clock.elapsedTime;
    meshRef.current.rotation.y = t * 0.04;
    meshRef.current.rotation.x = Math.sin(t * 0.03) * 0.08;
  });

  return (
    <mesh ref={meshRef}>
      <icosahedronGeometry args={[2.4, 4]} />
      <meshStandardMaterial
        color="#60a5fa"
        roughness={0.6}
        metalness={0.1}
        transparent
        opacity={0.07}
        side={THREE.FrontSide}
        wireframe={false}
      />
    </mesh>
  );
}

// ─── Wireframe shell around the core ──────────────────────────────────────
function CloudCoreWireframe() {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    if (!meshRef.current) return;
    const t = clock.elapsedTime;
    meshRef.current.rotation.y = -t * 0.02;
    meshRef.current.rotation.z = t * 0.015;
  });

  return (
    <mesh ref={meshRef}>
      <icosahedronGeometry args={[2.6, 2]} />
      <meshBasicMaterial color="#93c5fd" transparent opacity={0.06} wireframe />
    </mesh>
  );
}

// ─── Orbiting ring ─────────────────────────────────────────────────────────
function OrbitRing({ radiusX, radiusZ, tilt, color, speed }: {
  radiusX: number;
  radiusZ: number;
  tilt: number;
  color: string;
  speed: number;
}) {
  const points = useMemo(() => {
    const pts: THREE.Vector3[] = [];
    // LineSegments needs pairs of points; build a circle from segments
    const segments = 128;
    for (let i = 0; i < segments; i++) {
      const a0 = (i / segments) * Math.PI * 2;
      const a1 = ((i + 1) / segments) * Math.PI * 2;
      pts.push(new THREE.Vector3(Math.cos(a0) * radiusX, 0, Math.sin(a0) * radiusZ));
      pts.push(new THREE.Vector3(Math.cos(a1) * radiusX, 0, Math.sin(a1) * radiusZ));
    }
    return pts;
  }, [radiusX, radiusZ]);

  const geometry = useMemo(() => {
    const g = new THREE.BufferGeometry().setFromPoints(points);
    return g;
  }, [points]);

  useEffect(() => {
    return () => geometry.dispose();
  }, [geometry]);

  const groupRef = useRef<THREE.Group>(null);
  useFrame(({ clock }) => {
    if (!groupRef.current) return;
    groupRef.current.rotation.y = clock.elapsedTime * speed;
  });

  return (
    <group ref={groupRef} rotation={[tilt, 0, 0]}>
      <lineSegments geometry={geometry}>
        <lineBasicMaterial color={color} transparent opacity={0.1} />
      </lineSegments>
    </group>
  );
}

// ─── Complete cloud infrastructure scene ──────────────────────────────────
const nodeData: { pos: [number, number, number]; r: number; color: string; speed: number; phase: number }[] = [
  { pos: [0, 0, 0],      r: 0.18, color: '#3b82f6', speed: 0.4, phase: 0 },     // central
  { pos: [3.5, 1.2, -1], r: 0.13, color: '#06b6d4', speed: 0.5, phase: 1.2 },   // AWS node
  { pos: [-3.2, 1.5, 0.5], r: 0.12, color: '#22c55e', speed: 0.45, phase: 2.4 }, // GCP node
  { pos: [2.2, -2.0, 1.2], r: 0.10, color: '#a78bfa', speed: 0.55, phase: 0.8 }, // Azure node
  { pos: [-2.5, -1.8, -1], r: 0.11, color: '#f59e0b', speed: 0.48, phase: 3.6 },
  { pos: [4.5, -0.5, 0],   r: 0.09, color: '#06b6d4', speed: 0.6,  phase: 1.8 },
  { pos: [-4.2, 0.3, -0.5],r: 0.09, color: '#3b82f6', speed: 0.52, phase: 4.2 },
  { pos: [1.5, 3.0, -2],  r: 0.08, color: '#22c55e', speed: 0.58, phase: 2.0 },
  { pos: [-1.2, -3.0, 1], r: 0.09, color: '#a78bfa', speed: 0.47, phase: 5.0 },
  { pos: [0.5, 2.5, 2],   r: 0.08, color: '#f59e0b', speed: 0.53, phase: 3.0 },
  // background scatter
  { pos: [-5.5, 2.0, -3], r: 0.07, color: '#60a5fa', speed: 0.35, phase: 1.5 },
  { pos: [5.8, 1.8, -2],  r: 0.07, color: '#34d399', speed: 0.38, phase: 2.8 },
  { pos: [-3.0, -3.5, 2], r: 0.07, color: '#c084fc', speed: 0.42, phase: 0.5 },
  { pos: [3.5, 3.5, 1.5], r: 0.07, color: '#fbbf24', speed: 0.36, phase: 4.5 },
];

const connections: [number, number][] = [
  [0, 1], [0, 2], [0, 3], [0, 4], [0, 5], [0, 6],
  [1, 5], [2, 6], [3, 7], [4, 8], [1, 7], [2, 9],
  [5, 10], [6, 10], [1, 11], [3, 12], [4, 13],
];

function CloudInfrastructureScene() {
  return (
    <group>
      <CloudCore />
      <CloudCoreWireframe />

      {/* Orbit rings */}
      <OrbitRing radiusX={4.5} radiusZ={4.5} tilt={0.3} color="#3b82f6" speed={0.03} />
      <OrbitRing radiusX={6.0} radiusZ={3.5} tilt={-0.5} color="#06b6d4" speed={-0.02} />
      <OrbitRing radiusX={5.5} radiusZ={5.5} tilt={1.1} color="#a78bfa" speed={0.015} />

      {/* Data nodes */}
      {nodeData.map((n, i) => (
        <DataNode key={i} position={n.pos} radius={n.r} color={n.color} speed={n.speed} phaseOffset={n.phase} />
      ))}

      {/* Connection lines */}
      {connections.map(([a, b], i) => (
        <ConnectionLine key={i} start={nodeData[a].pos} end={nodeData[b].pos} opacity={0.10} />
      ))}

      {/* Atmospheric sparkles / micro-particles */}
      <Sparkles
        count={120}
        scale={16}
        size={0.6}
        speed={0.2}
        opacity={0.18}
        color="#93c5fd"
        noise={0.5}
      />
      <Sparkles
        count={60}
        scale={10}
        size={0.8}
        speed={0.15}
        opacity={0.12}
        color="#a5f3fc"
        noise={0.3}
      />
    </group>
  );
}

// ─── Gradient sky plane ───────────────────────────────────────────────────
function SkyGradient({ theme }: { theme: 'dark' | 'light' }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const material = useMemo(() => {
    const isDark = theme === 'dark';
    return new THREE.ShaderMaterial({
      uniforms: {
        uColorTop: { value: new THREE.Color(isDark ? '#04060d' : '#dbeafe') },
        uColorBottom: { value: new THREE.Color(isDark ? '#0b0f19' : '#f0f7ff') },
      },
      vertexShader: `
        precision mediump float;
        varying vec2 vUv;
        void main() {
          vUv = uv;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        precision mediump float;
        uniform vec3 uColorTop;
        uniform vec3 uColorBottom;
        varying vec2 vUv;
        void main() {
          gl_FragColor = vec4(mix(uColorBottom, uColorTop, vUv.y), 1.0);
        }
      `,
      side: THREE.BackSide,
      depthWrite: false,
    });
  }, [theme]);

  useEffect(() => {
    return () => {
      material.dispose();
    };
  }, [material]);

  return (
    <mesh ref={meshRef} material={material} scale={[80, 80, 80]}>
      <sphereGeometry args={[1, 32, 32]} />
    </mesh>
  );
}

import { isWebGLAvailable } from '../../lib/utils';

// ─── Exported GlobalCanvas ─────────────────────────────────────────────────
export function GlobalCanvas() {
  const { theme } = useStore();
  const hasWebGL = useMemo(() => isWebGLAvailable(), []);

  if (!hasWebGL) {
    return (
      <div
        style={{
          position: 'fixed',
          inset: 0,
          width: '100%',
          height: '100vh',
          zIndex: 0,
          pointerEvents: 'none',
          background: theme === 'dark' 
            ? 'linear-gradient(to top, #0b0f19 0%, #04060d 100%)'
            : 'linear-gradient(to top, #f0f7ff 0%, #dbeafe 100%)',
        }}
      />
    );
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        width: '100%',
        height: '100vh',
        zIndex: 1,
        pointerEvents: 'none',
      }}
    >
      <Canvas
        camera={{ position: [0, 0, 12], fov: 50, near: 0.1, far: 200 }}
        dpr={[1, 2]}
        gl={{
          antialias: true,
          alpha: true,
          powerPreference: 'high-performance',
          outputColorSpace: THREE.SRGBColorSpace,
        }}
        style={{ background: 'transparent' }}
      >
        {/* Gradient background sky is removed to allow background video to show */}

        {/* Ambient lighting — soft, neutral */}
        <ambientLight intensity={1.2} color="#f0f4ff" />

        {/* Soft directional fill from upper left */}
        <directionalLight position={[-6, 8, 4]} intensity={0.6} color="#e0eaff" />

        {/* Cool blue rim from right */}
        <directionalLight position={[8, 2, -4]} intensity={0.4} color="#bfdbfe" />

        {/* Subtle warm fill from below */}
        <directionalLight position={[0, -6, 2]} intensity={0.2} color="#fefce8" />

        {/* HDRI environment — dawn: soft, bright, enterprise feel */}
        <React.Suspense fallback={null}>
          <Environment preset="dawn" background={false} />
        </React.Suspense>

        {/* Idle camera drift */}
        <CameraDrift />

        {/* Main 3D content */}
        <React.Suspense fallback={null}>
          <CloudInfrastructureScene />
        </React.Suspense>
      </Canvas>
    </div>
  );
}

