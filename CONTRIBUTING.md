# Cómo trabajamos en equipo (guía para principiantes)

Esta guía es para colaborar en DesviAI **sin haber usado GitHub antes**. Si sigues estos
pasos, es muy difícil que algo salga mal.

## 0. Instala GitHub Desktop (una sola vez)

Descárgalo de **https://desktop.github.com** e inicia sesión con tu cuenta de GitHub.
Con GitHub Desktop, todo lo de git se hace con botones — no hace falta escribir comandos.

> El terminal solo lo necesitas para **correr** la app (ver el `README.md`). Para **git**,
> usa GitHub Desktop.

Luego, en GitHub Desktop: **File → Clone repository → DesviAI-TFM**.

## 1. El ciclo diario (memoriza estos 4 pasos)

Cada vez que te sientas a trabajar:

1. **Pull / Fetch origin** — trae lo que subieron los demás. **SIEMPRE primero.**
2. **Trabaja** en tu parte.
3. **Commit** — guarda tu cambio con un mensaje claro (abajo a la izquierda en Desktop).
4. **Push origin** — sube tu cambio para que los demás lo tengan.

Regla de oro: **Pull antes de empezar, Push cuando terminas una tanda.**

## 2. Trabaja siempre en tu propia rama (no en `main`)

`main` es la versión buena; no trabajamos directo sobre ella.

1. En GitHub Desktop: **Current Branch → New Branch**.
2. Nómbrala según tu tarea: `formulario-nuevo`, `arreglo-agente`, `memoria-episodica`…
3. Trabaja, haz Commit y Push **en esa rama**.
4. Cuando termines: botón **Create Pull Request** (abre la web).
5. Otra persona lo revisa y le da **Merge**. Así `main` siempre funciona.

## 3. Reglas de oro (evitan el 95% de los problemas)

- **Repartan el trabajo por archivos/áreas.** Que dos personas no editen el mismo archivo a
  la vez. (Ej: uno `core/ml/`, otro `core/agent/`, otro los `*.jsx`, otro `knowledge/`.)
- **Pull antes de empezar** y **antes de subir**.
- **Cada uno en su rama.** Nunca subas directo a `main`.
- **Commits pequeños y frecuentes**, con mensaje claro ("arreglo el formulario", no "cambios").
- **Avisa por el chat** qué estás tocando: *"estoy en el reporte esta tarde"*.

## 4. Qué NO se sube (ya está configurado)

El `.gitignore` deja fuera, a propósito:
- `backend/.venv/` (el entorno virtual, ~500 MB)
- `backend/core/ml/artifacts/` (los `.pkl` del modelo — cada uno los regenera con `train.py`)
- `db.sqlite3` y cualquier `.env` (secretos)

Por eso, tras clonar, el primer paso es `python core/ml/train.py` (ver `README.md`).
Esto también evita conflictos: nadie pelea por archivos binarios.

## 5. Si algo se rompe o aparece un "conflicto"

**No fuerces nada.** Un conflicto pasa cuando dos personas cambiaron lo mismo; es normal y se
arregla. Saca una captura, avisa en el chat del grupo y resuélvanlo juntos con calma. Casi
nada en git es irreversible.

## Resumen en una línea

> Instala GitHub Desktop · Pull antes de empezar · trabaja en tu rama · Commit + Push · Pull
> Request · repártanse los archivos · avisen por el chat.
