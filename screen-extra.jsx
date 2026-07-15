/* eslint-disable */
function ScreenHistory({ go, historico, openObra }) {
  const [filter, setFilter] = React.useState('all');

  if (!historico) {
    return (
      <div className="screen">
        <div className="card" style={{ padding: 48, textAlign: 'center' }}>
          <Spinner/> <span style={{ marginLeft: 8 }}>Cargando historial…</span>
        </div>
      </div>
    );
  }

  const all = historico.obras;
  const byBanda = (b) => all.filter(r => r.banda === b);
  const filtered = filter === 'all' ? all
    : filter === 'low'  ? byBanda('BAJO')
    : filter === 'med'  ? byBanda('MEDIO')
    :                     byBanda('ALTO');

  return (
    <div className="screen">
      <div className="page-head">
        <div>
          <div className="page-eyebrow">Historial · {all.length} obras del dataset</div>
          <h1 className="page-title">Cartera histórica</h1>
          <div className="page-sub">Cada obra con su banda de riesgo (clasificador) y desvío real. Clic para abrir su reporte.</div>
        </div>
        <div className="row">
          <button className="btn btn-outline">{I.download()} Exportar CSV</button>
          <button className="btn btn-primary" onClick={() => go('form')}>{I.plus()} Nueva predicción</button>
        </div>
      </div>

      <div className="card">
        <div className="filter-bar">
          <button className={"chip-toggle" + (filter === 'all' ? ' active' : '')} onClick={() => setFilter('all')}>Todas · {all.length}</button>
          <button className={"chip-toggle" + (filter === 'low' ? ' active' : '')} onClick={() => setFilter('low')}><span style={{ width:6,height:6,borderRadius:'50%',background:'var(--green)' }}/> Bajo · {byBanda('BAJO').length}</button>
          <button className={"chip-toggle" + (filter === 'med' ? ' active' : '')} onClick={() => setFilter('med')}><span style={{ width:6,height:6,borderRadius:'50%',background:'var(--amber)' }}/> Medio · {byBanda('MEDIO').length}</button>
          <button className={"chip-toggle" + (filter === 'high' ? ' active' : '')} onClick={() => setFilter('high')}><span style={{ width:6,height:6,borderRadius:'50%',background:'var(--red)' }}/> Alto · {byBanda('ALTO').length}</button>
          <div className="spacer"/>
          <span className="mono dim" style={{ fontSize: 11.5 }}>{filtered.length} resultados · ordenado por fecha</span>
        </div>
        <div className="recent-list">
          {filtered.slice(0, 60).map(r => {
            const cls = r.banda === 'BAJO' ? 'low' : r.banda === 'MEDIO' ? 'med' : 'high';
            const devColor = r.desvio_costo > 8 ? 'var(--red)' : r.desvio_costo > 4 ? 'var(--orange-2)' : 'var(--green)';
            return (
              <div className="recent-row" key={r.id_proyecto} onClick={() => openObra(r)}>
                <div className="recent-id">#{r.id_proyecto}</div>
                <div className="recent-name">
                  {r.sistema_constructivo} · acabado {r.nivel_acabado}
                  <span className="meta">{fmt.m2(r.sup_m2)} · {r.niveles} niveles · {r.unidades} unidades</span>
                </div>
                <div className="recent-dev" style={{ color: devColor }}>{fmt.pct(r.desvio_costo)}</div>
                <div><span className={"badge dot " + cls}>{r.banda}</span></div>
                <div className="recent-date mono">{r.tiene_episodio ? '● episodio' : '—'} · {r.fecha_inicio}</div>
                <div className="recent-chev">{I.chevRight()}</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function ScreenSettings() {
  const [t1, setT1] = React.useState(true);
  const [t2, setT2] = React.useState(true);
  const [t3, setT3] = React.useState(false);
  const [t4, setT4] = React.useState(true);

  return (
    <div className="screen">
      <div className="page-head">
        <div>
          <div className="page-eyebrow">Workspace · Constructora Lempira</div>
          <h1 className="page-title">Configuración</h1>
          <div className="page-sub">Parámetros del modelo y preferencias del workspace.</div>
        </div>
      </div>

      <div className="settings-grid">
        <div className="card">
          <div className="card-head"><h3>Modelo de predicción</h3><span className="badge low">activo</span></div>
          <div className="card-pad">
            <Setting name="Versión activa" desc="XGBoost v1.4.2 · entrenado 12/08/2025" v="v1.4.2"/>
            <Setting name="Intervalo de confianza" desc="Ancho del IC en los reportes" v="80%"/>
            <Setting name="Re-entrenamiento automático" desc="Cuando se agregan 5+ proyectos nuevos" toggle={t1} on={() => setT1(!t1)}/>
            <Setting name="Incluir features macro" desc="Inflación, tasa de cambio, índice de construcción" toggle={t2} on={() => setT2(!t2)}/>
          </div>
        </div>
        <div className="card">
          <div className="card-head"><h3>Workspace</h3></div>
          <div className="card-pad">
            <Setting name="Moneda" desc="Mostrar todos los valores en…" v="USD ($)"/>
            <Setting name="Notificar al completar análisis" desc="Email a lucia.reyes@constructora-lempira.hn" toggle={t4} on={() => setT4(!t4)}/>
            <Setting name="Compartir reportes con el equipo" desc="Por defecto todos los reportes son privados" toggle={t3} on={() => setT3(!t3)}/>
            <Setting name="Zona horaria" desc="Para timestamps de los reportes" v="UTC-6 · Tegucigalpa"/>
          </div>
        </div>
      </div>
    </div>
  );
}

function Setting({ name, desc, v, toggle, on }) {
  return (
    <div className="setting-row">
      <div>
        <div className="setting-name">{name}</div>
        <div className="setting-desc">{desc}</div>
      </div>
      {v !== undefined && <div className="mono" style={{ color: 'var(--orange-2)', fontSize: 13, fontWeight: 600 }}>{v}</div>}
      {toggle !== undefined && (
        <div className={"toggle " + (toggle ? "on" : "")} onClick={on}/>
      )}
    </div>
  );
}

window.ScreenHistory = ScreenHistory;
window.ScreenSettings = ScreenSettings;
