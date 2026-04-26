import { useRef, useLayoutEffect } from 'react'
import { useFrame } from '@react-three/fiber'
import { OrbitControls, Html, Line } from '@react-three/drei'
import * as THREE from 'three'
import { ELEMENTS, USERS } from '../data/demoModel'

// ─── Presence outline ─────────────────────────────────────────────────────────
// Renders a colored wireframe box slightly larger than the parent element,
// plus a floating name chip — like a Google Docs cursor label.
// `presence` is an array of { userId, color, name } from the parent element.

function PresenceOutlines({ presence, geomArgs, chipOffset }) {
  if (!presence || presence.length === 0) return null

  return presence.map((p, i) => {
    // Each extra user gets a slightly larger outline to avoid z-fighting
    const scale = 1 + 0.07 * (i + 1)
    return (
      <group key={p.userId}>
        {/* Wireframe outline box */}
        <mesh scale={scale}>
          <boxGeometry args={geomArgs} />
          <meshBasicMaterial color={p.color} wireframe transparent opacity={0.75} />
        </mesh>

        {/* Floating name chip — like Google Docs "James" label near cursor */}
        {i === 0 && (
          <Html position={chipOffset} distanceFactor={12}>
            <div
              className="presence-chip"
              style={{ '--presence-color': p.color }}
            >
              {p.name}
            </div>
          </Html>
        )}
      </group>
    )
  })
}

// ─── Wall ─────────────────────────────────────────────────────────────────────

const WALL_BASE = ELEMENTS['wall-1'].position

function Wall({ targetX, highlighted, label, presence, onClick }) {
  const ref = useRef()

  useLayoutEffect(() => {
    if (ref.current) ref.current.position.set(WALL_BASE[0], WALL_BASE[1], WALL_BASE[2])
  }, [])

  useFrame(() => {
    if (!ref.current) return
    ref.current.position.x = THREE.MathUtils.lerp(ref.current.position.x, targetX, 0.06)
  })

  return (
    <mesh
      ref={ref}
      castShadow
      onClick={(e) => { e.stopPropagation(); onClick('wall-1') }}
      onPointerOver={() => (document.body.style.cursor = 'pointer')}
      onPointerOut={() =>  (document.body.style.cursor = 'auto')}
    >
      <boxGeometry args={[0.4, 4, 6]} />
      <meshStandardMaterial
        color={highlighted ? '#ff8a65' : '#778899'}
        emissive={highlighted ? '#3a1500' : '#000000'}
        roughness={0.7}
      />

      <PresenceOutlines
        presence={presence}
        geomArgs={[0.4, 4, 6]}
        chipOffset={[0.6, 1.6, 3.2]}
      />

      <Html position={[0, 2.6, 0]} center distanceFactor={12}>
        <div className={`element-label${highlighted ? ' label-editing' : presence?.length ? ' label-selected' : ''}`}>
          {label}
        </div>
      </Html>
    </mesh>
  )
}

// ─── Column ───────────────────────────────────────────────────────────────────

function Column({ position, label, presence, onClick }) {
  return (
    <mesh
      position={position}
      castShadow
      onClick={(e) => { e.stopPropagation(); onClick('column-1') }}
      onPointerOver={() => (document.body.style.cursor = 'pointer')}
      onPointerOut={() =>  (document.body.style.cursor = 'auto')}
    >
      <boxGeometry args={[0.6, 4, 0.6]} />
      <meshStandardMaterial color="#6eaec8" roughness={0.6} />

      <PresenceOutlines
        presence={presence}
        geomArgs={[0.6, 4, 0.6]}
        chipOffset={[0.8, 1.6, 0.6]}
      />

      <Html position={[0, 2.6, 0]} center distanceFactor={12}>
        <div className={`element-label${presence?.length ? ' label-selected' : ''}`}>
          {label}
        </div>
      </Html>
    </mesh>
  )
}

// ─── Beam ─────────────────────────────────────────────────────────────────────

function Beam({ position, label, conflicted, pulsing, presence, onClick }) {
  const matRef = useRef()

  useFrame(({ clock }) => {
    if (!pulsing || !matRef.current) return
    const t = (Math.sin(clock.getElapsedTime() * 5) + 1) / 2
    matRef.current.emissiveIntensity = 0.4 + t * 0.8
  })

  const isHighlighted = conflicted || pulsing

  return (
    <mesh
      position={position}
      castShadow
      onClick={(e) => { e.stopPropagation(); onClick('beam-1') }}
      onPointerOver={() => (document.body.style.cursor = 'pointer')}
      onPointerOut={() =>  (document.body.style.cursor = 'auto')}
    >
      <boxGeometry args={[8.2, 0.4, 0.5]} />
      <meshStandardMaterial
        ref={matRef}
        color={isHighlighted ? '#ff4444' : '#c8a06e'}
        emissive={isHighlighted ? '#ff1111' : '#000000'}
        emissiveIntensity={conflicted && !pulsing ? 0.4 : 0}
        roughness={0.6}
      />

      <PresenceOutlines
        presence={presence}
        geomArgs={[8.2, 0.4, 0.5]}
        chipOffset={[0, 0.7, 0.6]}
      />

      <Html position={[0, 0.6, 0]} center distanceFactor={12}>
        <div className={`element-label${pulsing ? ' label-impact' : conflicted ? ' label-conflict' : presence?.length ? ' label-selected' : ''}`}>
          {label}
        </div>
      </Html>
    </mesh>
  )
}

// ─── Dependency line ──────────────────────────────────────────────────────────

function DependencyLine({ wallX }) {
  return (
    <Line
      points={[[wallX + 0.2, 4.0, 0], [-4.1, 4.2, 0]]}
      color="#ff4444"
      lineWidth={2}
      dashed
      dashScale={2}
      dashSize={0.3}
      gapSize={0.2}
    />
  )
}

// ─── Scene ────────────────────────────────────────────────────────────────────

export default function Scene({ activeEdit, activeConflict, whatIfActive, userPresence, onElementClick }) {
  const wallTargetX =
    activeEdit?.elementId === 'wall-1'
      ? WALL_BASE[0] + activeEdit.delta[0]
      : WALL_BASE[0]

  const wallHighlighted = activeEdit?.elementId === 'wall-1'
  const beamConflicted  = activeConflict?.impactedElement === 'beam-1'

  // Build per-element presence arrays from the userPresence map:
  // { 'wall-1': [{userId, color, name}, ...], 'beam-1': [...], ... }
  const elementPresence = {}
  if (userPresence) {
    Object.entries(userPresence).forEach(([userId, elementId]) => {
      if (!elementId) return
      if (!elementPresence[elementId]) elementPresence[elementId] = []
      elementPresence[elementId].push({
        userId,
        color: USERS[userId].color,
        name:  USERS[userId].name,
      })
    })
  }

  return (
    <>
      <color attach="background" args={['#111318']} />
      <ambientLight intensity={0.5} />
      <directionalLight position={[8, 16, 8]} intensity={1.2} castShadow />

      {/* Floor plate */}
      <mesh position={[0, -0.1, 0]} receiveShadow>
        <boxGeometry args={[22, 0.2, 14]} />
        <meshStandardMaterial color="#1a2535" roughness={0.9} />
      </mesh>

      {/* Grid */}
      <gridHelper args={[22, 22, '#2a3a4a', '#2a3a4a']} position={[0, 0.01, 0]} />

      {/* BIM elements */}
      <Wall
        targetX={wallTargetX}
        highlighted={wallHighlighted}
        label="wall-1"
        presence={elementPresence['wall-1']}
        onClick={onElementClick}
      />
      <Column
        position={ELEMENTS['column-1'].position}
        label="column-1"
        presence={elementPresence['column-1']}
        onClick={onElementClick}
      />
      <Beam
        position={ELEMENTS['beam-1'].position}
        label="beam-1"
        conflicted={beamConflicted}
        pulsing={whatIfActive}
        presence={elementPresence['beam-1']}
        onClick={onElementClick}
      />

      {whatIfActive && <DependencyLine wallX={wallTargetX} />}

      <OrbitControls
        makeDefault
        minDistance={6}
        maxDistance={40}
        maxPolarAngle={Math.PI / 2.1}
      />
    </>
  )
}
