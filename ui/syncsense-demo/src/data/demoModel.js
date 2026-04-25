/**
 * demoModel.js
 *
 * Hardcoded demo data for the SyncSense conflict prediction demo.
 * No backend, no persistence — everything here is deterministic and local.
 * This file is the single source of truth for the initial scene state.
 */

// ─── Elements ─────────────────────────────────────────────────────────────────
// Each element maps to a mesh in the 3D scene.
// `position` is [x, y, z] matching Scene.jsx placement.

export const ELEMENTS = {
  'wall-1': {
    id: 'wall-1',
    type: 'wall',
    label: 'wall-1',
    position: [-4, 2, 0],   // centre of the mesh in Scene.jsx
  },
  'beam-1': {
    id: 'beam-1',
    type: 'beam',
    label: 'beam-1',
    position: [0, 4.2, 0],
  },
  'column-1': {
    id: 'column-1',
    type: 'column',
    label: 'column-1',
    position: [4, 2, 0],
  },
}

// ─── Users ────────────────────────────────────────────────────────────────────

export const USERS = {
  'user-you': {
    id: 'user-you',
    name: 'You',
    color: '#4fc3f7',   // light blue — used for avatar/highlight
    isLocal: true,
  },
  'user-james': {
    id: 'user-james',
    name: 'James',
    color: '#ff8a65',  // orange — used for avatar/highlight
    isLocal: false,
  },
}

// ─── Dependency map ───────────────────────────────────────────────────────────
// Format: dependentId → [ids it depends on]
// "beam-1 depends on wall-1" means if wall-1 moves, beam-1 may break.

export const DEPENDENCIES = {
  'beam-1': ['wall-1'],
}

/**
 * Returns all elements that are impacted when `elementId` is modified.
 * Walks the dependency map in reverse: who depends on this element?
 */
export function getImpactedElements(elementId) {
  return Object.entries(DEPENDENCIES)
    .filter(([, deps]) => deps.includes(elementId))
    .map(([dependent]) => dependent)
}

// ─── Edit event shape ─────────────────────────────────────────────────────────
// Not used yet — documents the shape that Phase 6 scripted events will emit.

/**
 * @typedef {Object} EditEvent
 * @property {string}   id          - unique event id, e.g. 'evt-001'
 * @property {string}   userId      - who triggered it, e.g. 'user-james'
 * @property {string}   elementId   - which element was changed, e.g. 'wall-1'
 * @property {string}   action      - 'move' | 'resize' | 'delete'
 * @property {number[]} [delta]     - [dx, dy, dz] offset applied (for move)
 * @property {number}   timestamp   - Date.now() when the event occurred
 */

export function makeEditEvent({ userId, elementId, action, delta = [0, 0, 0] }) {
  return {
    id: `evt-${Date.now()}`,
    userId,
    elementId,
    action,
    delta,
    timestamp: Date.now(),
  }
}

// ─── Conflict object shape ────────────────────────────────────────────────────

/**
 * @typedef {Object} Conflict
 * @property {string} id              - unique conflict id, e.g. 'conflict-001'
 * @property {string} type            - 'dependency_conflict'
 * @property {string} sourceUser      - user whose edit caused the conflict
 * @property {string} targetUser      - user whose work is impacted
 * @property {string} sourceElement   - element that was modified
 * @property {string} impactedElement - element that is now at risk
 * @property {'high'|'medium'|'low'} severity
 * @property {number} timestamp
 */

export function makeConflict({ sourceUser, targetUser, sourceElement, impactedElement, severity = 'high' }) {
  return {
    id: `conflict-${Date.now()}`,
    type: 'dependency_conflict',
    sourceUser,
    targetUser,
    sourceElement,
    impactedElement,
    severity,
    timestamp: Date.now(),
  }
}

// ─── Mock AI responses ────────────────────────────────────────────────────────
// TEMPORARY: These are hardcoded local responses standing in for a real AI API
// call. In production this would be replaced by a POST to the ai-layer service
// (coordination-service/ai-layer) which returns plain-English explanations from
// the language model.
//
// Keyed by `${sourceElement}→${impactedElement}` for deterministic lookup.

const MOCK_AI_RESPONSES = {
  'wall-1→beam-1': {
    warning:
      'James is modifying a wall your beam depends on.',
    recommendation:
      'This may break structural alignment. Wait for James to finish, or reattach beam-1 to another support before continuing.',
  },
}

/**
 * Returns the mock AI warning + recommendation for a given conflict.
 * Returns null if no canned response exists for this conflict pair.
 *
 * TODO: Replace with real API call to ai-layer once backend is ready.
 */
export function getMockAiRecommendation(conflict) {
  if (!conflict) return null
  const key = `${conflict.sourceElement}→${conflict.impactedElement}`
  return MOCK_AI_RESPONSES[key] ?? null
}

// ─── Initial app state shape ──────────────────────────────────────────────────
// Documents what the React state object will look like across all phases.

/**
 * @typedef {Object} DemoState
 * @property {EditEvent|null}  activeEdit    - most recent edit in progress
 * @property {Conflict|null}   activeConflict
 * @property {string[]}        activityFeed  - list of human-readable log strings
 */

export const INITIAL_STATE = {
  activeEdit: null,
  activeConflict: null,
  whatIfActive: false,
  activityFeed: [],
  // Google Docs-style presence: which element each user is currently focused on.
  // null means idle / not focused on anything.
  userPresence: {
    'user-james': null,
    'user-you':   null,
  },
}
