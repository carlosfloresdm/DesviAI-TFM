/* eslint-disable */
function ScreenPipeline({ go, status, error }) {
  const [step, setStep] = React.useState(0);
  const [done, setDone] = React.useState(false);
  const bodyRef = React.useRef(null);

  // El análisis está listo cuando la animación terminó Y la API respondió.
  const ready = done && status === 'done';
  const failed = status === 'error';

  const lines = [
    { ts: '14:32:18', kind: 'sys',  text: 'Inicio del pipeline · payload validado (10/10 campos OK)' },
    { ts: '14:32:19', kind: 'agent', text: 'Agente: Ingesta', detail: 'ingeniería de variables → vector(14)' },
    { ts: '14:32:20', kind: 'tool', name: 'normalizar_inputs', out: 'OK · 14 features del modelo' },
    { ts: '14:32:21', kind: 'agent', text: 'Agente: Validador', detail: 'rangos y consistencia' },
    { ts: '14:32:22', kind: 'tool', name: 'validar_rangos', out: 'OK · sin outliers' },
    { ts: '14:32:23', kind: 'tool', name: 'validar_consistencia', out: 'OK · dentro de rango histórico' },
    { ts: '14:32:24', kind: 'agent', text: 'Agente: Analista', detail: 'Random Forest + SHAP' },
    { ts: '14:32:25', kind: 'tool', name: 'predecir',           out: 'RandomForest · desvío costo y plazo' },
    { ts: '14:32:26', kind: 'tool', name: 'explicar_shap',      out: 'TreeSHAP · contribución por variable' },
    { ts: '14:32:27', kind: 'tool', name: 'banda_riesgo',       out: 'clasificador · BAJO / MEDIO / ALTO' },
    { ts: '14:32:29', kind: 'llm',  text: 'Analista sintetizando el reporte…' },
    { ts: '14:32:31', kind: 'done', text: 'Reporte listo · predicción + narrativa' },
  ];

  React.useEffect(() => {
    if (step >= lines.length) { setDone(true); return; }
    const delay = step === 0 ? 350 : 320 + Math.random() * 220;
    const t = setTimeout(() => setStep(step + 1), delay);
    return () => clearTimeout(t);
  }, [step]);

  React.useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
  }, [step]);

  const nodeStates = (() => {
    if (step <= 3) return ['active', 'idle', 'idle', 'idle'];
    if (step <= 6) return ['done', 'active', 'idle', 'idle'];
    if (step < lines.length) return ['done', 'done', 'active', 'idle'];
    return ['done', 'done', 'done', 'idle'];
  })();

  const nodes = [
    { title: 'Ingesta',        sub: 'agent · ingest',   icon: <NodeIcon kind="ingest"/> },
    { title: 'Validador',      sub: 'agent · validate', icon: <NodeIcon kind="validate"/> },
    { title: 'Analista',       sub: 'agent · analyze',  icon: <NodeIcon kind="analyze"/> },
    { title: 'Conversacional', sub: 'agent · chat',     icon: <NodeIcon kind="chat"/> },
  ];

  return (
    <div className="screen">
      <div className="page-head">
        <div>
          <div className="page-eyebrow">Nueva predicción · Paso 03 de 04 · run_id <span className="mono" style={{ color: 'var(--violet)' }}>r-2025-0901-064</span></div>
          <h1 className="page-title">Análisis en curso</h1>
          <div className="page-sub">El pipeline multi-agente está procesando tu solicitud. Esto suele tardar 15–30 segundos.</div>
        </div>
        {failed ? (
          <button className="btn" onClick={() => go('form')}>← Reintentar</button>
        ) : ready ? (
          <button className="btn btn-primary" onClick={() => go('report')}>
            Ver resultados {I.arrowRight()}
          </button>
        ) : done ? (
          <button className="btn" disabled><Spinner/> Finalizando análisis…</button>
        ) : null}
      </div>

      {failed && (
        <div className="login-error" style={{ marginBottom: 12 }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2"/><path d="M12 7v6M12 16v.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
          Error al analizar: {error}. Verifica que el backend esté activo.
        </div>
      )}

      <Stepper active="analisis"/>

      <div className="pipeline-row">
        {nodes.map((n, i) => (
          <div key={n.title} className={"node " + (nodeStates[i] === 'idle' ? '' : nodeStates[i])}>
            <div className="node-arrow"/>
            <div className="node-head">
              <div className="node-icon">{n.icon}</div>
              <div>
                <div className="node-title">{n.title}</div>
                <div className="node-sub">{n.sub}</div>
              </div>
            </div>
            <div className="node-status">
              {nodeStates[i] === 'done' && <><span>✓</span><span>completado</span></>}
              {nodeStates[i] === 'active' && <><Spinner/><span>procesando…</span></>}
              {nodeStates[i] === 'idle' && <><span style={{ color: 'var(--ink-5)' }}>○</span><span>pendiente</span></>}
            </div>
          </div>
        ))}
      </div>

      <div className="terminal">
        <div className="terminal-head">
          <div className="lights"><span/><span/><span/></div>
          <div className="title">~ desviai/agents/run.log</div>
          <div className="meta">run_id: <span style={{ color: '#A78BFA' }}>r-2025-0901-064</span></div>
        </div>
        <div className="terminal-body" ref={bodyRef}>
          {lines.slice(0, step).map((l, i) => <TermLine key={i} line={l}/>)}
          {!done && (
            <span className="t-line">
              <span className="prompt">›</span>
              <span className="ai">agente</span>
              <span className="cursor"/>
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

function Spinner() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" style={{ animation: 'spin 800ms linear infinite' }}>
      <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="14 40"/>
    </svg>
  );
}

function NodeIcon({ kind }) {
  switch (kind) {
    case 'ingest':
      return <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M12 3v14m0 0l-5-5m5 5l5-5M5 21h14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>;
    case 'validate':
      return <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M5 13l4 4 10-10" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/></svg>;
    case 'analyze':
      return <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M4 19h16M6 15l3-6 4 3 5-8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>;
    case 'chat':
      return <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M4 5h16v11H8l-4 4V5z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"/></svg>;
  }
}

function TermLine({ line }) {
  if (line.kind === 'sys') {
    return (
      <span className="t-line fade-in">
        <span className="prompt">▸</span>
        <span className="warn">[{line.ts}]</span> {line.text}
      </span>
    );
  }
  if (line.kind === 'agent') {
    return (
      <span className="t-line fade-in">
        <span className="prompt">▸</span>
        <span className="warn">[{line.ts}]</span> <span className="ai">{line.text}</span>
        <span style={{ color: '#7C8398' }}> · {line.detail}</span>
      </span>
    );
  }
  if (line.kind === 'tool') {
    return (
      <span className="t-line fade-in">
        <span className="prompt">›</span>
        tool <span className="tool">{line.name}()</span> →{' '}
        <span className={line.out.includes('OK') ? 'ok' : 'num'}>{line.out}</span>
      </span>
    );
  }
  if (line.kind === 'llm') {
    return (
      <span className="t-line fade-in">
        <span className="prompt">›</span>
        <span className="ai">LLM Analista</span> redactando reporte… <span style={{ color: '#7C8398' }}>(stream)</span>
      </span>
    );
  }
  if (line.kind === 'done') {
    return (
      <span className="t-line fade-in">
        <span className="prompt">▸</span>
        <span className="ok">✓ {line.text}</span>
      </span>
    );
  }
  return null;
}

window.ScreenPipeline = ScreenPipeline;
window.NodeIcon = NodeIcon;
window.Spinner = Spinner;
