/* eslint-disable */
function ScreenChat({ go, project, analysis }) {
  if (!project) {
    return (
      <div className="screen">
        <div className="card" style={{ padding: 48, textAlign: 'center' }}>
          <h3 style={{ marginBottom: 8 }}>No hay un proyecto en contexto</h3>
          <div className="page-sub" style={{ marginBottom: 20 }}>Genera una predicción para conversar con el agente sobre ella.</div>
          <button className="btn btn-primary" onClick={() => go('form')}>{I.plus()} Nueva predicción</button>
        </div>
      </div>
    );
  }

  const saludo = (() => {
    if (analysis) {
      const c = analysis.prediccion.costo;
      const p = analysis.prediccion.tiempo;
      return `Hola 👋  El reporte está listo. Resumen:\n\n• Desvío de costo estimado: ${(c.desvio_estimado_pct>0?'+':'')}${c.desvio_estimado_pct.toFixed(1)}% (riesgo ${c.riesgo}, IC80% [${c.ic80_pct[0]}%, ${c.ic80_pct[1]}%])\n• Desvío de plazo estimado: ${(p.desvio_estimado_pct>0?'+':'')}${p.desvio_estimado_pct.toFixed(1)}% (riesgo ${p.riesgo})\n\nPregúntame por los drivers, los casos comparables o cómo mitigar el riesgo.`;
    }
    return 'Hola 👋  Pregúntame lo que quieras sobre este proyecto: drivers del riesgo, casos comparables o mitigaciones.';
  })();

  const [messages, setMessages] = React.useState([{ who: 'agent', text: saludo }]);
  const [draft, setDraft] = React.useState('');
  const [typing, setTyping] = React.useState(false);
  const bodyRef = React.useRef(null);

  const suggestions = [
    '¿Qué explica el riesgo de este proyecto?',
    '¿Qué tan confiable es la predicción?',
    '¿Cómo mitigo el riesgo de cambio de alcance?',
    '¿Cómo se compara con obras históricas?',
  ];

  const sendMessage = async (text) => {
    if (!text.trim()) return;
    setMessages(m => [...m, { who: 'user', text }]);
    setDraft('');
    setTyping(true);
    try {
      const data = await API.agent(project, text, analysis ? analysis.obraId : null);
      setTyping(false);
      setMessages(m => [...m, { who: 'agent', text: data.respuesta, traza: data.trazabilidad, modo: data.modo }]);
    } catch (e) {
      setTyping(false);
      setMessages(m => [...m, { who: 'agent', text: 'No pude consultar el modelo: ' + e.message }]);
    }
  };

  React.useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
  }, [messages, typing]);

  const nodes = [
    { title: 'Ingesta', sub: 'agent · ingest' },
    { title: 'Validador', sub: 'agent · validate' },
    { title: 'Analista', sub: 'agent · analyze' },
    { title: 'Conversacional', sub: 'agent · chat' },
  ];

  return (
    <div className="screen">
      <div className="page-head">
        <div>
          <div className="page-eyebrow">Agente conversacional · contexto del proyecto actual</div>
          <h1 className="page-title">Diagnóstico experto</h1>
          <div className="page-sub">El agente responde con tool calling sobre SHAP, memoria episódica, casos similares y base de conocimiento — citando cada fuente.</div>
        </div>
        <button className="btn" onClick={() => go('report')}>← Volver al reporte</button>
      </div>

      <div className="pipeline-row">
        {nodes.map((n, i) => (
          <div key={n.title} className={"node " + (i === 3 ? "active" : "done")}>
            <div className="node-arrow"/>
            <div className="node-head">
              <div className="node-icon">
                {i === 0 && <NodeIcon kind="ingest"/>}
                {i === 1 && <NodeIcon kind="validate"/>}
                {i === 2 && <NodeIcon kind="analyze"/>}
                {i === 3 && <NodeIcon kind="chat"/>}
              </div>
              <div>
                <div className="node-title">{n.title}</div>
                <div className="node-sub">{n.sub}</div>
              </div>
            </div>
            <div className="node-status">
              {i < 3 ? <><span>✓</span><span>completado</span></> : <><span style={{ color: 'var(--orange)' }}>●</span><span>en línea</span></>}
            </div>
          </div>
        ))}
      </div>

      <div className="chat-shell">
        <div className="chat-header">
          <div className="avatar">AI</div>
          <div>
            <div className="title">DesviAI · Analista conversacional</div>
            <div className="subtitle"><span className="ok-dot"/>contexto: proyecto actual · tool calling auditable</div>
          </div>
          <div className="spacer"/>
          <span className="badge dot low">en línea</span>
        </div>

        <div className="chat-body" ref={bodyRef}>
          {messages.map((m, i) => (
            <div key={i} className={"msg " + m.who}>
              <div className="who">{m.who === 'agent' ? 'DesviAI · Analista' : 'Tú'}</div>
              {m.text}
              {m.traza && m.traza.length > 0 && (
                <div className="mono" style={{ marginTop: 8, paddingTop: 8, borderTop: '1px dashed var(--border)', fontSize: 11, color: 'var(--ink-4)' }}>
                  🔧 {m.traza.map(t => t.tool).join(' → ')}
                  {m.modo && <span style={{ marginLeft: 8, opacity: 0.7 }}>· {m.modo}</span>}
                </div>
              )}
            </div>
          ))}
          {typing && (
            <div className="msg agent typing">
              <div className="who">DesviAI · Analista</div>
              consultando herramientas <span className="dots"><span/><span/><span/></span>
            </div>
          )}
        </div>

        <div className="suggest-row">
          {suggestions.map((s, i) => (
            <button key={i} className="chip" onClick={() => sendMessage(s)}>{s}</button>
          ))}
        </div>

        <div className="chat-input">
          <input
            className="ipt"
            placeholder="Pregunta lo que quieras sobre este proyecto…"
            value={draft}
            onChange={e => setDraft(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') sendMessage(draft); }}
          />
          <button className="btn btn-primary" onClick={() => sendMessage(draft)}>
            Enviar {I.arrowRight()}
          </button>
        </div>
      </div>
    </div>
  );
}

window.ScreenChat = ScreenChat;
