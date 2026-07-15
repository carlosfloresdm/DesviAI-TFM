# Guion de demo — DesviAI (PoC)

Presentación al mentor. Duración objetivo: **8–10 min**. Todo corre en local, un solo servidor.

## 0. Antes de empezar

```powershell
cd C:\Users\carlo\DESVIAI_TFM\backend
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8200
```

Abrir en el navegador: **http://127.0.0.1:8200/**
(Si es una máquina nueva: `python core/ml/train.py` y `python core/ml/gen_memoria.py` una vez antes.)

## 1. El pitch (30 s)

> "El modelo predictivo ya estaba cerrado: Random Forest + SHAP sobre 200 obras, que estima
> el desvío de costo y de plazo y clasifica el riesgo. Lo nuevo es la capa de **diagnóstico**:
> responde *por qué* una obra se desvía, *qué se hizo bien/mal* y *qué aprender*, con un agente
> que cita cada afirmación a una fuente. La memoria es un esquema de archivos `.md`
> (semántica / procedural / episódica), sin RAG, como conversamos."

## 2. Arquitectura (1 min) — http://127.0.0.1:8200/arquitectura.html

Mostrar el diagrama de una página. Señalar:
- Capa 1 **cerrada** (no se toca).
- Las tres memorias `.md` (el punto que pediste explorar).
- El **score de riesgo contextual** con su fórmula (el mecanismo que faltaba definir).
- La decisión **binaria y auditable** del agente (evidencia directa vs. estadística).

## 3. Predicción de un proyecto nuevo (2–3 min) — pantalla principal

1. **Dashboard**: cartera real de 200 obras, distribución de riesgo, salud del modelo (R² 0.48, AUC 0.87).
2. Clic en **"Nueva predicción"** → formulario con los **10 campos reales** del modelo.
3. Clic en **"Analizar con el modelo"** → animación del pipeline → **"Ver resultados"**.
4. En el **reporte**, señalar (todo es salida real del modelo):
   - **Score de riesgo contextual** con su **desglose** (modelo + vecinos + episódica) y el badge "evidencia estadística".
   - Desvío de **costo** y de **plazo**, cada uno con banda, probabilidad e **IC80%**.
   - **SHAP**: los factores que suben/bajan el desvío.
   - **Casos similares** reales.
5. Abrir el **chat** (botón "Abrir agente conversacional"):
   - Preguntar *"¿Cómo mitigo el riesgo de cambio de alcance?"* → recupera la guía procedural, cita la fuente.
   - Señalar la **traza de herramientas** bajo la respuesta (`consultar_shap → leer_memoria`).

## 4. El diferencial: evidencia directa (2 min)

1. Volver al **Historial** (sidebar) → filtrar o buscar una obra con **"● episodio"**.
2. Clic en esa obra → su **reporte real**, ahora con la tarjeta **"Episodio documentado · evidencia directa"** (causa dominante, categorías, desvío real).
3. En el chat, preguntar *"¿Por qué se desvió esta obra?"*:
   - El agente responde con la **causa de ejecución** citando las **órdenes de cambio** (evidencia DIRECTA), distinta de la causa estructural (SHAP).
   - Contrastar con el proyecto nuevo del paso 3, donde el mismo agente declaró **evidencia estadística**. *Esa es la única decisión autónoma del agente, y es auditable.*

## 5. Evaluación con métricas (1 min)

```powershell
.\.venv\Scripts\python.exe eval\run_eval.py
```

Mostrar `backend/eval/resultados.md`:
- **5 casos canónicos**, **21/21 checks** en modo mock.
- Métricas: precisión de tools, exactitud factual, cobertura de citación, ruta de evidencia, recuperación.
- Recalcar: la verdad de referencia se **deriva de los datos** (no está fijada a mano), y el
  mismo harness evaluará al agente **Claude** cuando activemos la API key.

## 6. Cierre (30 s)

> "El PoC ya integra las tres memorias, el score contextual definido y la evaluación del agente.
> Está deliberadamente **simple y auditable**: una sola decisión autónoma, cada afirmación
> trazable a su fuente. El siguiente paso es activar el agente con Claude y ampliar la memoria
> episódica; el harness de evaluación ya está listo para medir esa versión."

---

## Preguntas probables y respuestas

- **¿Por qué no RAG?** El corpus es pequeño y manejable; los `.md` relacionados (OKF) son más
  simples, más trazables y suficientes. Migrar a vectores queda como trabajo futuro si el corpus crece.
- **¿Las órdenes de cambio son reales?** No: es un **estudio piloto reconstruido** para el ~20%
  del histórico, con la suma cuadrando con la brecha real. Declarado como limitación, no oculto.
- **¿Cómo se calcula el score?** Fórmula determinística (0.5 modelo + 0.3 vecinos + 0.2 episódica);
  el LLM la narra, no la calcula. Cada componente se ve en el reporte.
- **¿El agente inventa?** No: responde solo con lo que devuelven las tools y cita la fuente; en
  modo mock es determinístico. La evaluación mide exactamente eso.
