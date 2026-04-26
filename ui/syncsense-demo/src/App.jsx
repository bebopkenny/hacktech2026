import { useState, useEffect } from 'react'
import { Canvas } from '@react-three/fiber'
import Scene from './components/Scene'
import Panel from './components/Panel'
import {
  INITIAL_STATE,
  USERS,
  DEPENDENCIES,
  makeEditEvent,
  makeConflict,
  getImpactedElements,
} from './data/demoModel'
import './App.css'

const AI_LAYER_URL = 'http://localhost:8001'

export default function App() {
  const [demoState, setDemoState] = useState(INITIAL_STATE)
  const [aiResponse, setAiResponse] = useState(null)
  const [aiLoading, setAiLoading] = useState(false)

  // ─── Auto-seed: James joins and moves wall-1 on load ─────────────────────────
  // Simulates a real collaborative session — James is already editing when you open the app.
  useEffect(() => {
    const t1 = setTimeout(() => {
      setDemoState(prev => ({
        ...prev,
        userPresence: { ...prev.userPresence, 'user-james': 'wall-1' },
        activityFeed: ['James joined the session.', 'James selected wall-1.'],
      }))
    }, 1000)

    const t2 = setTimeout(() => {
      const event = makeEditEvent({
        userId:    'user-james',
        elementId: 'wall-1',
        action:    'move',
        delta:     [2.5, 0, 0],
      })
      setDemoState(prev => ({
        ...prev,
        activeEdit:   event,
        activityFeed: [...prev.activityFeed, 'James moved wall-1.'],
      }))
    }, 2200)

    return () => { clearTimeout(t1); clearTimeout(t2) }
  }, [])

  // ─── K2 conflict call ─────────────────────────────────────────────────────────
  async function callK2(conflict) {
    setAiLoading(true)
    try {
      const resp = await fetch(`${AI_LAYER_URL}/explain`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conflict_id: conflict.id,
          severity:    'error',
          elements:    [conflict.sourceElement, conflict.impactedElement],
          reason_code: 'host_modified_while_child_owned_by_other',
          context: {
            acting_session: USERS[conflict.sourceUser]?.name ?? conflict.sourceUser,
            host_category:  'Walls',
            child_category: 'Structural Framing',
            level:          'Level 3',
            action:         'move',
          },
        }),
      })
      const data = await resp.json()
      setAiResponse(data)
      setDemoState(prev => ({
        ...prev,
        activityFeed: [...prev.activityFeed, 'K2 Think V2 generated real-time conflict analysis.'],
      }))
    } catch {
      // AI layer unreachable — Panel falls back to mock automatically.
    } finally {
      setAiLoading(false)
    }
  }

  // ─── Real-time element click ──────────────────────────────────────────────────
  // When you click an element, check instantly if it conflicts with James's active edit.
  async function handleElementClick(elementId) {
    setDemoState(prev => {
      const current = prev.userPresence['user-you']
      const next    = current === elementId ? null : elementId
      return {
        ...prev,
        userPresence: { ...prev.userPresence, 'user-you': next },
        activityFeed: [...prev.activityFeed,
          next ? `You selected ${elementId}.` : `You deselected ${elementId}.`],
      }
    })

    // Real-time conflict check: does this element depend on what James is editing?
    const jamesEditId = demoState.activeEdit?.userId === 'user-james'
      ? demoState.activeEdit.elementId
      : null

    if (!jamesEditId) return

    const deps = DEPENDENCIES[elementId] ?? []
    if (!deps.includes(jamesEditId)) return

    // Conflict — James is editing something this element depends on.
    const conflict = makeConflict({
      sourceUser:      'user-james',
      targetUser:      'user-you',
      sourceElement:   jamesEditId,
      impactedElement: elementId,
      severity:        'high',
    })

    setDemoState(prev => ({
      ...prev,
      activeConflict: conflict,
      activityFeed: [...prev.activityFeed,
        `Conflict detected: ${elementId} depends on ${jamesEditId}.`],
    }))

    await callK2(conflict)
  }

  // ─── Simulate James (manual fallback) ────────────────────────────────────────
  function handleSimulateJames() {
    setDemoState(prev => ({
      ...prev,
      userPresence: { ...prev.userPresence, 'user-james': 'wall-1' },
      activityFeed: [...prev.activityFeed, `${USERS['user-james'].name} selected wall-1.`],
    }))

    setTimeout(() => {
      const event = makeEditEvent({
        userId:    'user-james',
        elementId: 'wall-1',
        action:    'move',
        delta:     [2.5, 0, 0],
      })
      setDemoState(prev => ({
        ...prev,
        activeEdit:   event,
        activityFeed: [...prev.activityFeed, `${USERS['user-james'].name} moved wall-1.`],
      }))
    }, 600)

    setTimeout(async () => {
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
        activityFeed: [...prev.activityFeed,
          `Conflict detected: beam-1 depends on wall-1.`],
      }))

      await callK2(conflict)
    }, 1500)
  }

  // ─── What-if simulation ───────────────────────────────────────────────────────
  function handleWhatIf() {
    setDemoState(prev => ({
      ...prev,
      whatIfActive: true,
      activityFeed: [...prev.activityFeed, 'Impact simulation completed.'],
    }))
  }

  // ─── Reset ────────────────────────────────────────────────────────────────────
  function handleReset() {
    setDemoState(INITIAL_STATE)
    setAiResponse(null)
    setAiLoading(false)
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
        aiResponse={aiResponse}
        aiLoading={aiLoading}
        onSimulateJames={handleSimulateJames}
        onWhatIf={handleWhatIf}
        onReset={handleReset}
      />

    </div>
  )
}
