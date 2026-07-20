/* eslint-disable */
// Shared UI primitives for DesviAI (Procore/ACC-like shell)

const ROUTES = ['dashboard', 'form', 'pipeline', 'report', 'chat', 'closeout', 'history', 'settings', 'login'];

/* ============== Icons ============== */
const I = {
  home:    (p={}) => <svg {...p} width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M3 11l9-7 9 7v9a2 2 0 01-2 2h-4v-7H10v7H6a2 2 0 01-2-2v-9z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"/></svg>,
  predict: (p={}) => <svg {...p} width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M3 17l5-6 4 3 5-8 4 5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/><circle cx="8" cy="11" r="1.5" fill="currentColor"/><circle cx="12" cy="14" r="1.5" fill="currentColor"/><circle cx="17" cy="6" r="1.5" fill="currentColor"/></svg>,
  history: (p={}) => <svg {...p} width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M3 12a9 9 0 109-9M3 12V5M3 12h7" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/><path d="M12 7v5l3 2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg>,
  folder:  (p={}) => <svg {...p} width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"/></svg>,
  model:   (p={}) => <svg {...p} width="18" height="18" viewBox="0 0 24 24" fill="none"><rect x="5" y="5" width="14" height="14" rx="2" stroke="currentColor" strokeWidth="1.8"/><path d="M9 9h6v6H9z" stroke="currentColor" strokeWidth="1.8"/><path d="M3 9h2M3 15h2M19 9h2M19 15h2M9 3v2M15 3v2M9 19v2M15 19v2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg>,
  team:    (p={}) => <svg {...p} width="18" height="18" viewBox="0 0 24 24" fill="none"><circle cx="9" cy="9" r="3" stroke="currentColor" strokeWidth="1.8"/><path d="M3 19a6 6 0 0112 0" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/><circle cx="17" cy="8" r="2.5" stroke="currentColor" strokeWidth="1.8"/><path d="M14.5 19a5 5 0 016.5-4.8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg>,
  reports: (p={}) => <svg {...p} width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M6 3h9l5 5v13a1 1 0 01-1 1H6a1 1 0 01-1-1V4a1 1 0 011-1z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"/><path d="M14 3v5h6M9 13h6M9 17h4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg>,
  cog:     (p={}) => <svg {...p} width="18" height="18" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.8"/><path d="M19.4 15a1.7 1.7 0 00.3 1.8l.1.1a2 2 0 11-2.8 2.8l-.1-.1a1.7 1.7 0 00-1.8-.3 1.7 1.7 0 00-1 1.5V21a2 2 0 11-4 0v-.1a1.7 1.7 0 00-1.1-1.5 1.7 1.7 0 00-1.8.3l-.1.1a2 2 0 11-2.8-2.8l.1-.1a1.7 1.7 0 00.3-1.8 1.7 1.7 0 00-1.5-1H3a2 2 0 110-4h.1a1.7 1.7 0 001.5-1.1 1.7 1.7 0 00-.3-1.8l-.1-.1a2 2 0 112.8-2.8l.1.1a1.7 1.7 0 001.8.3H9a1.7 1.7 0 001-1.5V3a2 2 0 114 0v.1a1.7 1.7 0 001 1.5 1.7 1.7 0 001.8-.3l.1-.1a2 2 0 112.8 2.8l-.1.1a1.7 1.7 0 00-.3 1.8V9a1.7 1.7 0 001.5 1H21a2 2 0 110 4h-.1a1.7 1.7 0 00-1.5 1z" stroke="currentColor" strokeWidth="1.6"/></svg>,
  check:   (p={}) => <svg {...p} width="18" height="18" viewBox="0 0 24 24" fill="none"><rect x="4" y="4" width="16" height="16" rx="3" stroke="currentColor" strokeWidth="1.8"/><path d="M8 12l3 3 5-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>,
  help:    (p={}) => <svg {...p} width="16" height="16" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.8"/><path d="M9.5 9a2.5 2.5 0 015 0c0 1.5-2.5 2-2.5 4M12 17v.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg>,
  search:  (p={}) => <svg {...p} width="15" height="15" viewBox="0 0 24 24" fill="none"><circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="1.8"/><path d="M20 20l-3.5-3.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg>,
  bell:    (p={}) => <svg {...p} width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M6 9a6 6 0 1112 0c0 5 2 6 2 6H4s2-1 2-6z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"/><path d="M10 19a2 2 0 004 0" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg>,
  message: (p={}) => <svg {...p} width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M4 5h16v11H8l-4 4V5z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"/></svg>,
  chevDown: (p={}) => <svg {...p} width="12" height="12" viewBox="0 0 24 24" fill="none"><path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>,
  chevRight: (p={}) => <svg {...p} width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M9 6l6 6-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>,
  arrowRight: (p={}) => <svg {...p} width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/></svg>,
  plus:    (p={}) => <svg {...p} width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"/></svg>,
  download:(p={}) => <svg {...p} width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 4v12m0 0l-4-4m4 4l4-4M5 20h14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>,
  logout:  (p={}) => <svg {...p} width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M15 4h4v16h-4M14 12H4M8 8l-4 4 4 4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>,
};

/* ============== Sidebar ============== */
function Sidebar({ route, go }) {
  const isPredictionFlow = ['form','pipeline','report','chat'].includes(route);

  const nav = [
    { key: 'main', items: [
      { k: 'dashboard', label: 'Resumen',          icon: I.home,    target: 'dashboard' },
      { k: 'predict',   label: 'Nueva predicción', icon: I.predict, target: 'form',     count: '4 pasos' },
      { k: 'closeout',  label: 'Cerrar proyecto',  icon: I.check,   target: 'closeout', count: 1 },
      { k: 'history',   label: 'Historial',        icon: I.history, target: 'history',  count: 50 },
    ]},
    { key: 'workspace', title: 'Workspace', items: [
      { k: 'projects',  label: 'Proyectos',     icon: I.folder,  target: 'history' },
      { k: 'reports',   label: 'Reportes',      icon: I.reports, target: 'history' },
      { k: 'team',      label: 'Equipo',        icon: I.team,    target: 'settings' },
    ]},
    { key: 'admin', title: 'Administración', items: [
      { k: 'model',     label: 'Modelo IA',     icon: I.model,   target: 'settings' },
      { k: 'settings',  label: 'Configuración', icon: I.cog,     target: 'settings' },
    ]},
  ];

  // Resolve "active" key
  const activeKey = (() => {
    if (route === 'dashboard') return 'dashboard';
    if (isPredictionFlow)      return 'predict';
    if (route === 'closeout')  return 'closeout';
    if (route === 'history')   return 'history';
    if (route === 'settings')  return 'settings';
    return null;
  })();

  return (
    <aside className="sidebar">
      <div className="side-head">
        <div className="side-brand">
          <div className="side-brand-mark">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M3 18 L9 10 L13 14 L21 4" stroke="white" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"/>
              <circle cx="21" cy="4" r="1.6" fill="white"/>
            </svg>
          </div>
          <div className="side-brand-name">
            <span className="o">Desvi</span><span className="ai">AI</span>
          </div>
        </div>
      </div>

      <div className="side-project">
        <div className="swatch">CL</div>
        <div className="meta">
          <div className="label">Workspace</div>
          <div className="name">Constructora Lempira</div>
        </div>
        <span className="chev">{I.chevDown()}</span>
      </div>

      {nav.map(group => (
        <div className="side-section" key={group.key}>
          {group.title && <div className="side-section-title">{group.title}</div>}
          {group.items.map(it => (
            <button
              key={it.k}
              className={"side-item" + (activeKey === it.k ? " active" : "")}
              onClick={() => go(it.target)}
            >
              <span className="ic">{it.icon()}</span>
              <span>{it.label}</span>
              {it.count !== undefined && <span className="count">{it.count}</span>}
            </button>
          ))}
        </div>
      ))}

      <div className="side-foot">
        <div className="status">
          <span className="dot"/>
          <span>API · v1.4.2 · online</span>
        </div>
        <button className="side-item" style={{ fontSize: 12 }}>
          <span className="ic">{I.help()}</span>
          <span>Centro de ayuda</span>
        </button>
      </div>
    </aside>
  );
}

/* ============== TopBar (breadcrumbs + search + user) ============== */
function TopBar({ route, go, onLogout, crumbs }) {
  // Default crumb path per route
  const defaultCrumbs = (() => {
    switch (route) {
      case 'dashboard': return [{ label: 'Resumen', current: true }];
      case 'form':      return [{ label: 'Predicciones', go: 'history' }, { label: 'Nueva predicción', current: true }];
      case 'pipeline':  return [{ label: 'Predicciones', go: 'history' }, { label: 'Análisis en curso', current: true }];
      case 'report':    return [{ label: 'Predicciones', go: 'history' }, { label: 'Reporte · P-050', current: true }];
      case 'chat':      return [{ label: 'Predicciones', go: 'history' }, { label: 'Agente · P-050', current: true }];
      case 'closeout':  return [{ label: 'Predicciones', go: 'history' }, { label: 'Cerrar proyecto · P-049', current: true }];
      case 'history':   return [{ label: 'Historial', current: true }];
      case 'settings':  return [{ label: 'Configuración', current: true }];
      default: return [];
    }
  })();
  const path = crumbs || defaultCrumbs;

  return (
    <header className="topbar">
      <div className="crumbs">
        <span className="c" onClick={() => go('dashboard')}>Constructora Lempira</span>
        {path.map((p, i) => (
          <React.Fragment key={i}>
            <span className="sep">/</span>
            <span
              className={"c" + (p.current ? " current" : "")}
              onClick={() => p.go && go(p.go)}
            >{p.label}</span>
          </React.Fragment>
        ))}
      </div>

      <div className="tb-search">
        <span className="ic">{I.search()}</span>
        <input placeholder="Buscar proyectos, IDs, presupuestos…"/>
        <span className="kbd">⌘K</span>
      </div>

      <div className="tb-actions">
        <button className="tb-icon" title="Mensajes">
          {I.message()}
          <span className="badge-dot"/>
        </button>
        <button className="tb-icon" title="Notificaciones">
          {I.bell()}
          <span className="badge-dot"/>
        </button>
        <button className="tb-icon" title="Ayuda">{I.help({ width: 18, height: 18 })}</button>

        <div className="tb-divider"/>

        <div className="tb-user" onClick={onLogout} title="Cerrar sesión">
          <span className="avatar">LR</span>
          <div>
            <div className="name">Lucía Reyes</div>
            <div className="role">PROJECT MGR</div>
          </div>
          <span style={{ color: 'var(--ink-5)' }}>{I.chevDown()}</span>
        </div>
      </div>
    </header>
  );
}

/* ============== Subnav (project tabs / context) ============== */
function SubNav({ route, go }) {
  // Show only on dashboard / list pages — the prediction flow uses the Stepper.
  if (['form','pipeline','report','chat','login'].includes(route)) return null;

  const tabs = [
    { k: 'dashboard', label: 'Resumen',            target: 'dashboard' },
    { k: 'history',   label: 'Predicciones', count: 50, target: 'history' },
    { k: 'projects',  label: 'Proyectos',    count: 32, target: 'history' },
    { k: 'reports',   label: 'Reportes',     count: 18, target: 'history' },
    { k: 'team',      label: 'Equipo',       count:  7,  target: 'settings' },
    { k: 'settings',  label: 'Configuración',          target: 'settings' },
  ];

  const active = route;
  return (
    <nav className="subnav">
      {tabs.map(t => (
        <button
          key={t.k}
          className={"subnav-tab" + (active === t.k ? " active" : "")}
          onClick={() => go(t.target)}
        >
          {t.label}
          {t.count !== undefined && <span className="count">{t.count}</span>}
        </button>
      ))}
    </nav>
  );
}

/* ============== Stepper ============== */
function Stepper({ active }) {
  const steps = [
    { k: 'entrada',    label: 'Entrada',    sub: '01 · Datos' },
    { k: 'validacion', label: 'Validación', sub: '02 · Reglas' },
    { k: 'analisis',   label: 'Análisis',   sub: '03 · Modelo' },
    { k: 'resultado',  label: 'Resultado',  sub: '04 · Reporte' },
  ];
  const idx = steps.findIndex(s => s.k === active);
  return (
    <div className="stepper">
      {steps.map((s, i) => (
        <React.Fragment key={s.k}>
          <div className={"step " + (i < idx ? "done" : i === idx ? "active" : "")}>
            <div className="step-num">{i < idx ? '✓' : String(i + 1).padStart(2, '0')}</div>
            <div className="step-label">
              <span className="sm">{s.sub}</span>
              <span>{s.label}</span>
            </div>
          </div>
          {i < steps.length - 1 && <div className="step-line"/>}
        </React.Fragment>
      ))}
    </div>
  );
}

/* ============== Donut ============== */
function Donut({ size = 132, stroke = 16, data, center }) {
  const total = data.reduce((a,b) => a + b.value, 0);
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  let offset = 0;
  return (
    <div className="donut-host" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size/2} cy={size/2} r={r}
          fill="none" stroke="#ECEEF2" strokeWidth={stroke}/>
        {data.map((d, i) => {
          const len = (d.value / total) * c;
          const dasharray = `${len} ${c - len}`;
          const el = (
            <circle key={i}
              cx={size/2} cy={size/2} r={r}
              fill="none"
              stroke={d.color}
              strokeWidth={stroke}
              strokeDasharray={dasharray}
              strokeDashoffset={-offset}
            />
          );
          offset += len;
          return el;
        })}
      </svg>
      <div className="donut-center">
        <div>
          <div className="v">{center?.value ?? total}</div>
          <div className="l">{center?.label ?? 'Proyectos'}</div>
        </div>
      </div>
    </div>
  );
}

/* ============== Toast root ============== */
function ToastRoot({ toasts }) {
  return (
    <div className="toast-wrap">
      {toasts.map(t => (
        <div className="toast" key={t.id}>
          <div className={"ic " + (t.kind || 'spin')}>
            {t.kind === 'pdf' ? 'PDF' : t.kind === 'xls' ? 'XLS' : ''}
          </div>
          <div>
            <div className="tt">{t.title}</div>
            <div className="ts">{t.subtitle}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

/* ============== Formatters ============== */
const fmt = {
  usd: (n) => '$' + n.toLocaleString('en-US'),
  pct: (n, sign = true) => (sign && n > 0 ? '+' : '') + n.toFixed(1) + '%',
  m2:  (n) => n.toLocaleString('en-US') + ' m²',
};

/* ============== API client (mismo origen que Django) ============== */
const API = {
  base: '/api',
  async _post(path, body) {
    const r = await fetch(this.base + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json; charset=utf-8' },
      body: JSON.stringify(body),
    });
    const data = await r.json();
    if (!r.ok || data.ok === false) throw new Error(data.error || ('HTTP ' + r.status));
    return data;
  },
  async _get(path) {
    const r = await fetch(this.base + path);
    const data = await r.json();
    if (!r.ok || data.ok === false) throw new Error(data.error || ('HTTP ' + r.status));
    return data;
  },
  health()               { return this._get('/health'); },
  historico()            { return this._get('/historico'); },
  predict(project)       { return this._post('/predict', { project }); },
  explain(project)       { return this._post('/explain', { project }); },
  agent(project, pregunta, obra_id=null, historial=null) {
    return this._post('/agent/chat', { project, pregunta, obra_id, historial });
  },
  // Análisis de contexto de gestión (checklist opcional del reporte).
  contextoConfig(project)   { return this._post('/contexto/config', { project }); },
  contextoCalcular(checklist) { return this._post('/contexto/calcular', { checklist }); },
  contextoExplicar(contexto) { return this._post('/contexto/explicar', { contexto }); },
  // Orquesta el análisis. Si obraId no es null (obra del histórico), se excluye a sí
  // misma de los similares/score y se recupera su episodio (evidencia directa).
  // Si el usuario completó el checklist de contexto de gestión en la entrada de
  // datos, se calcula aquí y el reporte solo muestra el resultado.
  async analyze(project, obraId=null, checklist=null) {
    const [pred, exp, sim, sc, ctx] = await Promise.all([
      this.predict(project),
      this.explain(project),
      this._post('/similares', { project, k: 5, excluir_id: obraId }),
      this._post('/score-contextual', { project, excluir_id: obraId }),
      checklist ? this.contextoCalcular(checklist) : Promise.resolve(null),
    ]);
    let episodio = null;
    if (obraId != null) {
      try { episodio = await this._get('/episodio/' + obraId); } catch (e) { /* sin episodio */ }
    }
    return {
      prediccion: pred.prediccion,
      explicaciones: exp.explicaciones,
      similares: sim.similares,
      score: sc.score_contextual,
      contexto: ctx ? ctx.contexto : null,
      episodio,
      obraId,
    };
  },
};

/* Opciones de formulario que coinciden EXACTO con las categorías del modelo. */
const MODEL_OPTS = {
  sistema_constructivo: ['Concreto Postensado', 'Concreto Tradicional'],
  nivel_acabado: ['Básico', 'Medio', 'Alto'],
  avance_proyecto: ['60 - 70', '70 - 80', '80 - 90', '90 - 100'],
  proyectos_similares: ['0 - 5', '5 - 10', '10 - 15', '15 - 20', '20 +'],
};

Object.assign(window, { ROUTES, I, Sidebar, TopBar, SubNav, Stepper, Donut, ToastRoot, fmt, API, MODEL_OPTS });
