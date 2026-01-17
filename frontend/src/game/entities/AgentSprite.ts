/**
 * AgentSprite - Visual representation of a LangGraph agent
 *
 * Extends Phaser.GameObjects.Container to hold the sprite and speech bubble together.
 */

import Phaser from 'phaser'

export type AgentState = 'idle' | 'thinking' | 'speaking' | 'using_tool'

export class AgentSprite extends Phaser.GameObjects.Container {
  private sprite: Phaser.GameObjects.Graphics
  private bubble: Phaser.GameObjects.Container | null = null
  private bubbleText: Phaser.GameObjects.Text | null = null
  private thinkingDots: Phaser.GameObjects.Text | null = null
  private toolIcon: Phaser.GameObjects.Text | null = null
  private nameLabel: Phaser.GameObjects.Text

  public agentId: string
  public currentState: AgentState = 'idle'

  private colors = {
    body: 0x6a5acd,      // Slate blue
    outline: 0x483d8b,   // Dark slate blue
    eyes: 0xffffff,
    pupils: 0x000000,
    hat: 0x9370db,       // Medium purple (wizard hat)
  }

  constructor(
    scene: Phaser.Scene,
    x: number,
    y: number,
    agentId: string,
    displayName?: string
  ) {
    super(scene, x, y)

    this.agentId = agentId

    // Create the 8-bit character sprite using graphics
    this.sprite = this.createCharacterGraphics()
    this.add(this.sprite)

    // Create name label
    this.nameLabel = scene.add.text(0, 50, displayName || agentId, {
      fontFamily: '"Press Start 2P", cursive',
      fontSize: '8px',
      color: '#ffffff',
      stroke: '#000000',
      strokeThickness: 2,
    })
    this.nameLabel.setOrigin(0.5)
    this.add(this.nameLabel)

    scene.add.existing(this)

    // Start idle animation
    this.startIdleAnimation()
  }

  private createCharacterGraphics(): Phaser.GameObjects.Graphics {
    const graphics = this.scene.add.graphics()
    const pixelSize = 4

    // 8-bit wizard character (16x16 pixels scaled up)
    const character = [
      '    HHHH    ',
      '   HHHHHH   ',
      '  HHHHHHHH  ',
      '   BBBBBB   ',
      '  BEEWWEEB  ',
      '  BBBBBBBB  ',
      '  BB BB BB  ',
      '   BBBBBB   ',
      '    RRRR    ',
      '   RRRRRR   ',
      '  RR RR RR  ',
      '  RR RR RR  ',
      '   LL  LL   ',
      '   LL  LL   ',
    ]

    const colorMap: Record<string, number> = {
      'H': this.colors.hat,
      'B': this.colors.body,
      'E': this.colors.eyes,
      'W': this.colors.pupils,
      'R': 0x8b4513,  // Robe (brown)
      'L': 0x2f2f2f,  // Legs (dark gray)
    }

    character.forEach((row, y) => {
      row.split('').forEach((char, x) => {
        if (char !== ' ' && colorMap[char]) {
          graphics.fillStyle(colorMap[char])
          graphics.fillRect(
            (x - 6) * pixelSize,
            (y - 7) * pixelSize,
            pixelSize,
            pixelSize
          )
        }
      })
    })

    return graphics
  }

  private startIdleAnimation() {
    // Subtle breathing animation
    this.scene.tweens.add({
      targets: this.sprite,
      scaleY: { from: 1, to: 1.02 },
      duration: 1000,
      yoyo: true,
      repeat: -1,
      ease: 'Sine.easeInOut',
    })
  }

  /**
   * Show thinking state with animated dots
   */
  showThinking() {
    this.currentState = 'thinking'
    this.clearBubble()

    // Create thinking bubble
    this.bubble = this.scene.add.container(0, -60)

    const bubbleBg = this.scene.add.graphics()
    bubbleBg.fillStyle(0xffffff, 0.9)
    bubbleBg.fillRoundedRect(-30, -15, 60, 30, 8)

    // Add dots
    this.thinkingDots = this.scene.add.text(0, 0, '...', {
      fontFamily: '"Press Start 2P", cursive',
      fontSize: '12px',
      color: '#333333',
    })
    this.thinkingDots.setOrigin(0.5)

    this.bubble.add(bubbleBg)
    this.bubble.add(this.thinkingDots)
    this.add(this.bubble)

    // Animate dots
    let dotCount = 0
    this.scene.time.addEvent({
      delay: 400,
      callback: () => {
        if (this.thinkingDots && this.currentState === 'thinking') {
          dotCount = (dotCount + 1) % 4
          this.thinkingDots.setText('.'.repeat(dotCount + 1))
        }
      },
      loop: true,
    })

    // Highlight effect
    this.scene.tweens.add({
      targets: this,
      alpha: { from: 1, to: 0.8 },
      duration: 500,
      yoyo: true,
      repeat: -1,
    })
  }

  /**
   * Show speech bubble with text
   */
  say(text: string, duration: number = 3000): Promise<void> {
    return new Promise((resolve) => {
      this.currentState = 'speaking'
      this.clearBubble()

      // Stop any highlight tweens
      this.scene.tweens.killTweensOf(this)
      this.alpha = 1

      // Create speech bubble
      this.bubble = this.scene.add.container(0, -70)

      // Calculate bubble size based on text
      const maxWidth = 200
      const padding = 12
      const fontSize = 8

      // Create text first to measure
      this.bubbleText = this.scene.add.text(0, 0, text, {
        fontFamily: '"Press Start 2P", cursive',
        fontSize: `${fontSize}px`,
        color: '#333333',
        wordWrap: { width: maxWidth - padding * 2 },
        align: 'center',
      })
      this.bubbleText.setOrigin(0.5)

      const textWidth = Math.min(this.bubbleText.width + padding * 2, maxWidth)
      const textHeight = this.bubbleText.height + padding * 2

      // Draw bubble background
      const bubbleBg = this.scene.add.graphics()
      bubbleBg.fillStyle(0xffffff, 0.95)
      bubbleBg.fillRoundedRect(-textWidth / 2, -textHeight / 2, textWidth, textHeight, 8)

      // Draw speech bubble tail
      bubbleBg.fillTriangle(
        -5, textHeight / 2 - 2,
        5, textHeight / 2 - 2,
        0, textHeight / 2 + 10
      )

      // Add border
      bubbleBg.lineStyle(2, 0x333333)
      bubbleBg.strokeRoundedRect(-textWidth / 2, -textHeight / 2, textWidth, textHeight, 8)

      this.bubble.add(bubbleBg)
      this.bubble.add(this.bubbleText)
      this.add(this.bubble)

      // Typewriter effect
      const fullText = text
      let currentIndex = 0
      this.bubbleText.setText('')

      this.scene.time.addEvent({
        delay: 30,
        callback: () => {
          if (this.bubbleText && currentIndex < fullText.length) {
            currentIndex++
            this.bubbleText.setText(fullText.substring(0, currentIndex))
          }
        },
        repeat: fullText.length - 1,
      })

      // Remove bubble after duration
      this.scene.time.delayedCall(duration, () => {
        this.setIdle()
        resolve()
      })
    })
  }

  /**
   * Show tool usage icon
   */
  showTool(toolName: string) {
    this.currentState = 'using_tool'

    // Show tool icon above character
    const iconMap: Record<string, string> = {
      'search': '🔍',
      'web_search': '🌐',
      'calculator': '🧮',
      'code': '💻',
      'file': '📄',
      'default': '🔧',
    }

    const icon = iconMap[toolName.toLowerCase()] || iconMap['default']

    this.toolIcon = this.scene.add.text(25, -40, icon, {
      fontSize: '20px',
    })
    this.add(this.toolIcon)

    // Bounce animation
    this.scene.tweens.add({
      targets: this.toolIcon,
      y: { from: -40, to: -50 },
      duration: 300,
      yoyo: true,
      repeat: -1,
    })
  }

  /**
   * Hide tool icon
   */
  hideTool() {
    if (this.toolIcon) {
      this.toolIcon.destroy()
      this.toolIcon = null
    }
  }

  /**
   * Set agent to idle state
   */
  setIdle() {
    this.currentState = 'idle'
    this.clearBubble()
    this.hideTool()
    this.scene.tweens.killTweensOf(this)
    this.alpha = 1
  }

  /**
   * Clear the speech/thought bubble
   */
  private clearBubble() {
    if (this.bubble) {
      this.bubble.destroy()
      this.bubble = null
      this.bubbleText = null
      this.thinkingDots = null
    }
  }

  /**
   * Highlight this agent (when speaking or active)
   */
  highlight() {
    this.scene.tweens.add({
      targets: this,
      scaleX: 1.1,
      scaleY: 1.1,
      duration: 200,
      ease: 'Quad.easeOut',
    })
  }

  /**
   * Remove highlight
   */
  unhighlight() {
    this.scene.tweens.add({
      targets: this,
      scaleX: 1,
      scaleY: 1,
      alpha: 0.7,
      duration: 200,
      ease: 'Quad.easeOut',
    })
  }
}
