/* eslint-disable */
// Floating conversational agent — bubble + popup chat for the report screen.

function FloatingChat({ project, obraId }) {
  const [open, setOpen] = React.useState(false);
  const [seen, setSeen] = React.useState(false);
  const [messages, setMessages] = React.useState([
    { who: 'agent', text: 'Hola 👋  Soy el agente conversacional de DesviAI. Tengo el contexto de este proyecto: predicción, SHAP, casos similares y memoria.\n\nPuedo profundizar en cualquier punto, comparar con históricos o sugerir mitigaciones. ¿Por dónde empezamos?' },
  ]);
  const [draft, setDraft] = React.useState('');
  const [typing, setTyping] = React.useState(false);
  const bodyRef = React.useRef(null);

  // Auto-dismiss the teaser after 6s
  React.useEffect(() => {
    const t = setTimeout(() => setSeen(true), 6000);
    return () => clearTimeout(t);
  }, []);

  React.useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
  }, [messages, typing, open]);

  const suggestions = [
    '¿Qué factor genera más riesgo?',
    '¿Qué tan confiable es la predicción?',
    '¿Cómo se compara con históricos?',
  ];

  const sendMessage = async (text) => {
    if (!text.trim()) return;
    setMessages(m => [...m, { who: 'user', text }]);
    setDraft('');
    setTyping(true);
    try {
      const data = await API.agent(project, text, obraId);
      setTyping(false);
      setMessages(m => [...m, { who: 'agent', text: data.respuesta, traza: data.trazabilidad }]);
    } catch (e) {
      setTyping(false);
      setMessages(m => [...m, { who: 'agent', text: 'No pude consultar el modelo: ' + e.message }]);
    }
  };

  const handleToggle = () => {
    setOpen(!open);
    setSeen(true);
  };

  return (
    <div className="fab-host">
      {/* Teaser tooltip (first visit) */}
      {!open && !seen && (
        <div className="fab-teaser">
          <div className="fab-teaser-head">
            <span className="badge dot low" style={{ fontSize: 9 }}>EN LÍNEA</span>
            <button className="fab-teaser-x" onClick={() => setSeen(true)} aria-label="Cerrar">✕</button>
          </div>
          <div className="fab-teaser-body">
            <strong>¿Tienes preguntas sobre este reporte?</strong>
            <div className="dim" style={{ fontSize: 12, marginTop: 4 }}>
              Puedo explicarte la predicción, los SHAP, los proyectos similares o sugerir mitigaciones.
            </div>
          </div>
          <div className="fab-teaser-tail"/>
        </div>
      )}

      {/* Popup chat panel */}
      {open && (
        <div className="chat-popup">
          <div className="chat-popup-head">
            <div className="avatar">AI</div>
            <div style={{ minWidth: 0 }}>
              <div className="title">Agente conversacional</div>
              <div className="subtitle">
                <span className="ok-dot"/>contexto: reporte P-050
              </div>
            </div>
            <div className="spacer"/>
            <button className="cp-icon" title="Cerrar" onClick={() => setOpen(false)}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            </button>
          </div>

          <div className="chat-popup-body" ref={bodyRef}>
            {messages.map((m, i) => (
              <div key={i} className={"msg " + m.who}>
                <div className="who">{m.who === 'agent' ? 'DesviAI' : 'Tú'}</div>
                {m.text}
              </div>
            ))}
            {typing && (
              <div className="msg agent typing">
                <div className="who">DesviAI</div>
                escribiendo <span className="dots"><span/><span/><span/></span>
              </div>
            )}
          </div>

          {messages.length <= 2 && (
            <div className="cp-suggest">
              {suggestions.map((s, i) => (
                <button key={i} className="chip" onClick={() => sendMessage(s)}>{s}</button>
              ))}
            </div>
          )}

          <div className="chat-popup-input">
            <input
              className="ipt"
              placeholder="Pregunta sobre el reporte…"
              value={draft}
              onChange={e => setDraft(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') sendMessage(draft); }}
              autoFocus
            />
            <button className="btn btn-primary btn-sm" onClick={() => sendMessage(draft)} aria-label="Enviar">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <path d="M3 12L21 4l-4 17-5-7-9-2z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* The floating bubble itself */}
      <button
        className={"fab" + (open ? " open" : "") + (!seen && !open ? " pulse" : "")}
        onClick={handleToggle}
        aria-label={open ? 'Cerrar chat' : 'Abrir chat con el agente'}
      >
        <span className="fab-status"/>
        {open ? (
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
            <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        ) : (
          <span className="fab-content">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path d="M4 5h16v11H9l-5 4V5z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"/>
              <circle cx="9" cy="10.5" r="1.2" fill="currentColor"/>
              <circle cx="13" cy="10.5" r="1.2" fill="currentColor"/>
              <circle cx="17" cy="10.5" r="1.2" fill="currentColor"/>
            </svg>
          </span>
        )}
      </button>
    </div>
  );
}

window.FloatingChat = FloatingChat;
