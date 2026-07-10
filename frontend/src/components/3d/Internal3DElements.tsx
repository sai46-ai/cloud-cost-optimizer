import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { isWebGLAvailable } from '../../lib/utils';

// --- Dashboard Data Cube ---
function DataCubeMesh({ color }: { color: string }) {
  const meshRef = useRef<THREE.Mesh>(null);
  
  useFrame(({ clock }) => {
    if (meshRef.current) {
      meshRef.current.rotation.x = clock.getElapsedTime() * 0.5;
      meshRef.current.rotation.y = clock.getElapsedTime() * 0.5;
    }
  });

  return (
    <mesh ref={meshRef}>
      <boxGeometry args={[2, 2, 2]} />
      <meshStandardMaterial 
        color={color} 
        wireframe 
        transparent 
        opacity={0.6}
        emissive={color}
        emissiveIntensity={0.2}
      />
    </mesh>
  );
}

export function DashboardDataCube() {
  const hasWebGL = React.useMemo(() => isWebGLAvailable(), []);
  if (!hasWebGL) return null;

  return (
    <div className="hidden md:block w-16 h-16 absolute -top-4 -right-4 pointer-events-none opacity-50">
      <Canvas camera={{ position: [0, 0, 5] }}>
        <ambientLight intensity={0.5} />
        <DataCubeMesh color="#3b82f6" />
      </Canvas>
    </div>
  );
}


// --- Analytics Network Graph ---
function NetworkGraphMesh() {
  const groupRef = useRef<THREE.Group>(null);
  
  useFrame(({ clock }) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = clock.getElapsedTime() * 0.2;
    }
  });

  const [geo1, geo2] = useMemo(() => {
    const g1 = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(1, 1, 0), new THREE.Vector3(-1, -0.5, 1)]);
    const g2 = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(-1, -0.5, 1), new THREE.Vector3(0, -1, -1)]);
    return [g1, g2];
  }, []);

  React.useEffect(() => {
    return () => {
      geo1.dispose();
      geo2.dispose();
    };
  }, [geo1, geo2]);

  return (
    <group ref={groupRef}>
      <mesh position={[1, 1, 0]}>
        <sphereGeometry args={[0.3, 16, 16]} />
        <meshStandardMaterial color="#06b6d4" emissive="#06b6d4" />
      </mesh>
      <mesh position={[-1, -0.5, 1]}>
        <sphereGeometry args={[0.2, 16, 16]} />
        <meshStandardMaterial color="#22c55e" emissive="#22c55e" />
      </mesh>
      <mesh position={[0, -1, -1]}>
        <sphereGeometry args={[0.25, 16, 16]} />
        <meshStandardMaterial color="#8b5cf6" emissive="#8b5cf6" />
      </mesh>
      {/* Lines between nodes */}
      <lineSegments geometry={geo1}>
        <lineBasicMaterial color="#06b6d4" transparent opacity={0.3} />
      </lineSegments>
      <lineSegments geometry={geo2}>
        <lineBasicMaterial color="#22c55e" transparent opacity={0.3} />
      </lineSegments>
    </group>
  );
}

export function AnalyticsNetworkGraph() {
  const hasWebGL = React.useMemo(() => isWebGLAvailable(), []);
  if (!hasWebGL) return null;

  return (
    <div className="hidden md:block absolute right-0 top-0 w-32 h-32 opacity-40 pointer-events-none">
      <Canvas camera={{ position: [0, 0, 4] }}>
        <ambientLight intensity={1} />
        <NetworkGraphMesh />
      </Canvas>
    </div>
  );
}

// --- Reports Rotating Cube ---
function AnalyticsCubeMesh() {
  const meshRef = useRef<THREE.Mesh>(null);
  
  useFrame(({ clock }) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = clock.getElapsedTime() * 0.3;
      meshRef.current.rotation.z = Math.sin(clock.getElapsedTime() * 0.5) * 0.2;
    }
  });

  return (
    <mesh ref={meshRef}>
      <dodecahedronGeometry args={[1.5, 0]} />
      <meshStandardMaterial 
        color="#f59e0b" 
        wireframe 
        transparent 
        opacity={0.4}
      />
    </mesh>
  );
}

export function ReportsAnalyticsCube() {
  const hasWebGL = React.useMemo(() => isWebGLAvailable(), []);
  if (!hasWebGL) return null;

  return (
    <div className="hidden md:block w-24 h-24 absolute right-8 top-8 opacity-30 pointer-events-none">
      <Canvas camera={{ position: [0, 0, 5] }}>
        <ambientLight intensity={1} />
        <AnalyticsCubeMesh />
      </Canvas>
    </div>
  );
}

// --- Settings Holographic Sphere ---
function HoloSphereMesh() {
  const meshRef = useRef<THREE.Mesh>(null);
  
  useFrame(({ clock }) => {
    if (meshRef.current) {
      meshRef.current.rotation.x = clock.getElapsedTime() * 0.1;
      meshRef.current.rotation.y = clock.getElapsedTime() * 0.2;
    }
  });

  return (
    <mesh ref={meshRef}>
      <sphereGeometry args={[1.5, 32, 32]} />
      <meshStandardMaterial 
        color="#ec4899" 
        wireframe 
        transparent 
        opacity={0.2}
      />
    </mesh>
  );
}

export function SettingsHoloSphere() {
  const hasWebGL = React.useMemo(() => isWebGLAvailable(), []);
  if (!hasWebGL) return null;

  return (
    <div className="hidden md:block w-20 h-20 absolute -right-2 top-0 opacity-40 pointer-events-none">
      <Canvas camera={{ position: [0, 0, 4] }}>
        <ambientLight intensity={1} />
        <HoloSphereMesh />
      </Canvas>
    </div>
  );
}

