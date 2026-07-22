/* eslint-disable */
const BANDA_CLS = { BAJO: 'low', MEDIO: 'med', ALTO: 'high' };

function ScreenDashboard({ go, historico, openObra }) {
  if (!historico) {
    return (
      <div className="screen">
        <div className="card" style={{ padding: 48, textAlign: 'center' }}>
          <Spinner/> <span style={{ marginLeft: 8 }}>Cargando cartera histórica…</span>
        </div>
      </div>
    );
  }

  const { stats, obras } = historico;
  const d = stats.distribucion;
  const total = stats.n_obras || 1;
  const dist = [
    { label: 'Bajo',  value: d.BAJO,  color: '#16A34A', pct: Math.round(d.BAJO / total * 100) + '%' },
    { label: 'Medio', value: d.MEDIO, color: '#D97706', pct: Math.round(d.MEDIO / total * 100) + '%' },
    { label: 'Alto',  value: d.ALTO,  color: '#DC2626', pct: Math.round(d.ALTO / total * 100) + '%' },
  ];
  const recientes = obras.slice(0, 6);

  return (
    <div className="screen">
      <div className="page-head">
        <div>
          <div className="page-eyebrow">Cartera histórica · {stats.fecha_min} → {stats.fecha_max}</div>
          <h1 className="page-title">Resumen del workspace</h1>
          <div className="page-sub">Modelo Random Forest + SHAP sobre {stats.n_obras} obras. Clasificación de riesgo y memoria episódica.</div>
        </div>
        <div className="row">
          <button className="btn btn-outline">{I.download()} Exportar resumen</button>
          <button className="btn btn-primary" onClick={() => go('form')}>{I.plus()} Nueva predicción</button>
        </div>
      </div>

      <div className="stats-row">
        <div className="stat">
          <div className="stat-label">Obras históricas</div>
          <div className="stat-value">{stats.n_obras}<span className="unit">obras</span></div>
          <div className="stat-delta up">▲ dataset de entrenamiento</div>
        </div>
        <div className="stat">
          <div className="stat-label">Con episodio documentado</div>
          <div className="stat-value">{stats.n_con_episodio}</div>
          <div className="stat-sub mono">órdenes de cambio · capa forense</div>
        </div>
        <div className="stat">
          <div className="stat-label">Obras en banda ALTO</div>
          <div className="stat-value">{d.ALTO}<span className="unit">obras</span></div>
          <div className="stat-sub mono">{Math.round(d.ALTO / total * 100)}% de la cartera</div>
        </div>
        <div className="stat">
          <div className="stat-label">Distribución de riesgo</div>
          <div className="donut-wrap" style={{ marginTop: 6 }}>
            <Donut data={dist} size={112} stroke={14} center={{ value: stats.n_obras, label: 'Obras' }}/>
            <div className="legend">
              {dist.map(x => (
                <div className="legend-row" key={x.label}>
                  <span className="sw" style={{ background: x.color }}/>
                  <span style={{ color: 'var(--ink-3)' }}>{x.label}</span>
                  <span className="v">{x.value}</span>
                  <span className="pct">{x.pct}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: 16 }}>
        <div className="card">
          <div className="card-head">
            <div>
              <h3>Obras recientes</h3>
              <div className="desc" style={{ marginTop: 2 }}>Clic para abrir el reporte real (predicción, SHAP, contexto de gestión)</div>
            </div>
            <button className="btn-link" onClick={() => go('history')}>Ver todo →</button>
          </div>
          <div className="recent-list">
            {recientes.map(r => {
              const cls = BANDA_CLS[r.banda];
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
                  <div className="recent-date mono">
                    {r.tiene_episodio ? '● episodio' : '—'} · {r.fecha_inicio}
                  </div>
                  <div className="recent-chev">{I.chevRight()}</div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="col" style={{ gap: 16 }}>
          <div className="card">
            <div className="card-head">
              <h3>Salud del modelo</h3>
              <span className="badge low">● online</span>
            </div>
            <div className="card-pad">
              <ModelRow name="Modelo" desc="Random Forest por target + SHAP" v="RF v1"/>
              <ModelRow name="R² desvío costo" desc="Validación cruzada (RepeatedKFold)" v="0.48" ok/>
              <ModelRow name="AUC riesgo costo" desc="Clasificación de banda" v="0.87" ok/>
              <ModelRow name="AUC riesgo plazo" desc="Clasificación de banda" v="0.85" ok/>
              <ModelRow name="Entrenamiento" desc="Obras históricas" v={stats.n_obras + ' obras'}/>
            </div>
          </div>

          <div className="card">
            <div className="card-head"><h3>Capas del sistema</h3></div>
            <div className="card-pad" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <ChecklistItem done text="Modelo predictivo (RF) + SHAP"/>
              <ChecklistItem done text={`Memoria episódica · ${stats.n_con_episodio} obras`}/>
              <ChecklistItem done text="Análisis de contexto de gestión"/>
              <ChecklistItem done text="Agente conversacional (tool calling)"/>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ModelRow({ name, desc, v, ok }) {
  return (
    <div className="setting-row" style={{ padding: '8px 0' }}>
      <div>
        <div className="setting-name">{name}</div>
        <div className="setting-desc">{desc}</div>
      </div>
      <span className="mono" style={{ fontWeight: 700, color: ok ? 'var(--green)' : 'var(--ink-2)' }}>{v}</span>
    </div>
  );
}

function ChecklistItem({ done, text }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 13 }}>
      <span style={{
        width: 18, height: 18, borderRadius: 4,
        background: done ? 'var(--green)' : 'var(--bg-elev)',
        border: done ? '1px solid var(--green)' : '1px solid var(--border-strong)',
        display: 'grid', placeItems: 'center', flex: 'none'
      }}>
        {done && <svg width="11" height="11" viewBox="0 0 24 24"><path d="M5 13l4 4 10-10" stroke="white" strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round"/></svg>}
      </span>
      <span style={{ color: done ? 'var(--ink-4)' : 'var(--ink-2)' }}>{text}</span>
    </div>
  );
}

window.ScreenDashboard = ScreenDashboard;
