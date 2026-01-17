Esta es una planificación técnica detallada diseñada para ser **modular y escalable**. La clave para que esto funcione a largo plazo es desacoplar la **lógica de ejecución** (LangGraph) de la **lógica de visualización** (Frontend), utilizando un patrón basado en eventos.

### Stack Tecnológico Recomendado

*   **Backend:** Python 3.11+, FastAPI (para WebSockets de alto rendimiento), LangGraph, LangChain.
*   **Frontend:** React (para la UI de controles y chat) + **Phaser 3** (Motor de juegos 2D JS robusto y optimizado).
*   **Protocolo:** WebSockets (comunicación bidireccional en tiempo real).

---

### Arquitectura General: "The Puppeteer Pattern"

Para asegurar la escalabilidad, el Backend actúa como el "Titiritero" y el Frontend es el "Teatro". El Backend no dice "mueve el pixel x a y", sino que envía **Comandos Semánticos** (ej: `AGENT_SPEAK`, `AGENT_THINK`, `TOOL_START`).

---

### FASE 1: Diseño del Protocolo (El Contrato)

Antes de programar, definimos el esquema de mensajes. Esto permite agregar nuevos tipos de agentes o acciones sin romper el código.

**Estructura del Evento JSON (WebSocket):**
```json
{
  "event_id": "uuid",
  "timestamp": "ISO8601",
  "type": "AGENT_ACTION", // o SYSTEM_STATUS, ERROR, etc.
  "data": {
    "source_agent_id": "agent_researcher",
    "target_agent_id": "agent_writer", // Opcional, si es mensaje directo
    "action": "SPEAK", // SPEAK, THINK, TOOL_USE, HANDOFF
    "content": "He encontrado la información...",
    "metadata": { "tool_name": "google_search" } // Opcional
  }
}
```

---

### FASE 2: Planificación Backend (Python + LangGraph)

El objetivo es que el Backend sea agnóstico de la interfaz. Si mañana quieres cambiar el frontend 8-bit por uno 3D, el backend no cambia.

#### 1. Custom Callbacks (El Espía)
LangGraph/LangChain emite eventos internos. Necesitamos un interceptor.
*   **Tarea:** Crear una clase `GameVisualizerCallbackHandler` que herede de `BaseCallbackHandler`.
*   **Escalabilidad:** En lugar de hardcodear `print`, este handler inyectará los eventos en una cola asíncrona (`asyncio.Queue`).
*   **Eventos a capturar:** `on_chat_model_start`, `on_tool_start`, `on_chain_end`, `on_agent_finish`.

#### 2. Gestor de Sesiones (Session Manager)
Para que sea escalable a múltiples usuarios simultáneos.
*   **Tarea:** Crear una clase que mapee `websocket_id` -> `graph_instance`.
*   **Persistencia:** Usar `LangGraph Checkpointers` (SQLite para empezar, Postgres para producción) para poder pausar el juego y resumirlo.

#### 3. API Websocket (FastAPI)
*   **Endpoint:** `/ws/simulation/{simulation_id}`.
*   **Lógica:**
    1.  Acepta conexión.
    2.  Instancia el grafo.
    3.  Inicia un loop que consume la `asyncio.Queue` del Callback y envía JSONs por el socket.

---

### FASE 3: Planificación Frontend (React + Phaser)

Aquí es donde ocurre la magia. Usaremos React para la estructura de la página y Phaser para el canvas del juego.

#### 1. El Motor del Juego (Phaser Scene)
*   **Clase `MainScene`:** Maneja el fondo, la carga de assets y la física básica.
*   **Sistema de Sprites Escalable:** Crear una clase `AgentSprite` que extienda de `Phaser.GameObjects.Sprite`.
    *   Propiedades: `role` (determina el skin), `state` (idle, walking, talking).
    *   Métodos: `say(text)`, `walkTo(x, y)`, `showIcon(iconType)`.

#### 2. La Cola de Acciones (The Action Queue) - **CRÍTICO**
Este es el desafío técnico más importante para la UX.
*   **Problema:** El Backend envía 5 mensajes en 1 segundo. La animación de hablar dura 3 segundos.
*   **Solución:** Implementar un patrón **Producer-Consumer** en el frontend.
    1.  El WebSocket recibe el evento y lo empuja a una `eventQueue` (Array).
    2.  El "Director" (una función en el `update loop` de Phaser) mira si la animación actual terminó.
    3.  Si terminó (`isAnimating == false`), saca el siguiente evento de la cola y ejecuta la animación correspondiente.

#### 3. Sistema de Layout Dinámico
Para que sea escalable visualmente (de 2 a 10 agentes).
*   **Algoritmo:** Implementar un posicionamiento circular o de grid.
*   Si llegan `n` agentes, calcular posiciones `(x, y)` dividiendo el círculo en `360/n` grados. Así, si agregas más agentes, se reorganizan solos.

---

### FASE 4: Hoja de Ruta de Implementación (Roadmap)

#### Sprint 1: El MVP "Hello World"
1.  **Back:** Grafo simple de LangGraph con 1 nodo que devuelve "Hola".
2.  **Back:** Servidor FastAPI que envía ese "Hola" por WS.
3.  **Front:** Setup de Phaser. Cargar 1 sprite estático.
4.  **Front:** Al recibir el mensaje, mostrar un `TextBubble` sobre el sprite.

#### Sprint 2: Interacción Multi-Agente
1.  **Back:** Grafo cíclico (Agente A <-> Agente B).
2.  **Front:** Clase `AgentSprite`. Instanciar 2 personajes.
3.  **Front:** Lógica de `turn_based`. Iluminar al que habla, oscurecer al que escucha.

#### Sprint 3: Tools y Pensamiento (La "Explicabilidad")
1.  **Back:** Distinguir entre "Reasoning" (pensamiento interno del LLM) y "Final Answer".
2.  **Front:**
    *   Evento `THINK`: Aparece una nube de pensamiento sobre el personaje (burbuja punteada).
    *   Evento `TOOL`: El personaje "saca" un objeto (ej: sprite de una lupa para búsqueda web).

#### Sprint 4: Escalabilidad y UI
1.  **UI Overlay:** Panel lateral en React que muestra el log de texto completo (historial), para no perder detalle.
2.  **Speed Control:** Un slider en la UI para controlar la velocidad de reproducción de la `ActionQueue` (1x, 2x, Salto instantáneo).

---

### Desafíos de Escalabilidad y Soluciones Propuestas

1.  **Demasiados Agentes en Pantalla:**
    *   *Solución:* Cámara dinámica (Zoom in/out) en Phaser. Si hay muchos agentes, la cámara se aleja. Si uno habla, la cámara hace zoom suave hacia él.

2.  **Mensajes de Texto muy largos:**
    *   *Solución:* En el globo de 8-bit, mostrar solo un resumen o efecto de "máquina de escribir" (...). El texto completo se envía al panel lateral de React.

3.  **Latencia del LLM:**
    *   *Solución:* Estado de "Esperando". Mientras el backend procesa, el personaje muestra una animación de "idle" (respirando o golpeando el pie) para que el usuario sepa que no se congeló.

### Estructura de Archivos Sugerida (Monorepo)

```text
/project-root
  /backend
    /app
      /agents       # Definiciones de LangGraph
      /core         # Config de Websockets y Callbacks
      main.py       # FastAPI entry point
    requirements.txt
  /frontend
    /public
      /assets       # Sprites 8-bit (.png), Tilesets
    /src
      /components   # UI React (ChatLog, Controls)
      /game         # Lógica Phaser
        /scenes     # MainScene.js
        /sprites    # AgentSprite.js
        /managers   # QueueManager.js
      App.js
    package.json
```

Aquí tienes el código completo y comentado para el **`GameVisualizerCallbackHandler`**.

Este código está diseñado para ser el **puente** entre la ejecución lógica (LangChain/LangGraph) y tu interfaz visual. Captura los eventos clave y los transforma en "Instrucciones de Juego" estandarizadas.

### `game_callbacks.py`

```python
import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult, ChatGeneration

# Definimos los Tipos de Eventos que el Frontend (Phaser) entenderá
class GameEventType:
    AGENT_THINK_START = "AGENT_THINK_START"   # Aparece burbuja de pensamiento (...)
    AGENT_SPEAK = "AGENT_SPEAK"               # Aparece burbuja de diálogo con texto
    TOOL_START = "TOOL_START"                 # Agente saca un objeto/icono
    TOOL_END = "TOOL_END"                     # Agente guarda el objeto
    AGENT_IDLE = "AGENT_IDLE"                 # Agente vuelve a estado de reposo
    ERROR = "ERROR"

class GameVisualizerCallbackHandler(BaseCallbackHandler):
    """
    Captura eventos de LangGraph/LangChain y los envía a una cola asíncrona
    para ser consumidos por un WebSocket.
    """

    def __init__(self, event_queue: asyncio.Queue):
        super().__init__()
        self.queue = event_queue
        # Rastreamos qué agente está activo actualmente basándonos en metadatos
        self.current_active_agent = "System"

    async def _emit_game_event(self, event_type: str, agent_name: str, payload: Dict[str, Any] = None):
        """Helper para estructurar y encolar el mensaje JSON estándar."""
        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "type": event_type,
            "agent_id": agent_name, # El ID que usará Phaser para buscar el Sprite
            "data": payload or {}
        }
        # Ponemos el evento en la cola (sin bloquear la ejecución del LLM)
        await self.queue.put(event)

    # --- 1. Cuando el LLM empieza a "Pensar" ---
    async def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[Any]],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Se dispara cuando el modelo recibe el prompt y empieza a procesar.
        Visualmente: Nube de pensamiento '...' sobre el personaje.
        """
        # Intentamos obtener el nombre del agente de los metadatos o tags
        agent_name = metadata.get("agent_name") or "Unknown_Agent"
        self.current_active_agent = agent_name

        await self._emit_game_event(
            GameEventType.AGENT_THINK_START,
            agent_name,
            {"status": "processing"}
        )

    # --- 2. Cuando el LLM termina de generar respuesta ---
    async def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Se dispara cuando el modelo tiene la respuesta lista.
        Visualmente: Globo de texto con la respuesta.
        """
        # Extraer el texto generado. Maneja múltiples generaciones si es necesario.
        text_content = ""
        if response.generations:
            # Tomamos la primera generación (usualmente suficiente para chat)
            generation = response.generations[0][0]
            if isinstance(generation, ChatGeneration):
                text_content = generation.message.content
            else:
                text_content = generation.text

        await self._emit_game_event(
            GameEventType.AGENT_SPEAK,
            self.current_active_agent,
            {"content": text_content}
        )
       
        # Opcional: Volver a IDLE después de hablar
        await self._emit_game_event(
            GameEventType.AGENT_IDLE,
            self.current_active_agent
        )

    # --- 3. Cuando un Agente usa una Tool ---
    async def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Se dispara cuando el agente decide usar una herramienta.
        Visualmente: El personaje muestra un icono (ej: Lupa, Calculadora).
        """
        tool_name = serialized.get("name", "generic_tool")
       
        # A veces el tool no tiene el metadata del agente, usamos el último activo
        agent_name = metadata.get("agent_name") or self.current_active_agent

        await self._emit_game_event(
            GameEventType.TOOL_START,
            agent_name,
            {
                "tool_name": tool_name,
                "input_args": input_str
            }
        )

    async def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Se dispara cuando la herramienta termina su trabajo.
        Visualmente: El icono desaparece o el personaje asiente.
        """
        await self._emit_game_event(
            GameEventType.TOOL_END,
            self.current_active_agent,
            {"result_preview": output[:50] + "..."} # Solo enviamos un preview visual
        )

```

### Cómo integrarlo (Ejemplo de uso)

Para que esto funcione y sea escalable, **necesitas pasar el nombre del agente en los metadatos** cuando defines tus nodos en LangGraph.

Aquí tienes un ejemplo conceptual de cómo se usa en tu grafo:

```python
# main.py (Backend con FastAPI)
import asyncio
from fastapi import FastAPI, WebSocket
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
from game_callbacks import GameVisualizerCallbackHandler

app = FastAPI()

# --- Definición de tus Agentes ---

async def agent_node_a(state):
    # IMPORTANTE: Aquí inyectamos el nombre para que el Callback sepa quién es
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        callbacks=[] # Se inyectarán en tiempo de ejecución
    )
    # Lógica del agente...
    return {"messages": ["Hola desde Agente A"]}

# ... configuración de LangGraph ...

# --- Endpoint WebSocket ---

@app.websocket("/ws/game")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
   
    # 1. Crear la cola de eventos para esta sesión
    event_queue = asyncio.Queue()
   
    # 2. Instanciar nuestro Callback Handler
    game_handler = GameVisualizerCallbackHandler(event_queue)
   
    # 3. Tarea en segundo plano para leer la cola y enviar por WS
    async def sender_task():
        while True:
            event = await event_queue.get()
            await websocket.send_json(event)
            event_queue.task_done()
           
    asyncio.create_task(sender_task())

    try:
        while True:
            # Esperar input del usuario (si aplica)
            data = await websocket.receive_text()
           
            # 4. EJECUTAR LANGGRAPH
            # Al invocar el grafo, pasamos el callback en la configuración
            # Nota: Esto depende de cómo tengas configurado tu grafo,
            # pero la clave es pasar 'callbacks': [game_handler]
           
            # Simulación de ejecución de un nodo con metadata
            config = {
                "callbacks": [game_handler],
                "metadata": {"agent_name": "Wizard_8Bit"}
            }
           
            # Aquí llamarías a tu grafo real:
            # await graph.ainvoke(inputs, config=config)
           
            # (Simulación para testear sin LangGraph montado)
            llm = ChatOpenAI(temperature=0)
            await llm.ainvoke("Di hola brevemente", config=config)
           
    except Exception as e:
        print(f"Error: {e}")
```

### Puntos Clave para la Escalabilidad

1.  **Async Queue (`asyncio.Queue`):** Fíjate que el `GameVisualizerCallbackHandler` no envía datos por el WebSocket directamente. Solo los mete en una cola. Esto es vital. Si el WebSocket se pone lento, no frena el razonamiento del modelo de IA.
2.  **Metadata (`agent_name`):** El código depende de `metadata.get("agent_name")`. Cuando definas tus nodos en LangGraph, asegúrate de pasar esta info. Es lo que permite mapear "Nodo Python" -> "Sprite Frontend".
3.  **Filtrado de Datos:** En `on_tool_end`, cortamos el output (`output[:50]`). No envíes megabytes de JSON al frontend visual si solo necesitas mostrar que "la búsqueda terminó". Mantén el payload ligero.

Para este tipo de proyecto (una herramienta visual altamente acoplada donde el frontend debe reaccionar exactamente a lo que envía el backend), te recomiendo encarecidamente un **Monorepo**.

### ¿Por qué Monorepo?
1.  **Sincronización del Protocolo:** Si cambias el nombre de un evento en el Backend (ej: de `AGENT_SPEAK` a `AGENT_TALK`), puedes actualizar el Frontend en el mismo *commit*, evitando que se rompa la aplicación por versiones desalineadas.
2.  **Facilidad de Desarrollo:** Con un solo `docker-compose up`, levantas todo el entorno (juego + IA).
3.  **Despliegue:** Puedes desplegar ambos en un solo servicio (como Render o DigitalOcean App Platform) o configurar un pipeline de CI/CD que detecte cambios en carpetas específicas.

Aquí tienes la estructura ideal para que sea **escalable** y **profesional**:

---

### Estructura de Directorios

```text
langgraph-8bit-visualizer/   (Raíz del repositorio)
├── .github/                 # Workflows de CI/CD (Actions)
├── docs/                    # Documentación del protocolo WebSocket (Importante)
├── docker-compose.yml       # Orquestación local (Back + Front + DB)
├── Makefile                 # Comandos rápidos (ej: make run, make test)
├── README.md
│
├── backend/                 # SERVIDOR (Python + FastAPI + LangGraph)
│   ├── app/
│   │   ├── api/             # Endpoints (HTTP y WebSockets)
│   │   │   └── routers/
│   │   ├── core/            # Configuraciones (Env vars, Logging, Security)
│   │   ├── engine/          # Lógica pura de LangGraph
│   │   │   ├── agents/      # Definiciones de los agentes (Prompts, Modelos)
│   │   │   ├── tools/       # Herramientas personalizadas
│   │   │   ├── graph.py     # Construcción del grafo de estados
│   │   │   └── callbacks.py # El GameVisualizerCallbackHandler (Tu puente)
│   │   ├── schemas/         # Modelos Pydantic (Protocolo de eventos)
│   │   └── main.py          # Entry point de FastAPI
│   ├── tests/               # Pytest (Unitarios y de Integración)
│   ├── requirements.txt
│   └── Dockerfile
│
└── frontend/                # CLIENTE (React + Phaser)
    ├── public/
    │   └── assets/          # Archivos estáticos
    │       ├── sprites/     # Personajes 8-bit (.png, .json)
    │       ├── tilesets/    # Mapas de fondo
    │       └── sounds/      # Efectos de sonido (opcional)
    ├── src/
    │   ├── api/             # Cliente WebSocket y manejo de conexión
    │   ├── components/      # UI React (Overlays, Chat logs, Botones)
    │   │   ├── HUD/         # Heads-Up Display
    │   │   └── Terminal/    # Consola de depuración visual
    │   ├── game/            # Lógica de Phaser (Separada de React)
    │   │   ├── scenes/      # Escenas (MainScene, LoadingScene)
    │   │   ├── entities/    # Clases (AgentSprite, Item)
    │   │   └── systems/     # Sistemas (ActionQueueManager, LayoutSystem)
    │   ├── hooks/           # Hooks para comunicar React <-> Phaser
    │   └── App.tsx
    ├── package.json
    ├── vite.config.ts
    └── Dockerfile
```

---

### Análisis de las Carpetas Clave

#### 1. `backend/app/engine/`
Aquí vive la lógica de LangGraph separada de la API.
*   **Escalabilidad:** Si mañana quieres cambiar FastAPI por Django, o correr el grafo como un script de CLI, esta carpeta no se toca.
*   **`callbacks.py`:** Aquí va el código que te generé antes. Es la pieza fundamental que "espía" lo que ocurre en `graph.py`.

#### 2. `frontend/src/game/` (Phaser) vs `frontend/src/components/` (React)
Esta separación es vital.
*   **React** maneja el DOM (HTML): menús, logs de texto, configuraciones, login.
*   **Phaser** maneja el Canvas (WebGL): sprites moviéndose, animaciones.
*   **Comunicación:** No mezcles lógica. Usa un patrón de "Event Bus" o Custom Hooks en React que llamen a métodos de la instancia del juego de Phaser.

#### 3. `frontend/public/assets/sprites/`
Para mantener el estilo 8-bit organizado.
*   Usa **Texture Atlases** (un archivo PNG grande con todos los movimientos de un personaje y un archivo JSON que dice dónde está cada frame). Esto mejora muchísimo el rendimiento del navegador en lugar de cargar 50 imágenes sueltas.

#### 4. `backend/app/schemas/`
Aquí defines tus modelos Pydantic.
*   *Tip Pro:* Define la estructura de los eventos del WebSocket aquí. Así aseguras que el backend siempre envíe datos que cumplan el contrato.

### Flujo de Trabajo (Developer Experience)

Con esta estructura, tu flujo de trabajo diario sería:

1.  **Arranque:**
    ```bash
    docker-compose up --build
    ```
    Esto levanta:
    *   Backend en `localhost:8000` (con Hot Reload).
    *   Frontend en `localhost:3000` (con Vite HMR).
    *   Redis/Postgres (si necesitas persistencia para LangGraph).

2.  **Modificar un Agente:**
    *   Editas `backend/app/engine/agents/researcher.py`.
    *   Guardas.
    *   LangGraph se recarga.
    *   Vas al navegador, reinicias la simulación y ves el cambio.

3.  **Agregar un nuevo Sprite:**
    *   Pones el PNG en `frontend/public/assets/sprites/`.
    *   Creas la clase en `frontend/src/game/entities/NewAgent.ts`.
    *   Mapeas el nombre del agente del backend al nombre del sprite en el frontend.

### Consideración sobre Git

Asegúrate de tener un `.gitignore` robusto en la raíz que ignore:
*   `__pycache__`
*   `node_modules`
*   `.env` (¡Muy importante, ahí van las API Keys de OpenAI!)
*   `.DS_Store`

Esta estructura te da la **rigidez** necesaria para que el proyecto no se desordene cuando crezca, pero la **flexibilidad** de tener todo a mano en un solo repositorio.