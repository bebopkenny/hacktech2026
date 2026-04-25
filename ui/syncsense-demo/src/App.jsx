import { useState } from 'react'
import { Canvas } from '@react-three/fiber'
import Scene from './components/Scene'
import Panel from './components/Panel'
import {
  INITIAL_STATE,
  USERS,
  makeEditEvent,
  makeConflict,
  getImpactedElements,
} from './data/demoModel'
import './App.css'

export default function App() {
  const [demoState, setDemoState] = useState(INITIAL_STATE)

  // ─── Presence helpers ─────────────────────────────────────────────────────

  function setPresence(userId, elementId) {
    setDemoState(prev => ({
      ...prev,
      userPresence: { ...prev.userPresence, [userId]: elementId },
    }))
  }

  // ─── Clicking a 3D element sets "your" presence on it ────────────────────
  // Clicking the same element again deselects (toggle).
  function handleElementClick(elementId) {
    setDemoState(prev => {
      const current = prev.userPresence['user-you']
      const next    = current === elementId ? null : elementId
      const feedEntry = next
        ? `You selected ${elementId}.`
        : `You deselected ${elementId}.`
      return {
        ...prev,
        userPresence: { ...prev.userPresence, 'user-you': next },
        activityFeed: [...prev.activityFeed, feedEntry],
      }
    })
  }

  // ─── Simulate James: presence → move → conflict ───────────────────────────
  // Staged to feel like a real collaborative session:
  //   0ms   — James's cursor appears on wall-1 (presence)
  //   600ms — James starts moving wall-1 (edit event)
  //   1500ms— Conflict detector fires, beam-1 highlighted
  function handleSimulateJames() {
    // Stage 0: James selects wall-1
    setDemoState(prev => ({
      ...prev,
      userPresence: { ...prev.userPresence, 'user-james': 'wall-1' },
      activityFeed: [...prev.activityFeed, `${USERS['user-james'].name} selected wall-1.`],
    }))

    // Stage 1: James moves the wall
    setTimeout(() => {
      const event = makeEditEvent({
        userId:    'user-james',
        elementId: 'wall-1',
        action:    'move',
        delta:     [2.5, 0, 0],
      })
      setDemoState(prev => ({
        ...prev,
        activeEdit:  event,
        activityFeed: [...prev.activityFeed, `${USERS['user-james'].name} moved wall-1.`],
      }))
    }, 600)

    // Stage 2: Conflict detection
    setTimeout(() => {
      const impacted = getImpactedElements('wall-1')
      if (impacted.length === 0) return

      const conflict = makeConflict({
        sourceUser:      'user-james',
        targetUser:      'user-you',
        sourceElement:   'wall-1',
        impactedElement: impacted[0],
        severity:        'high',
      })
      setDemoState(prev => ({
        ...prev,
        activeConflict: conflict,
        activityFeed: [
          ...prev.activityFeed,
          `Conflict detected: beam-1 depends on wall-1.`,
        ],
      }))
    }, 1500)
  }

  // ─── What-if simulation ───────────────────────────────────────────────────
  function handleWhatIf() {
    setDemoState(prev => ({
      ...prev,
      whatIfActive: true,
      activityFeed: [...prev.activityFeed, 'Impact simulation completed.'],
    }))
  }

  // ─── Reset ────────────────────────────────────────────────────────────────
  function handleReset() {
    setDemoState(INITIAL_STATE)
  }

  return (
    <div className="app-shell">

      <div className="viewport">
        <Canvas camera={{ position: [2, 8, 16], fov: 45 }} shadows>
          <Scene
            activeEdit={demoState.activeEdit}
            activeConflict={demoState.activeConflict}
            whatIfActive={demoState.whatIfActive}
            userPresence={demoState.userPresence}
            onElementClick={handleElementClick}
          />
        </Canvas>

        <div className="scene-hud">
          <div className="scene-hud-title">SyncSense</div>
          <div className="scene-hud-subtitle">
            AI Conflict Prediction Demo &mdash; Real-time warnings before collaborative edits break dependent work.
          </div>
          <div className="scene-hud-hint">Click any element to select it</div>
        </div>
      </div>

      <Panel
        activeEdit={demoState.activeEdit}
        activeConflict={demoState.activeConflict}
        whatIfActive={demoState.whatIfActive}
        activityFeed={demoState.activityFeed}
        userPresence={demoState.userPresence}
        onSimulateJames={handleSimulateJames}
        onWhatIf={handleWhatIf}
        onReset={handleReset}
      />

    </div>
  )
}
