/**
 * HUD - Heads-Up Display component
 *
 * Shows connection status and game controls.
 */

import './HUD.css'

interface HUDProps {
  isConnected: boolean
}

export function HUD({ isConnected }: HUDProps) {
  return (
    <div className="hud">
      <div className="hud-left">
        <span className="hud-title">PIXELGRAPH</span>
        <span className="hud-version">v0.1.0</span>
      </div>

      <div className="hud-right">
        <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
          <span className="status-dot" />
          <span className="status-text">
            {isConnected ? 'CONNECTED' : 'CONNECTING...'}
          </span>
        </div>
      </div>
    </div>
  )
}
