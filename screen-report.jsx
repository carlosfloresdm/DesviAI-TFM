/* eslint-disable */
// Reporte conectado al modelo real. Renderiza la salida de /api/predict,
// /api/explain, /api/similares y /api/score-contextual.

const BANDA_CLASS = { BAJO: 'low', MEDIO: 'med', ALTO: 'high' };
const pctStr = (n) => (n > 0 ? '+' : '') + Number(n).toFixed(1) + '%';
const CAUSA_NOMBRE = {
  alcance: 'Cambio de alcance', 'diseño': 'Error u omisión de diseño',
  sitio: 'Condición de sitio', proveedor: 'Proveedor / suministro',
  normativa: 'Ajuste normativo', clima: 'Clima',
};

function Meta({ label, value }) {
  return (
    <div>
      <div style={{ fontSize: 11, color: 'var(--ink-4)', letterSpacing: '0.05em', textTransform: 'uppercase', fontWeight: 600 }}>{label}</div>
      <div className="mono" style={{ fontSize: 14, fontWeight: 700, color: 'var(--ink)', marginTop: 4 }}>{value}</div>
    </div>
  );
}

// El modelo produce DOS salidas que responden preguntas distintas: el % (¿cuánto
// se desvía? — regresión) y la banda (¿qué tan probable es superar el desvío típico
// del histórico? — clasificador). No son lo mismo ni una se deriva de la otra; la
// frase lo explica sin repetir números: la banda habla de probabilidad, el % grande
// de magnitud.
const PROB_TXT = { BAJO: 'Poco probable', MEDIO: 'Probabilidad media de', ALTO: 'Altamente probable' };

function DevBlock({ titulo, dim, sustantivo }) {
  return (
    <div className="deviation">
      <div className="page-eyebrow" style={{ marginBottom: 0 }}>{titulo}</div>
      <div className="deviation-pct">
        <span className="sign">{dim.desvio_estimado_pct > 0 ? '+' : ''}</span>
        {Number(dim.desvio_estimado_pct).toFixed(1)}<span className="small">%</span>
      </div>
      <div style={{ marginTop: 2 }}>
        <span className={"badge dot " + BANDA_CLASS[dim.riesgo]}>Riesgo {dim.riesgo.toLowerCase()}</span>
      </div>
      <div className="dim" style={{ fontSize: 12.5, lineHeight: 1.5, marginTop: 6 }}>
        {PROB_TXT[dim.riesgo]} un {sustantivo} por encima del típico del histórico.
      </div>
    </div>
  );
}

function ScreenReport({ go, showToast, project, analysis, status }) {
  if (status !== 'done' || !analysis) {
    return (
      <div className="screen">
        <div className="card" style={{ padding: 48, textAlign: 'center' }}>
          <h3 style={{ marginBottom: 8 }}>No hay un análisis activo</h3>
          <div className="page-sub" style={{ marginBottom: 20 }}>Genera una predicción para ver su reporte.</div>
          <button className="btn btn-primary" onClick={() => go('form')}>{I.plus()} Nueva predicción</button>
        </div>
      </div>
    );
  }

  const { prediccion, explicaciones, similares, score } = analysis;
  const sc = score.dimensiones.costo;
  const expC = explicaciones.desvio_costo;
  const shap = expC.contribuciones;
  const maxAbs = Math.max(...shap.map(s => Math.abs(s.contribucion_pts))) || 1;

  return (
    <div className="screen">
      <div className="page-head">
        <div>
          <div className="page-eyebrow">
            Resultado · Modelo <span className="mono" style={{ color: 'var(--ink-2)' }}>RandomForest v1</span> · SHAP · 200 obras
          </div>
          <h1 className="page-title">Reporte de predicción</h1>
          <div className="page-sub">
            {project.sup_m2.toLocaleString('en-US')} m² · {project.niveles} niveles · {project.sistema_constructivo} · acabado {project.nivel_acabado}
          </div>
        </div>
        <div className="export-btns">
          <button className="export-btn" onClick={() => showToast({ kind: 'pdf', title: 'Generando reporte PDF…', subtitle: 'desviai_reporte.pdf' })}>
            <span className="doc-icon pdf">PDF</span><span>Exportar PDF</span>
          </button>
          <button className="export-btn" onClick={() => showToast({ kind: 'xls', title: 'Generando reporte Excel…', subtitle: 'desviai_data.xlsx' })}>
            <span className="doc-icon xls">XLS</span><span>Exportar Excel</span>
          </button>
        </div>
      </div>

      <Stepper active="resultado"/>

      {/* Hero: score contextual + desvío de costo y de plazo */}
      <div className="risk-hero">
        <div className="risk-hero-grid">
          <div className="risk-score">
            <span className={"badge dot " + BANDA_CLASS[sc.banda]}>Riesgo {sc.banda.toLowerCase()}</span>
            <div className="risk-score-num">{sc.score}<span className="denom">/100</span></div>
            <span className="label">Score de riesgo contextual</span>
            <div className="dim" style={{ fontSize: 12, lineHeight: 1.5, marginTop: 4 }}>
              Modelo + casos similares + memoria episódica.
            </div>
          </div>
          <div className="col" style={{ gap: 14 }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: 13.5 }}>Según el modelo predictivo</div>
              <div className="dim" style={{ fontSize: 12 }}>
                Estimación basada en las <strong>dimensiones de diseño</strong> de la obra
                (superficie, niveles, presupuesto, sistema constructivo…).
              </div>
            </div>
            <DevBlock titulo="Desvío de costo" dim={prediccion.costo} sustantivo="sobrecosto"/>
            <div className="divider" style={{ margin: 0 }}/>
            <DevBlock titulo="Desvío de plazo" dim={prediccion.tiempo} sustantivo="sobreplazo"/>
          </div>
        </div>
      </div>

      <div className="report-grid">
        {/* SHAP local */}
        <div className="card">
          <div className="card-head">
            <div>
              <h3>Atribución de features <span className="accent">·</span> SHAP</h3>
              <div className="desc" style={{ marginTop: 2 }}>Contribución de cada variable al desvío de costo (pts %)</div>
            </div>
          </div>
          <div className="shap">
            <div className="shap-row head">
              <span>Feature</span>
              <span className="c">← reduce  /  aumenta →</span>
              <span className="r">Δ pts</span>
            </div>
            {shap.map((s, i) => {
              const dir = s.sentido === 'sube' ? 'pos' : 'neg';
              const w = (Math.abs(s.contribucion_pts) / maxAbs) * 48;
              return (
                <div className="shap-row" key={i}>
                  <div className="shap-name">{s.variable}</div>
                  <div className="shap-bar">
                    <div className="shap-axis"/>
                    <div className={"shap-fill " + dir} style={{ width: w + '%' }}/>
                  </div>
                  <div className={"shap-value " + dir}>
                    {s.contribucion_pts > 0 ? '+' : ''}{Number(s.contribucion_pts).toFixed(2)}
                  </div>
                </div>
              );
            })}
            <div className="dim" style={{ fontSize: 12, paddingTop: 8, lineHeight: 1.5 }}>{expC.resumen}</div>
          </div>
        </div>

        {/* Casos similares */}
        <div className="card">
          <div className="card-head">
            <div>
              <h3>Proyectos similares <span className="accent">·</span> top {similares.k}</h3>
              <div className="desc" style={{ marginTop: 2 }}>kNN sobre el histórico · desempeño real</div>
            </div>
          </div>
          <table className="tbl">
            <thead>
              <tr><th>ID</th><th>Desv. real</th><th>Sistema</th><th style={{ textAlign: 'right' }}>Evidencia</th></tr>
            </thead>
            <tbody>
              {similares.vecinos.map(r => (
                <tr key={r.id_proyecto}>
                  <td className="id">#{r.id_proyecto}</td>
                  <td className={"num " + (r.desvio_costo_alto ? '' : 'pos')} style={{ color: r.desvio_costo_alto ? 'var(--red)' : 'var(--green)' }}>
                    {pctStr(r.desvio_costo_real)}
                  </td>
                  <td className="dim" style={{ fontSize: 12.5 }}>
                    {r.sistema_constructivo}
                    <div className="mono" style={{ color: 'var(--ink-4)', fontSize: 11, marginTop: 2 }}>
                      {fmt.m2(r.sup_m2)} · {r.niveles} niv
                    </div>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    {r.tiene_episodio
                      ? <span className="badge low" style={{ fontSize: 10 }}>episodio</span>
                      : <span className="mono dim" style={{ fontSize: 11 }}>—</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Análisis de contexto de gestión: el checklist se responde en la entrada
            de datos; aquí solo se muestra el resultado (si se incluyó). */}
        {analysis.contexto && <ContextoResultadoCard resultado={analysis.contexto}/>}

        {/* Episodio documentado (evidencia directa) — sólo para obras del histórico */}
        {analysis.episodio && analysis.episodio.existe_evidencia && (
          <div className="card full">
            <div className="card-head">
              <div>
                <h3>Episodio documentado <span className="accent">·</span> evidencia directa</h3>
                <div className="desc" style={{ marginTop: 2 }}>Órdenes de cambio reconstruidas de esta obra (memoria episódica)</div>
              </div>
              <span className="badge low">obra #{analysis.episodio.obra_id}</span>
            </div>
            <div className="card-pad">
              <div className="row" style={{ gap: 32, flexWrap: 'wrap' }}>
                <Meta label="Causa dominante" value={CAUSA_NOMBRE[analysis.episodio.meta.causa_dominante] || analysis.episodio.meta.causa_dominante}/>
                <Meta label="Categorías" value={(analysis.episodio.meta.categorias_causa || []).map(c => CAUSA_NOMBRE[c] || c).join(' · ')}/>
                <Meta label="Desvío costo real" value={analysis.episodio.meta.desvio_costo_real + '%'}/>
                <Meta label="Desvío plazo real" value={analysis.episodio.meta.desvio_tiempo_real + '%'}/>
              </div>
              <div className="dim" style={{ fontSize: 12.5, marginTop: 14 }}>
                Pregúntale al agente <em>"¿por qué se desvió esta obra?"</em> para el detalle con cada orden de cambio citada como fuente.
              </div>
            </div>
          </div>
        )}

        {/* Narrativa */}
        <div className="card full">
          <div className="card-head">
            <div>
              <h3>Narrativa del análisis <span className="accent">·</span> trazable</h3>
              <div className="desc" style={{ marginTop: 2 }}>Síntesis a partir del reporte cuantitativo</div>
            </div>
          </div>
          <div className="narrative">
            <p>{sc.narrativa}</p>
            <p>{expC.resumen}</p>
            <p className="dim" style={{ fontSize: 12.5 }}>
              ¿Dudas sobre este reporte? Abre el chat con el agente (abajo a la derecha) para preguntar por los drivers, los casos similares o cómo mitigar el riesgo.
            </p>
          </div>
        </div>
      </div>

      <div className="report-cta">
        <button className="btn btn-outline btn-lg" onClick={() => go('chat')}>Abrir agente conversacional →</button>
      </div>

      <FloatingChat project={project} obraId={analysis.obraId}/>
    </div>
  );
}

window.ScreenReport = ScreenReport;
