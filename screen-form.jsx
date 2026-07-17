/* eslint-disable */
// Formulario conectado al modelo real. Los 10 campos coinciden EXACTO con el
// contrato de entrada del backend (RandomForest + SHAP).
function ScreenForm({ go, runAnalysis }) {
  const [nombre, setNombre]   = React.useState('Proyecto nuevo');   // cosmético, no se envía
  const [supM2, setSupM2]     = React.useState('45000');
  const [niveles, setNiveles] = React.useState('35');
  const [unidades, setUnidades] = React.useState('400');
  const [presupuesto, setPresupuesto] = React.useState('30000000');
  const [tiempo, setTiempo]   = React.useState('730');
  const [sistema, setSistema] = React.useState('Concreto Postensado');
  const [acabado, setAcabado] = React.useState('Medio');
  const [avance, setAvance]   = React.useState('70 - 80');
  const [similares, setSimilares] = React.useState('10 - 15');
  const [fecha, setFecha]     = React.useState('2024-03');

  // Contexto de gestión (checklist opcional — contexto-gestion.jsx).
  const [ctxIncluir, setCtxIncluir] = React.useState(false);
  const [ctxChecklist, setCtxChecklist] = React.useState({});

  const num = (s) => Number(String(s).replace(/[, $]/g, '')) || 0;

  // Costo por m² derivado (sólo informativo; no es input del modelo).
  const costoM2 = (() => {
    const p = num(presupuesto), a = num(supM2);
    return a > 0 ? Math.round(p / a).toLocaleString('en-US') : '—';
  })();

  const submit = () => {
    const project = {
      sup_m2: num(supM2),
      niveles: num(niveles),
      unidades: num(unidades),
      presupuesto_inicial: num(presupuesto),
      tiempo_inicial: num(tiempo),
      sistema_constructivo: sistema,
      nivel_acabado: acabado,
      avance_proyecto: avance,
      proyectos_similares: similares,
      fecha_inicio: fecha,
    };
    runAnalysis(project, null, ctxIncluir ? ctxChecklist : null);
    go('pipeline');
  };

  return (
    <div className="screen">
      <div className="page-head">
        <div>
          <div className="page-eyebrow">Nueva predicción · Paso 01 de 04 · Modelo RandomForest + SHAP</div>
          <h1 className="page-title">Datos del proyecto</h1>
          <div className="page-sub">Sólo variables conocidas al inicio de la obra. El modelo estima el desvío de costo y de plazo, su banda de riesgo y el score contextual.</div>
        </div>
        <button className="btn" onClick={() => go('dashboard')}>← Cancelar</button>
      </div>

      <Stepper active="entrada"/>

      <div className="card">
        <div className="card-head">
          <div>
            <h3>Parámetros de obra</h3>
            <div className="desc" style={{ marginTop: 2 }}>10 variables del modelo · vivienda vertical · valores en USD</div>
          </div>
          <span className="mono dim" style={{ fontSize: 11.5 }}>costo/m² estimado: USD ${costoM2}</span>
        </div>
        <div className="card-pad-lg">
          <div className="form-grid">
            <div className="field">
              <label>Nombre del proyecto <span className="help">sólo referencia</span></label>
              <div className="input">
                <input value={nombre} onChange={e => setNombre(e.target.value)} />
              </div>
            </div>

            <div className="field">
              <label><span className="req">*</span> Superficie total</label>
              <div className="input">
                <input value={supM2} onChange={e => setSupM2(e.target.value)} />
                <span className="suffix">m²</span>
              </div>
            </div>

            <div className="field">
              <label><span className="req">*</span> Número de niveles</label>
              <div className="input">
                <input value={niveles} onChange={e => setNiveles(e.target.value)} />
                <span className="suffix">pisos</span>
              </div>
            </div>

            <div className="field">
              <label><span className="req">*</span> Número de unidades</label>
              <div className="input">
                <input value={unidades} onChange={e => setUnidades(e.target.value)} />
                <span className="suffix">und</span>
              </div>
            </div>

            <div className="field">
              <label><span className="req">*</span> Sistema constructivo</label>
              <div className="input select-input">
                <select value={sistema} onChange={e => setSistema(e.target.value)}>
                  {MODEL_OPTS.sistema_constructivo.map(o => <option key={o}>{o}</option>)}
                </select>
                <span className="chev">▾</span>
              </div>
            </div>

            <div className="field">
              <label><span className="req">*</span> Nivel de acabados</label>
              <div className="input select-input">
                <select value={acabado} onChange={e => setAcabado(e.target.value)}>
                  {MODEL_OPTS.nivel_acabado.map(o => <option key={o}>{o}</option>)}
                </select>
                <span className="chev">▾</span>
              </div>
            </div>

            <div className="field">
              <label><span className="req">*</span> Presupuesto inicial</label>
              <div className="input">
                <span className="prefix">USD $</span>
                <input value={presupuesto} onChange={e => setPresupuesto(e.target.value)} />
              </div>
            </div>

            <div className="field">
              <label><span className="req">*</span> Plazo inicial</label>
              <div className="input">
                <input value={tiempo} onChange={e => setTiempo(e.target.value)} />
                <span className="suffix">días</span>
              </div>
            </div>

            <div className="field">
              <label><span className="req">*</span> Fecha de inicio</label>
              <div className="input">
                <input type="month" value={fecha} onChange={e => setFecha(e.target.value)} />
              </div>
            </div>

            <div className="field">
              <label>
                <span className="req">*</span> Avance del proyecto
                <span className="help">% físico al analizar</span>
              </label>
              <div className="input select-input">
                <select value={avance} onChange={e => setAvance(e.target.value)}>
                  {MODEL_OPTS.avance_proyecto.map(o => <option key={o}>{o}</option>)}
                </select>
                <span className="chev">▾</span>
              </div>
            </div>

            <div className="field">
              <label>
                <span className="req">*</span> Proyectos similares del equipo
                <span className="help">≥15 ⇒ experiencia alta</span>
              </label>
              <div className="input select-input">
                <select value={similares} onChange={e => setSimilares(e.target.value)}>
                  {MODEL_OPTS.proyectos_similares.map(o => <option key={o}>{o}</option>)}
                </select>
                <span className="chev">▾</span>
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* Checklist de contexto de gestión, junto con los datos del proyecto */}
      <ContextoGestionForm avance={avance} incluir={ctxIncluir} setIncluir={setCtxIncluir}
        checklist={ctxChecklist} setChecklist={setCtxChecklist}/>

      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-pad">
          <div className="row">
            <div className="dim" style={{ fontSize: 12.5 }}>
              <span className="mono" style={{ color: 'var(--green)', fontWeight: 700 }}>10/10</span> campos
              {ctxIncluir ? ' · con contexto de gestión' : ''} · listo para analizar con el modelo real
            </div>
            <div className="spacer"/>
            <button className="btn" onClick={() => go('dashboard')}>Cancelar</button>
            <button className="btn btn-primary" onClick={submit}>
              Analizar con el modelo {I.arrowRight()}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

window.ScreenForm = ScreenForm;
