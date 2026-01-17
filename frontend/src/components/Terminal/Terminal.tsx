/**
 * Terminal - Log display component
 *
 * Shows the full text log of all events for detailed viewing.
 */

import { useEffect, useRef } from 'react'
import './Terminal.css'

interface GameEvent {
  event_id: string
  timestamp: string
  type: string
  agent_id: string
  data: Record<string, unknown>
}

interface TerminalProps {
  logs: GameEvent[]
}

export function Terminal({ logs }: TerminalProps) {
  const terminalRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Auto-scroll to bottom
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
  }, [logs])

  const getEventColor = (type: string): string => {
    switch (type) {
      case 'AGENT_SPEAK':
        return 'log-speak'
      case 'AGENT_THINK_START':
        return 'log-think'
      case 'TOOL_START':
      case 'TOOL_END':
        return 'log-tool'
      case 'ERROR':
        return 'log-error'
      case 'SYSTEM_READY':
      case 'SIMULATION_START':
      case 'SIMULATION_END':
        return 'log-system'
      default:
        return 'log-default'
    }
  }

  const formatEventContent = (event: GameEvent): string => {
    switch (event.type) {
      case 'AGENT_SPEAK':
        return event.data.content as string || ''
      case 'AGENT_THINK_START':
        return 'Processing...'
      case 'TOOL_START':
        return `Using ${event.data.tool_name || 'tool'}...`
      case 'TOOL_END':
        return `Result: ${event.data.result_preview || 'Done'}`
      case 'ERROR':
        return event.data.error as string || 'Unknown error'
      case 'SYSTEM_READY':
        return 'System ready!'
      case 'SIMULATION_START':
        return `Input: "${event.data.input || ''}"`
      case 'SIMULATION_END':
        return 'Simulation complete'
      default:
        return JSON.stringify(event.data)
    }
  }

  return (
    <div className="terminal">
      <div className="terminal-header">
        <span className="terminal-title">EVENT LOG</span>
        <span className="terminal-count">{logs.length}</span>
      </div>

      <div className="terminal-content" ref={terminalRef}>
        {logs.length === 0 ? (
          <div className="terminal-empty">
            Waiting for events...
          </div>
        ) : (
          logs.map((event, index) => (
            <div key={event.event_id || index} className={`log-entry ${getEventColor(event.type)}`}>
              <span className="log-agent">[{event.agent_id}]</span>
              <span className="log-type">{event.type}</span>
              <span className="log-content">{formatEventContent(event)}</span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
