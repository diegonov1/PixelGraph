import { useEffect, useRef, useState } from 'react'
import Phaser from 'phaser'
import { MainScene } from './game/scenes/MainScene'
import { GameEventBus } from './game/systems/EventBus'
import { HUD } from './components/HUD/HUD'
import { Terminal } from './components/Terminal/Terminal'
import './App.css'

interface GameEvent {
  event_id: string
  timestamp: string
  type: string
  agent_id: string
  data: Record<string, unknown>
}

function App() {
  const gameRef = useRef<Phaser.Game | null>(null)
  const [logs, setLogs] = useState<GameEvent[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    // Initialize Phaser game
    const config: Phaser.Types.Core.GameConfig = {
      type: Phaser.AUTO,
      parent: 'game-container',
      width: 800,
      height: 500,
      pixelArt: true,
      backgroundColor: '#2d2d44',
      scene: [MainScene],
      scale: {
        mode: Phaser.Scale.FIT,
        autoCenter: Phaser.Scale.CENTER_BOTH,
      },
    }

    gameRef.current = new Phaser.Game(config)

    // Connect to WebSocket
    const wsUrl = import.meta.env.DEV
      ? 'ws://localhost:8000/ws/game'
      : `ws://${window.location.host}/ws/game`

    const connectWebSocket = () => {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('Connected to LangArcade server')
        setIsConnected(true)
      }

      ws.onmessage = (event) => {
        const data: GameEvent = JSON.parse(event.data)
        console.log('Received event:', data)

        setLogs(prev => [...prev, data])

        // Emit event to Phaser via event bus
        GameEventBus.emit('game-event', data)
      }

      ws.onclose = () => {
        console.log('Disconnected from server')
        setIsConnected(false)
        // Attempt to reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000)
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    }

    connectWebSocket()

    return () => {
      if (gameRef.current) {
        gameRef.current.destroy(true)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && inputValue.trim()) {
      wsRef.current.send(JSON.stringify({
        type: 'START_SIMULATION',
        input: inputValue.trim(),
      }))
      setInputValue('')
    }
  }

  return (
    <div className="app">
      <HUD isConnected={isConnected} />

      <div className="main-content">
        <div id="game-container" className="game-container" />
        <Terminal logs={logs} />
      </div>

      <form className="input-bar" onSubmit={handleSubmit}>
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder={isConnected ? "Enter your message..." : "Connecting..."}
          disabled={!isConnected}
          className="input-field"
        />
        <button
          type="submit"
          disabled={!isConnected || !inputValue.trim()}
          className="send-button"
        >
          SEND
        </button>
      </form>
    </div>
  )
}

export default App
