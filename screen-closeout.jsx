/* eslint-disable */
// Cierre de proyecto · captura de valores reales para alimentar el reentrenamiento

function ScreenCloseout({ go, showToast }) {
  // Project being closed (P-049 — most recent prediction, fictional)
  const project = {
    id: 'P-049',
    name: 'Torre Morazán',
    location: 'Tegucigalpa · Francisco Morazán',
    system: 'Concreto armado',
    finish: 'Medio',
    predicted: {
      area: 3200,
      levels: 8,
      units: 64,
      budget: 2000000,
      duration: 20,
      startDate: '01/12/2023',
      endDateExpected: '01/08/2025',
      deviation: 11.4,        // % predicted
      ciLow: 6.2,
      ciHigh: 16.8,
      score: 58,
      risk: 'MEDIO',
      finalCostExpected: 2228000, // budget * (1 + deviation)
    },
  };

  // Actual values entered by the user
  const [finalCost, setFinalCost] = React.useState('2,180,000');
  const [finalDuration, setFinalDuration] = React.useState('22');
  const [finalArea, setFinalArea] = React.useState('3,150');
  const [finalLevels, setFinalLevels] = React.useState('8');
  const [finalUnits, setFinalUnits] = React.useState('62');
  const [finalDate, setFinalDate] = React.useState('2025-08-15');
  const [systemFinal, setSystemFinal] = React.useState('Concreto armado');
  const [finishFinal, setFinishFinal] = React.useState('Medio');
  const [notes, setNotes] = React.useState(
    'Sobrecosto principalmente por incremento del acero estructural (+9% vs cotización inicial) y dos meses de extensión por permisos municipales. Se renegoció el contrato de ventanería a precios más bajos, lo que compensó parcialmente.'
  );
  const [confirmRetrain, setConfirmRetrain] = React.useState(true);

  // Parsed numbers
  const cost = Number(finalCost.replace(/[, $]/g, '')) || 0;
  const duration = Number(finalDuration) || 0;
  const area = Number(finalArea.replace(/[, ]/g, '')) || 0;
  const levels = Number(finalLevels) || 0;
  const units = Number(finalUnits) || 0;

  // Deltas vs prediction
  const costDelta = cost - project.predicted.finalCostExpected;
  const costDeltaPct = project.predicted.finalCostExpected
    ? ((costDelta / project.predicted.finalCostExpected) * 100)
    : 0;

  // Actual deviation vs initial budget
  const actualDeviation = project.predicted.budget
    ? ((cost - project.predicted.budget) / project.predicted.budget) * 100
    : 0;
  const modelError = actualDeviation - project.predicted.deviation; // signed (puntos porcentuales)
  const insideCI = actualDeviation >= project.predicted.ciLow && actualDeviation <= project.predicted.ciHigh;

  const durationDelta = duration - project.predicted.duration;
  const areaDelta = area - project.predicted.area;
  const unitsDelta = units - project.predicted.units;

  const finalize = () => {
    showToast({ kind: 'spin', title: 'Cerrando proyecto y reentrenando modelo…', subtitle: 'P-049 · 51 proyectos → set de entrenamiento' });
    setTimeout(() => go('history'), 1800);
  };

  return (
    <div className="screen">
      <div className="page-head">
        <div>
          <div className="page-eyebrow">Cierre de proyecto · Captura de valores reales</div>
          <h1 className="page-title">Finalizar {project.id} · {project.name}</h1>
          <div className="page-sub">
            Los valores reales servirán para comparar contra la predicción y reentrenar el modelo. Marcar como finalizado moverá el proyecto del estado <span className="badge dot info" style={{ fontSize: 10, verticalAlign: 'middle' }}>EN CURSO</span> a <span className="badge dot low" style={{ fontSize: 10, verticalAlign: 'middle' }}>CERRADO</span>.
          </div>
        </div>
        <button className="btn" onClick={() => go('history')}>← Cancelar</button>
      </div>

      {/* Project context card */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', alignItems: 'center', padding: '18px 24px' }}>
          <div className="row" style={{ gap: 16 }}>
            <div style={{
              width: 56, height: 56, borderRadius: 10,
              background: 'linear-gradient(135deg, #1F65E5, #0E4DBE)',
              display: 'grid', placeItems: 'center',
              color: 'white', fontFamily: 'var(--mono)', fontWeight: 700, fontSize: 16,
              flex: 'none',
            }}>
              {project.id.replace('P-', '')}
            </div>
            <div>
              <div className="row" style={{ gap: 10 }}>
                <div style={{ fontSize: 17, fontWeight: 700, color: 'var(--ink)' }}>{project.name}</div>
                <span className="badge dot info">EN CURSO · DÍA 624</span>
              </div>
              <div className="mono" style={{ color: 'var(--ink-4)', fontSize: 12, marginTop: 4 }}>
                {project.id} · {project.location} · {project.system} · {fmt.m2(project.predicted.area)} · {project.predicted.units} unidades
              </div>
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 11, color: 'var(--ink-4)', letterSpacing: '0.06em', textTransform: 'uppercase', fontWeight: 600 }}>Predicción original</div>
            <div className="mono" style={{ fontSize: 22, fontWeight: 700, color: 'var(--orange-2)', marginTop: 4 }}>
              +{project.predicted.deviation.toFixed(1)}%
            </div>
            <div className="mono" style={{ fontSize: 11, color: 'var(--ink-4)' }}>
              IC80% [+{project.predicted.ciLow}%, +{project.predicted.ciHigh}%]
            </div>
          </div>
        </div>
      </div>

      {/* Comparison sections */}
      <CompareGroup title="Costos y presupuesto" subtitle="El driver principal del cierre · USD">
        <CompareRow
          label="Costo final ejecutado"
          predictedLabel="Costo final estimado"
          predictedValue={fmt.usd(project.predicted.finalCostExpected)}
          predictedSub={`+${project.predicted.deviation}% sobre ${fmt.usd(project.predicted.budget)}`}
          actualPrefix="USD $"
          actualValue={finalCost}
          actualOnChange={setFinalCost}
          delta={costDelta}
          deltaLabel={costDelta >= 0 ? `+${fmt.usd(Math.abs(costDelta))} sobre la predicción` : `${fmt.usd(costDelta)} bajo la predicción`}
          deltaPct={costDeltaPct}
          better={costDelta < 0}
        />
      </CompareGroup>

      <CompareGroup title="Cronograma" subtitle="Plazos ejecutados vs proyectados">
        <CompareRow
          label="Duración real"
          predictedLabel="Duración estimada"
          predictedValue={`${project.predicted.duration} meses`}
          predictedSub={`Cierre esperado · ${project.predicted.endDateExpected}`}
          actualValue={finalDuration}
          actualSuffix="meses"
          actualOnChange={setFinalDuration}
          delta={durationDelta}
          deltaLabel={durationDelta > 0 ? `${durationDelta} meses de retraso` : durationDelta < 0 ? `${Math.abs(durationDelta)} meses antes` : 'En plazo'}
          better={durationDelta <= 0}
          unit=""
        />
        <CompareRow
          label="Fecha real de cierre"
          predictedLabel="Cierre estimado"
          predictedValue={project.predicted.endDateExpected}
          predictedSub="entrega + actas de finiquito"
          actualValue={finalDate}
          actualOnChange={setFinalDate}
          actualType="date"
          hideDelta
        />
      </CompareGroup>

      <CompareGroup title="Obra construida" subtitle="Pueden cambiar respecto al diseño inicial">
        <CompareRow
          label="Superficie final construida"
          predictedLabel="Superficie estimada"
          predictedValue={fmt.m2(project.predicted.area)}
          actualValue={finalArea}
          actualSuffix="m²"
          actualOnChange={setFinalArea}
          delta={areaDelta}
          deltaLabel={areaDelta !== 0 ? `${areaDelta > 0 ? '+' : ''}${areaDelta} m² vs diseño` : 'Sin cambios'}
          better={areaDelta === 0}
        />
        <CompareRow
          label="Niveles construidos"
          predictedLabel="Niveles proyectados"
          predictedValue={`${project.predicted.levels} pisos`}
          actualValue={finalLevels}
          actualSuffix="pisos"
          actualOnChange={setFinalLevels}
          delta={levels - project.predicted.levels}
          deltaLabel={(levels - project.predicted.levels) === 0 ? 'Sin cambios' : `${levels - project.predicted.levels > 0 ? '+' : ''}${levels - project.predicted.levels} niveles`}
          better={(levels - project.predicted.levels) === 0}
        />
        <CompareRow
          label="Unidades entregadas"
          predictedLabel="Unidades proyectadas"
          predictedValue={`${project.predicted.units} und`}
          actualValue={finalUnits}
          actualSuffix="und"
          actualOnChange={setFinalUnits}
          delta={unitsDelta}
          deltaLabel={unitsDelta === 0 ? 'Sin cambios' : `${unitsDelta > 0 ? '+' : ''}${unitsDelta} unidades vs diseño`}
          better={unitsDelta >= 0}
        />
      </CompareGroup>

      <CompareGroup title="Características constructivas" subtitle="Cambios respecto al diseño original">
        <CompareRowSelect
          label="Sistema constructivo final"
          predictedLabel="Sistema proyectado"
          predictedValue={project.predicted ? project.system : ''}
          actualValue={systemFinal}
          actualOnChange={setSystemFinal}
          options={['Concreto armado', 'Estructura metálica', 'Mampostería', 'Prefabricado', 'Mixto']}
          changed={systemFinal !== project.system}
        />
        <CompareRowSelect
          label="Nivel de acabados real"
          predictedLabel="Acabados proyectados"
          predictedValue={project.finish}
          actualValue={finishFinal}
          actualOnChange={setFinishFinal}
          options={['Básico', 'Medio', 'Alto', 'Premium']}
          changed={finishFinal !== project.finish}
        />
      </CompareGroup>

      {/* Lessons learned */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-head">
          <div>
            <h3>Lecciones aprendidas <span className="accent">·</span> causas de desviación</h3>
            <div className="desc" style={{ marginTop: 2 }}>Texto libre · alimentará el contexto del agente conversacional en futuras predicciones</div>
          </div>
          <span className="mono dim" style={{ fontSize: 11.5 }}>{notes.length} car · opcional</span>
        </div>
        <div className="card-pad-lg">
          <textarea
            className="textarea"
            value={notes}
            onChange={e => setNotes(e.target.value)}
            placeholder="Describe brevemente las causas del sobrecosto o ahorro, decisiones clave, problemas con proveedores, eventos no previstos, etc."
            rows={5}
          />
        </div>
      </div>

      {/* Model performance summary */}
      <ModelSummary
        predicted={project.predicted.deviation}
        actual={actualDeviation}
        error={modelError}
        insideCI={insideCI}
        ciLow={project.predicted.ciLow}
        ciHigh={project.predicted.ciHigh}
      />

      {/* Confirmation row */}
      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-pad" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <label className="check">
            <input type="checkbox" checked={confirmRetrain} onChange={e => setConfirmRetrain(e.target.checked)}/>
            <span className="box"/>
            <span style={{ fontSize: 13 }}>Incluir este proyecto en el próximo reentrenamiento del modelo</span>
          </label>
          <div className="spacer"/>
          <button className="btn" onClick={() => go('history')}>Guardar borrador</button>
          <button className="btn btn-primary" onClick={finalize}>
            Cerrar proyecto y reentrenar modelo {I.arrowRight()}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ============ Sub-components ============ */

function CompareGroup({ title, subtitle, children }) {
  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="card-head">
        <div>
          <h3>{title}</h3>
          {subtitle && <div className="desc" style={{ marginTop: 2 }}>{subtitle}</div>}
        </div>
        <div className="compare-head-cols">
          <span>Predicción</span>
          <span/>
          <span style={{ color: 'var(--orange-2)' }}>Valor real</span>
        </div>
      </div>
      <div className="compare-body">{children}</div>
    </div>
  );
}

function CompareRow({
  label, predictedLabel, predictedValue, predictedSub,
  actualValue, actualOnChange, actualPrefix, actualSuffix, actualType,
  delta, deltaLabel, deltaPct, better, hideDelta,
}) {
  return (
    <div className="cmp-row">
      <div className="cmp-row-label">{label}</div>
      <div className="cmp-row-grid">
        <div className="cmp-predicted">
          <div className="cmp-tag">{predictedLabel}</div>
          <div className="cmp-val mono">{predictedValue}</div>
          {predictedSub && <div className="cmp-sub">{predictedSub}</div>}
        </div>
        <div className="cmp-arrow">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <div className="cmp-actual">
          <div className="cmp-tag" style={{ color: 'var(--orange-2)' }}>Real</div>
          <div className="input">
            {actualPrefix && <span className="prefix">{actualPrefix}</span>}
            <input type={actualType || 'text'} value={actualValue} onChange={e => actualOnChange(e.target.value)}/>
            {actualSuffix && <span className="suffix">{actualSuffix}</span>}
          </div>
          {!hideDelta && deltaLabel && (
            <div className={"cmp-delta " + (better ? 'good' : delta === 0 ? 'neutral' : 'warn')}>
              <span className="d-arrow">{better ? '✓' : delta === 0 ? '–' : '!'}</span>
              {deltaLabel}
              {deltaPct !== undefined && Math.abs(deltaPct) > 0.05 && (
                <span className="mono" style={{ marginLeft: 6, opacity: 0.85 }}>
                  ({deltaPct >= 0 ? '+' : ''}{deltaPct.toFixed(1)}%)
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function CompareRowSelect({ label, predictedLabel, predictedValue, actualValue, actualOnChange, options, changed }) {
  return (
    <div className="cmp-row">
      <div className="cmp-row-label">{label}</div>
      <div className="cmp-row-grid">
        <div className="cmp-predicted">
          <div className="cmp-tag">{predictedLabel}</div>
          <div className="cmp-val">{predictedValue}</div>
        </div>
        <div className="cmp-arrow">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
        </div>
        <div className="cmp-actual">
          <div className="cmp-tag" style={{ color: 'var(--orange-2)' }}>Real</div>
          <div className="input select-input">
            <select value={actualValue} onChange={e => actualOnChange(e.target.value)}>
              {options.map(o => <option key={o}>{o}</option>)}
            </select>
            <span className="chev">▾</span>
          </div>
          <div className={"cmp-delta " + (changed ? 'warn' : 'good')}>
            <span className="d-arrow">{changed ? '↻' : '✓'}</span>
            {changed ? 'Cambio respecto al diseño original' : 'Sin cambios'}
          </div>
        </div>
      </div>
    </div>
  );
}

function ModelSummary({ predicted, actual, error, insideCI, ciLow, ciHigh }) {
  const min = -5, max = 25;
  const pos = (v) => Math.max(0, Math.min(100, ((v - min) / (max - min)) * 100));
  const errAbs = Math.abs(error);
  const verdictTone = insideCI && errAbs < 5 ? 'good' : insideCI ? 'okay' : 'miss';
  const verdictText = insideCI && errAbs < 3
    ? 'Excelente — predicción muy cercana al valor real'
    : insideCI
      ? 'Aceptable — el valor real cayó dentro del intervalo de confianza'
      : 'Fuera del intervalo — el modelo necesita reentrenarse';

  return (
    <div className="card model-summary">
      <div className="card-head">
        <div>
          <h3>Comparación con la predicción <span className="accent">·</span> rendimiento del modelo</h3>
          <div className="desc" style={{ marginTop: 2 }}>Cómo se desempeñó la predicción de DesviAI frente al cierre real</div>
        </div>
        <span className={"badge dot " + (verdictTone === 'good' ? 'low' : verdictTone === 'okay' ? 'med' : 'high')}>
          {verdictTone === 'good' ? '✓ Acertada' : verdictTone === 'okay' ? '~ Aceptable' : '✕ Fuera de IC'}
        </span>
      </div>

      <div style={{ padding: '20px 24px 8px', display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 24 }}>
        <KPI label="Predicción del modelo" value={`+${predicted.toFixed(1)}%`} sub={`IC80% [+${ciLow}%, +${ciHigh}%]`} color="var(--orange-2)"/>
        <KPI label="Desviación real medida" value={`${actual >= 0 ? '+' : ''}${actual.toFixed(1)}%`} sub="costo final vs presupuesto inicial" color="var(--ink)"/>
        <KPI
          label="Error del modelo"
          value={`${error >= 0 ? '+' : ''}${error.toFixed(1)} pts`}
          sub={insideCI ? '✓ Dentro del IC 80%' : '✕ Fuera del IC 80%'}
          color={insideCI ? 'var(--green)' : 'var(--red)'}
        />
      </div>

      <div className="cmp-bar">
        <div className="cmp-bar-track"/>
        <div className="cmp-bar-ci" style={{ left: pos(ciLow) + '%', width: (pos(ciHigh) - pos(ciLow)) + '%' }}/>
        <div className="cmp-bar-pred" style={{ left: pos(predicted) + '%' }} title="Predicción"/>
        <div className="cmp-bar-actual" style={{ left: pos(actual) + '%' }} title="Real"/>
        <div className="cmp-bar-tick" style={{ left: pos(0) + '%' }}>0%</div>
        <div className="cmp-bar-tick" style={{ left: pos(ciLow) + '%' }}>+{ciLow}%</div>
        <div className="cmp-bar-tick" style={{ left: pos(predicted) + '%', color: 'var(--orange-2)', fontWeight: 700 }}>pred +{predicted}%</div>
        <div className="cmp-bar-tick" style={{ left: pos(actual) + '%', color: 'var(--ink)', fontWeight: 700, top: 36 }}>real {actual >= 0 ? '+' : ''}{actual.toFixed(1)}%</div>
        <div className="cmp-bar-tick" style={{ left: pos(ciHigh) + '%' }}>+{ciHigh}%</div>
      </div>

      <div style={{ padding: '0 24px 22px', marginTop: 28 }}>
        <div className={"cmp-verdict " + verdictTone}>
          <span className="dot"/>
          <div>
            <strong>{verdictText}.</strong>
            {' '}Al cerrar el proyecto, este caso se agregará al set de entrenamiento (51 obras) y se ajustarán las atribuciones SHAP de los features que más contribuyeron al error.
          </div>
        </div>
      </div>
    </div>
  );
}

function KPI({ label, value, sub, color }) {
  return (
    <div>
      <div style={{ fontSize: 11, color: 'var(--ink-4)', letterSpacing: '0.06em', textTransform: 'uppercase', fontWeight: 600 }}>{label}</div>
      <div className="mono" style={{ fontSize: 30, fontWeight: 700, color, marginTop: 6, letterSpacing: '-0.015em', lineHeight: 1 }}>{value}</div>
      <div className="mono" style={{ fontSize: 11.5, color: 'var(--ink-4)', marginTop: 6 }}>{sub}</div>
    </div>
  );
}

window.ScreenCloseout = ScreenCloseout;
