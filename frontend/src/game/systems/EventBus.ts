/**
 * EventBus - Communication bridge between React and Phaser
 *
 * This allows React to send events to Phaser scenes and vice versa,
 * keeping the two frameworks decoupled.
 */

import Phaser from 'phaser'

export const GameEventBus = new Phaser.Events.EventEmitter()

// Type definitions for events
export interface GameEvent {
  event_id: string
  timestamp: string
  type: string
  agent_id: string
  data: Record<string, unknown>
}

// Event type constants
export const EVENT_TYPES = {
  // Agent events
  AGENT_THINK_START: 'AGENT_THINK_START',
  AGENT_SPEAK: 'AGENT_SPEAK',
  AGENT_IDLE: 'AGENT_IDLE',

  // Tool events
  TOOL_START: 'TOOL_START',
  TOOL_END: 'TOOL_END',

  // System events
  SYSTEM_READY: 'SYSTEM_READY',
  SIMULATION_START: 'SIMULATION_START',
  SIMULATION_END: 'SIMULATION_END',
  ERROR: 'ERROR',
} as const
