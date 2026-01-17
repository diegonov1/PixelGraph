/**
 * MainScene - Primary Phaser scene for the PixelGraph game
 *
 * Handles rendering of agents, backgrounds, and animations.
 * Listens to events from the EventBus to update visuals.
 */

import Phaser from 'phaser'
import { AgentSprite } from '../entities/AgentSprite'
import { GameEventBus, GameEvent, EVENT_TYPES } from '../systems/EventBus'
import { ActionQueue } from '../systems/ActionQueue'

export class MainScene extends Phaser.Scene {
  private agents: Map<string, AgentSprite> = new Map()
  private actionQueue: ActionQueue
  private statusText!: Phaser.GameObjects.Text
  private gridGraphics!: Phaser.GameObjects.Graphics

  constructor() {
    super({ key: 'MainScene' })
    this.actionQueue = new ActionQueue()
  }

  preload() {
    // Assets are created programmatically in this version
  }

  create() {
    // Create retro grid background
    this.createBackground()

    // Create title
    this.add.text(this.cameras.main.width / 2, 30, 'PIXELGRAPH', {
      fontFamily: '"Press Start 2P", cursive',
      fontSize: '20px',
      color: '#ffffff',
      stroke: '#000000',
      strokeThickness: 4,
    }).setOrigin(0.5)

    // Create status text
    this.statusText = this.add.text(
      this.cameras.main.width / 2,
      this.cameras.main.height - 30,
      'Waiting for connection...',
      {
        fontFamily: '"Press Start 2P", cursive',
        fontSize: '8px',
        color: '#aaaaaa',
      }
    ).setOrigin(0.5)

    // Create default wizard agent at center
    this.createAgent('wizard', 'Wizard', this.cameras.main.width / 2, 250)

    // Set up action queue handler
    this.actionQueue.setActionHandler(async (event) => {
      await this.handleGameEvent(event)
    })

    // Listen for events from React
    GameEventBus.on('game-event', (event: GameEvent) => {
      // Some events should be processed immediately, others queued
      const immediateEvents = [EVENT_TYPES.SYSTEM_READY, EVENT_TYPES.SIMULATION_START, EVENT_TYPES.ERROR]

      if (immediateEvents.includes(event.type as typeof EVENT_TYPES[keyof typeof EVENT_TYPES])) {
        this.handleSystemEvent(event)
      } else {
        this.actionQueue.enqueue(event)
      }
    })
  }

  private createBackground() {
    // Create animated grid background
    this.gridGraphics = this.add.graphics()

    const width = this.cameras.main.width
    const height = this.cameras.main.height

    // Draw grid lines
    this.gridGraphics.lineStyle(1, 0x3a3a5a, 0.3)

    const gridSize = 32
    for (let x = 0; x <= width; x += gridSize) {
      this.gridGraphics.lineBetween(x, 0, x, height)
    }
    for (let y = 0; y <= height; y += gridSize) {
      this.gridGraphics.lineBetween(0, y, width, y)
    }

    // Add decorative pixels in corners
    this.addDecorativePixels()
  }

  private addDecorativePixels() {
    const graphics = this.add.graphics()
    const colors = [0x4a9a4a, 0x9a4a4a, 0x4a4a9a, 0x9a9a4a]

    // Random floating pixels
    for (let i = 0; i < 20; i++) {
      const x = Phaser.Math.Between(50, this.cameras.main.width - 50)
      const y = Phaser.Math.Between(60, this.cameras.main.height - 60)
      const color = colors[Math.floor(Math.random() * colors.length)]
      const size = Phaser.Math.Between(2, 4)

      graphics.fillStyle(color, 0.3)
      graphics.fillRect(x, y, size, size)
    }
  }

  private createAgent(agentId: string, displayName: string, x: number, y: number): AgentSprite {
    const agent = new AgentSprite(this, x, y, agentId, displayName)
    this.agents.set(agentId, agent)
    return agent
  }

  private getOrCreateAgent(agentId: string): AgentSprite {
    let agent = this.agents.get(agentId)
    if (!agent) {
      // Calculate position based on number of agents (circular layout)
      const numAgents = this.agents.size
      const centerX = this.cameras.main.width / 2
      const centerY = 250
      const radius = 150

      let x: number, y: number
      if (numAgents === 0) {
        x = centerX
        y = centerY
      } else {
        const angle = (numAgents / (numAgents + 1)) * Math.PI * 2 - Math.PI / 2
        x = centerX + Math.cos(angle) * radius
        y = centerY + Math.sin(angle) * radius * 0.5
      }

      agent = this.createAgent(agentId, agentId, x, y)
    }
    return agent
  }

  private handleSystemEvent(event: GameEvent) {
    switch (event.type) {
      case EVENT_TYPES.SYSTEM_READY:
        this.statusText.setText('Connected! Ready to start.')
        this.statusText.setColor('#4a9a4a')
        break

      case EVENT_TYPES.SIMULATION_START:
        this.statusText.setText('Simulation running...')
        this.statusText.setColor('#9a9a4a')
        break

      case EVENT_TYPES.ERROR:
        this.statusText.setText(`Error: ${event.data.error}`)
        this.statusText.setColor('#9a4a4a')
        break
    }
  }

  private async handleGameEvent(event: GameEvent): Promise<void> {
    const agent = this.getOrCreateAgent(event.agent_id)

    // Highlight the active agent, dim others
    this.agents.forEach((a, id) => {
      if (id === event.agent_id) {
        a.highlight()
      } else {
        a.unhighlight()
      }
    })

    switch (event.type) {
      case EVENT_TYPES.AGENT_THINK_START:
        agent.showThinking()
        await this.wait(500) // Brief delay before next event
        break

      case EVENT_TYPES.AGENT_SPEAK:
        const content = event.data.content as string || 'Hello!'
        await agent.say(content, Math.min(content.length * 50 + 1000, 5000))
        break

      case EVENT_TYPES.TOOL_START:
        const toolName = event.data.tool_name as string || 'tool'
        agent.showTool(toolName)
        this.statusText.setText(`Using tool: ${toolName}`)
        await this.wait(800)
        break

      case EVENT_TYPES.TOOL_END:
        agent.hideTool()
        this.statusText.setText('Tool complete')
        await this.wait(300)
        break

      case EVENT_TYPES.AGENT_IDLE:
        agent.setIdle()
        // Restore all agents to normal
        this.agents.forEach(a => {
          a.alpha = 1
          a.setScale(1)
        })
        await this.wait(200)
        break

      case EVENT_TYPES.SIMULATION_END:
        this.statusText.setText('Simulation complete!')
        this.statusText.setColor('#4a9a4a')
        this.agents.forEach(a => {
          a.setIdle()
          a.alpha = 1
        })
        break

      default:
        console.log('Unknown event type:', event.type)
    }
  }

  private wait(ms: number): Promise<void> {
    return new Promise(resolve => {
      this.time.delayedCall(ms, resolve)
    })
  }

  update() {
    // Animation updates happen via tweens
  }
}
