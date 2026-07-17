/* eslint-disable */
// Análisis de contexto de gestión (checklist opcional del reporte).
// El usuario responde preguntas concretas sobre la gestión de la obra (madurez del
// ejecutivo, permisos, terreno, contrato, cliente…) y el backend calcula un índice
// con una fórmula ancla determinística (/api/contexto/calcular). Esta lectura
// CONVIVE con la predicción del modelo: no la modifica, la complementa — el modelo
// mira las dimensiones de diseño; esto mira la gestión, que el modelo no ve.
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

function CtxResultado({ resultado }) {
  return (
    <div style={{ marginTop: 18 }}>
      <div className="divider" style={{ margin: '0 0 16px' }}/>
      <h3 style={{ marginBottom: 2 }}>Según el análisis de contexto</h3>
      <div className="desc" style={{ marginBottom: 12 }}>
        Lectura basada en el <strong>contexto de gestión</strong> de la obra (madurez del proyecto,
        permisos, equipo del cliente…), que las dimensiones de diseño no capturan.
      </div>

      <span className={'badge dot ' + CTX_BANDA_CLASS[resultado.banda]} style={{ fontSize: 13, padding: '6px 14px' }}>
        Riesgo de gestión {resultado.banda.toLowerCase()}
      </span>
      <div className="dim mono" style={{ fontSize: 12, marginTop: 6 }}>
        Índice {resultado.indice} = riesgo base {resultado.riesgo_base} × factor del equipo {resultado.factor_amplificador}
      </div>

      <div style={{ fontWeight: 600, fontSize: 13, margin: '14px 0 4px' }}>¿De dónde viene?</div>
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

      <div style={{ marginTop: 12, padding: '10px 14px', borderRadius: 10, background: 'var(--blue-soft)', border: '1px solid var(--blue-line)', fontSize: 12.5, color: 'var(--ink-2)', lineHeight: 1.5 }}>
        🧭 <strong>Cómo leer las dos juntas:</strong> el modelo mira las <em>dimensiones</em> de la obra;
        este análisis mira su <em>gestión</em>. Que una dé más alta que la otra no es contradicción:
        son dos ángulos del mismo riesgo. Léelas en conjunto.
      </div>
    </div>
  );
}

function ContextoGestion({ project }) {
  const [abierto, setAbierto] = React.useState(false);
  const [config, setConfig] = React.useState(null);      // { tipos, sugerencia }
  const [checklist, setChecklist] = React.useState({});
  const [resultado, setResultado] = React.useState(null);
  const [error, setError] = React.useState(null);
  const [cargando, setCargando] = React.useState(false);

  // Carga la configuración (preguntas + sugerencia) al abrir por primera vez.
  React.useEffect(() => {
    if (!abierto || config) return;
    API.contextoConfig(project)
      .then(data => {
        setConfig(data);
        const inicial = {};
        data.tipos.forEach(t => {
          inicial[t.clave] = data.sugerencia[t.clave] || t.opciones[0].id;
        });
        setChecklist(inicial);
      })
      .catch(e => setError('No se pudo cargar el formulario: ' + e.message));
  }, [abierto]);

  const elegir = (clave, opcionId) => {
    setChecklist(prev => ({ ...prev, [clave]: opcionId }));
    setResultado(null);  // una respuesta nueva invalida el resultado anterior
  };

  const calcular = async () => {
    setCargando(true); setError(null);
    try {
      const data = await API.contextoCalcular(checklist);
      setResultado(data.contexto);
    } catch (e) {
      setError('No se pudo calcular: ' + e.message);
    } finally {
      setCargando(false);
    }
  };

  const haySugerencia = config && Object.keys(config.sugerencia).length > 0;

  return (
    <div className="card full">
      <div className="card-head" style={{ cursor: 'pointer' }} onClick={() => setAbierto(a => !a)}>
        <div>
          <h3>Análisis de contexto de gestión <span className="accent">·</span> opcional</h3>
          <div className="desc" style={{ marginTop: 2 }}>
            Complementa la predicción con lo que el modelo no ve: permisos, terreno, contrato, cliente
          </div>
        </div>
        <span className="dim mono" style={{ fontSize: 12 }}>{abierto ? '▾ ocultar' : '▸ analizar'}</span>
      </div>

      {abierto && (
        <div className="card-pad">
          <div className="dim" style={{ fontSize: 13, lineHeight: 1.5, marginBottom: 6 }}>
            Responde estas preguntas sobre el <strong>contexto de gestión</strong> de la obra. Este
            análisis es <strong>opcional</strong> y <strong>convive</strong> con la predicción del
            modelo: no la modifica, la complementa.
          </div>
          {haySugerencia && (
            <div className="dim" style={{ fontSize: 12, marginBottom: 10 }}>
              💡 Algunas respuestas vienen pre-seleccionadas a partir de los datos que ya cargaste.
              Revísalas y ajusta lo que haga falta.
            </div>
          )}

          {!config && !error && <div className="dim" style={{ fontSize: 13 }}>Cargando formulario…</div>}

          {config && (
            <div className="col" style={{ gap: 12 }}>
              {config.tipos.map(t => (
                <CtxPregunta key={t.clave} tipo={t} elegido={checklist[t.clave]} onElegir={elegir}/>
              ))}
              <button className="btn btn-primary" onClick={calcular} disabled={cargando}>
                {cargando ? 'Calculando…' : 'Calcular riesgo de gestión'}
              </button>
            </div>
          )}

          {error && <div style={{ color: 'var(--red)', fontSize: 13, marginTop: 10 }}>{error}</div>}
          {resultado && <CtxResultado resultado={resultado}/>}
        </div>
      )}
    </div>
  );
}

window.ContextoGestion = ContextoGestion;
