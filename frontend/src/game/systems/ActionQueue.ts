/**
 * ActionQueue - Producer-Consumer pattern for animation synchronization
 *
 * Solves the problem of backend sending events faster than animations can play.
 * Events are queued and consumed one at a time as animations complete.
 */

import { GameEvent } from './EventBus'

export class ActionQueue {
  private queue: GameEvent[] = []
  private isProcessing: boolean = false
  private onAction: ((event: GameEvent) => Promise<void>) | null = null

  constructor() {
    this.queue = []
    this.isProcessing = false
  }

  /**
   * Set the callback that processes each action
   */
  setActionHandler(handler: (event: GameEvent) => Promise<void>) {
    this.onAction = handler
  }

  /**
   * Add an event to the queue
   */
  enqueue(event: GameEvent) {
    this.queue.push(event)
    this.processNext()
  }

  /**
   * Process the next event in the queue
   */
  private async processNext() {
    if (this.isProcessing || this.queue.length === 0 || !this.onAction) {
      return
    }

    this.isProcessing = true
    const event = this.queue.shift()!

    try {
      await this.onAction(event)
    } catch (error) {
      console.error('Error processing action:', error)
    }

    this.isProcessing = false
    this.processNext()
  }

  /**
   * Clear all pending actions
   */
  clear() {
    this.queue = []
  }

  /**
   * Get the current queue length
   */
  get length(): number {
    return this.queue.length
  }

  /**
   * Check if currently processing
   */
  get processing(): boolean {
    return this.isProcessing
  }
}
