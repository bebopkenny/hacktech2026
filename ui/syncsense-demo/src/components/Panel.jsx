import { USERS, getMockAiRecommendation } from '../data/demoModel'

// ─── Section wrapper ──────────────────────────────────────────────────────────

function Section({ title, children, variant }) {
  return (
    <div className={`panel-section${variant ? ` panel-section--${variant}` : ''}`}>
      <div className="panel-section-title">{title}</div>
      <div className="panel-section-body">{children}</div>
    </div>
  )
}

// ─── Live Users ───────────────────────────────────────────────────────────────
// Shows who is online + what element they are currently focused on (presence),
// similar to how Google Docs shows "James is on page 3".

function LiveUsers({ editingUserId, userPresence }) {
  return (
    <Section title="Live Users">
      {Object.values(USERS).map((user) => {
        const focused = userPresence?.[user.id] ?? null
        return (
          <div key={user.id} className="user-row">
            <span className="user-dot" style={{ background: user.color }} />
            <span className="user-name">{user.name}</span>
            {focused && !editingUserId && (
              <span
                className="user-focus-tag"
                style={{ '--user-color': user.color }}
              >
                → {focused}
              </span>
            )}
            {editingUserId === user.id && (
              <span className="user-badge">editing</span>
            )}
          </div>
        )
      })}
    </Section>
  )
}

// ─── Panel ────────────────────────────────────────────────────────────────────

export default function Panel({
  activeEdit,
  activeConflict,
  whatIfActive,
  activityFeed,
  userPresence,
  onSimulateJames,
  onWhatIf,
  onReset,
}) {
  const editingUserId = activeEdit?.userId ?? null

  const currentEditText = activeEdit
    ? `${USERS[activeEdit.userId]?.name ?? activeEdit.userId} moved ${activeEdit.elementId}.`
    : 'No active edit.'

  const aiResponse       = getMockAiRecommendation(activeConflict)
  const conflictWarning  = aiResponse?.warning ?? null
  const aiRecommendation = aiResponse?.recommendation ?? null

  const isDemoActive = !!activeEdit

  return (
    <aside className="panel">

      {/* Panel header / branding */}
      <div className="panel-header">
        <div className="panel-header-name">SyncSense</div>
        <div className="panel-header-tag">AI Conflict Prediction</div>
        <div className={`panel-status-dot ${isDemoActive ? 'active' : ''}`} />
      </div>

      {/* Live Users */}
      <LiveUsers editingUserId={editingUserId} userPresence={userPresence} />

      {/* Current Edit */}
      <Section title="Current Edit">
        <p className={activeEdit ? 'panel-text active' : 'panel-text muted'}>
          {currentEditText}
        </p>
      </Section>

      {/* Conflict Warning */}
      <Section title="Conflict Warning" variant={conflictWarning ? 'warn' : undefined}>
        {conflictWarning ? (
          <p className="panel-text warning">{conflictWarning}</p>
        ) : (
          <p className="panel-text muted">No conflicts detected.</p>
        )}
      </Section>

      {/* AI Recommendation */}
      <Section title="AI Recommendation">
        {aiRecommendation ? (
          <>
            <p className="panel-text ai">{aiRecommendation}</p>
            <span className="mock-badge">mock response</span>
          </>
        ) : (
          <p className="panel-text muted">—</p>
        )}
      </Section>

      {/* Impact Simulation — appears after "What if" */}
      {whatIfActive && (
        <Section title="Impact Simulation" variant="impact">
          <p className="panel-text impact">
            If you continue, beam-1 may lose support because wall-1 has moved.
          </p>
          <p className="panel-text impact-sub">
            See the dashed line in the scene marking the broken connection.
          </p>
        </Section>
      )}

      {/* Activity Feed */}
      {activityFeed.length > 0 && (
        <Section title="Activity">
          <ul className="activity-feed">
            {activityFeed.map((entry, i) => (
              <li key={i} className="activity-item">{entry}</li>
            ))}
          </ul>
        </Section>
      )}

      {/* Controls */}
      <div className="panel-controls">
        <button
          className="btn btn-primary"
          onClick={onSimulateJames}
          disabled={!!activeEdit}
        >
          Simulate James Moving Wall
        </button>
        <button
          className="btn btn-secondary"
          onClick={onWhatIf}
          disabled={!activeConflict || whatIfActive}
        >
          {whatIfActive ? 'Impact Simulated ✓' : 'What happens if I continue?'}
        </button>
        <button
          className="btn btn-reset"
          onClick={onReset}
          disabled={!isDemoActive}
        >
          Reset Demo
        </button>
      </div>

    </aside>
  )
}
