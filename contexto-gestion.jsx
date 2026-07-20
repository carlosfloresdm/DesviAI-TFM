/* eslint-disable */
// Análisis de contexto de gestión — checklist opcional de la ENTRADA DE DATOS.
// El usuario responde preguntas concretas sobre la gestión de la obra (madurez del
// ejecutivo, permisos, terreno, contrato, cliente…) junto con los datos del
// proyecto; el backend calcula un índice con una fórmula ancla determinística
// (/api/contexto/calcular) durante el análisis, y el REPORTE muestra el resultado.
// Esta lectura CONVIVE con la predicción del modelo: no la modifica, la
// complementa — el modelo mira las dimensiones de diseño; esto mira la gestión.
// Las preguntas, opciones y pesos viven en el backend (core/ml/contexto.py, única
// fuente de verdad); aquí solo se dibujan y se recoge la respuesta.

const CTX_BANDA_CLASS = { BAJO: 'low', MEDIO: 'med', ALTO: 'high' };
const CTX_PUNTO = { BAJO: 'var(--green)', MEDIO: 'var(--amber)', ALTO: 'var(--red)' };

function CtxPregunta({ tipo, elegido, onElegir }) {
  return (
    <div style={{ border: '1px solid var(--border)', borderRadius: 10, padding: '14px 16px', background: 'var(--bg-tint)' }}>
      {tipo.rol === 'amplificador' && (
        <div className="dim" style={{ fontSize: 12, marginBottom: 8 }}>
          ⚙ El siguiente factor no suma riesgo: lo <strong>multiplica</strong>. Un cliente ágil
          atenúa el riesgo del resto; uno lento y moroso lo agrava.
        </div>
      )}
      <div style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 8 }}>{tipo.pregunta}</div>
      <div className="col" style={{ gap: 6 }}>
        {tipo.opciones.map(op => (
          <label key={op.id} className="row" style={{ gap: 8, alignItems: 'flex-start', cursor: 'pointer', fontSize: 13, color: 'var(--ink-2)' }}>
            <input type="radio" name={'ctx_' + tipo.clave} checked={elegido === op.id}
              onChange={() => onElegir(tipo.clave, op.id)} style={{ accentColor: 'var(--orange)', marginTop: 2 }}/>
            <span>{op.texto}</span>
          </label>
        ))}
      </div>
    </div>
  );
}

/* ===== Sección del FORMULARIO (entrada de datos) =====
   Vive en screen-form.jsx, debajo de los parámetros de obra. Es opcional: solo
   si el usuario la activa, el checklist viaja con el análisis. La pre-selección
   sigue al campo "Avance del proyecto" mientras el usuario no la corrija. */
function ContextoGestionForm({ avance, incluir, setIncluir, checklist, setChecklist }) {
  const [config, setConfig] = React.useState(null);   // { tipos, sugerencia }
  const [error, setError] = React.useState(null);
  const tocadas = React.useRef({});                   // preguntas ya corregidas a mano

  // Carga la configuración y re-aplica la sugerencia cuando cambia el avance
  // (solo sobre preguntas que el usuario no tocó: el sistema propone, él dispone).
  React.useEffect(() => {
    let vivo = true;
    API.contextoConfig({ avance_proyecto: avance })
      .then(data => {
        if (!vivo) return;
        setConfig(data);
        setChecklist(prev => {
          const next = { ...prev };
          data.tipos.forEach(t => {
            if (!next[t.clave]) next[t.clave] = data.sugerencia[t.clave] || t.opciones[0].id;
          });
          Object.entries(data.sugerencia).forEach(([clave, opcionId]) => {
            if (!tocadas.current[clave]) next[clave] = opcionId;
          });
          return next;
        });
      })
      .catch(e => vivo && setError('No se pudo cargar el checklist: ' + e.message));
    return () => { vivo = false; };
  }, [avance]);

  const elegir = (clave, opcionId) => {
    tocadas.current[clave] = true;
    setChecklist(prev => ({ ...prev, [clave]: opcionId }));
  };

  return (
    <div className="card" style={{ marginTop: 16 }}>
      <div className="card-head" style={{ cursor: 'pointer' }} onClick={() => setIncluir(v => !v)}>
        <div>
          <h3>Contexto de gestión <span className="accent">·</span> opcional</h3>
          <div className="desc" style={{ marginTop: 2 }}>
            Complementa la predicción con lo que el modelo no ve: permisos, terreno, contrato, cliente
          </div>
        </div>
        <label className="row" style={{ gap: 8, cursor: 'pointer', fontSize: 13, fontWeight: 600 }} onClick={e => e.stopPropagation()}>
          <input type="checkbox" checked={incluir} onChange={e => setIncluir(e.target.checked)}
            style={{ accentColor: 'var(--orange)' }}/>
          Incluir en el análisis
        </label>
      </div>

      {incluir && (
        <div className="card-pad">
          <div className="dim" style={{ fontSize: 13, lineHeight: 1.5, marginBottom: 6 }}>
            Responde estas preguntas sobre el <strong>contexto de gestión</strong> de la obra. Este
            análisis <strong>convive</strong> con la predicción del modelo: no la modifica, la
            complementa. El resultado aparecerá en el reporte.
          </div>
          {config && Object.keys(config.sugerencia).length > 0 && (
            <div className="dim" style={{ fontSize: 12, marginBottom: 10 }}>
              💡 Algunas respuestas vienen pre-seleccionadas a partir de los datos del proyecto
              (p. ej. el avance). Revísalas y ajusta lo que haga falta.
            </div>
          )}

          {!config && !error && <div className="dim" style={{ fontSize: 13 }}>Cargando checklist…</div>}
          {error && <div style={{ color: 'var(--red)', fontSize: 13 }}>{error}</div>}

          {config && (
            <div className="col" style={{ gap: 12 }}>
              {config.tipos.map(t => (
                <CtxPregunta key={t.clave} tipo={t} elegido={checklist[t.clave]} onElegir={elegir}/>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ===== Tarjeta del REPORTE (solo resultado, ya calculado en el análisis) ===== */
function ContextoResultadoCard({ resultado }) {
  // Explicación con LLM (capa interpretativa): opcional, bajo demanda. Funciona en
  // modo mock (plantilla determinística) sin API key, y con Claude u OpenAI si se
  // configuró AGENT_MODE. No recalcula el índice, solo lo narra.
  const [explicacion, setExplicacion] = React.useState(null);
  const [estadoLlm, setEstadoLlm] = React.useState(null);
  const [cargando, setCargando] = React.useState(false);
  const [error, setError] = React.useState(null);

  const explicar = async () => {
    setCargando(true); setError(null);
    try {
      const data = await API.contextoExplicar(resultado);
      setExplicacion(data.explicacion);
      setEstadoLlm(data.estado_llm);
    } catch (e) {
      setError('No se pudo generar la explicación: ' + e.message);
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="card full">
      <div className="card-head">
        <div>
          <h3>Según el análisis de contexto <span className="accent">·</span> gestión</h3>
          <div className="desc" style={{ marginTop: 2 }}>
            Lectura basada en el contexto de gestión de la obra (madurez del proyecto, permisos,
            equipo del cliente…), que las dimensiones de diseño no capturan
          </div>
        </div>
        <span className={'badge dot ' + CTX_BANDA_CLASS[resultado.banda]}>
          Riesgo de gestión {resultado.banda.toLowerCase()}
        </span>
      </div>
      <div className="card-pad">
        <div className="dim mono" style={{ fontSize: 12 }}>
          Índice {resultado.indice} = riesgo base {resultado.riesgo_base} × factor del equipo {resultado.factor_amplificador}
        </div>

        <div style={{ fontWeight: 600, fontSize: 13, margin: '12px 0 4px' }}>¿De dónde viene?</div>
        {Object.entries(resultado.desglose).map(([clave, d]) => (
          <div key={clave} style={{ padding: '8px 0', borderBottom: '1px solid var(--border-soft)' }}>
            <div className="row" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 600, fontSize: 13 }}>
                {d.etiqueta}
                {d.rol === 'amplificador' && <span className="dim" style={{ fontWeight: 400, fontSize: 11.5 }}> · amplificador</span>}
              </span>
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: CTX_PUNTO[d.nivel], flex: '0 0 auto' }}/>
            </div>
            <div className="dim" style={{ fontSize: 12, marginTop: 2 }}>{d.opcion_texto}</div>
          </div>
        ))}

        {/* Explicación del riesgo con el LLM (capa interpretativa, bajo demanda) */}
        <div style={{ marginTop: 14 }}>
          {!explicacion && (
            <button className="btn btn-outline" onClick={explicar} disabled={cargando}>
              {cargando ? 'Analizando la memoria de casos…' : '💬 Explicar este riesgo y sugerir mitigaciones'}
            </button>
          )}
          {error && <div style={{ color: 'var(--red)', fontSize: 13, marginTop: 8 }}>{error}</div>}
          {explicacion && (
            <div className="narrative" style={{ marginTop: 4 }}>
              {explicacion.split('\n').filter(p => p.trim()).map((p, i) => <p key={i}>{p}</p>)}
              {estadoLlm && <p className="dim" style={{ fontSize: 11.5 }}>{estadoLlm}</p>}
            </div>
          )}
        </div>

        <div style={{ marginTop: 12, padding: '10px 14px', borderRadius: 10, background: 'var(--blue-soft)', border: '1px solid var(--blue-line)', fontSize: 12.5, color: 'var(--ink-2)', lineHeight: 1.5 }}>
          🧭 <strong>Cómo leer las dos juntas:</strong> el modelo mira las <em>dimensiones</em> de la obra;
          este análisis mira su <em>gestión</em>. Que una dé más alta que la otra no es contradicción:
          son dos ángulos del mismo riesgo. Léelas en conjunto.
        </div>
      </div>
    </div>
  );
}

window.ContextoGestionForm = ContextoGestionForm;
window.ContextoResultadoCard = ContextoResultadoCard;
