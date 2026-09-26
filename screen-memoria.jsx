/* eslint-disable */
// Memoria del agente: muestra los grafos de las tres memorias (presentacion/grafos/)
// dentro de la app. Son páginas autocontenidas; aquí sólo se incrustan en un iframe.
const GRAFOS = 'presentacion/grafos/';
const MEMORIA_VISTAS = [
  { k: 'red',       label: 'Red de notas',            sub: 'Clic selecciona · arrastra los puntos · rueda = zoom', src: 'red-interactiva.html' },
  { k: 'narrativa', label: 'Una obra, tres memorias', sub: 'Obras 118, 177 y 167',                src: 'grafo-memorias.html?view=narrativa' },
  { k: 'completa',  label: 'La red completa',         sub: '40 episodios → causas → guías',       src: 'grafo-memorias.html?view=red' },
  { k: 'agente',    label: 'Cómo razona el agente',   sub: 'Evidencia directa vs. estadística',   src: 'grafo-memorias.html?view=agente' },
];

function ScreenMemoria() {
  const [vista, setVista] = React.useState('red');
  const [oscuro, setOscuro] = React.useState(false);
  const v = MEMORIA_VISTAS.find(x => x.k === vista);
  const url = GRAFOS + v.src + (v.src.includes('?') ? '&' : '?') + 'theme=' + (oscuro ? 'dark' : 'light');

  return (
    <div className="screen">
      <div className="page-head">
        <div>
          <div className="page-eyebrow">Memoria del agente · episódica · semántica · procedural</div>
          <h1 className="page-title">Cómo se conecta lo que sabe el agente</h1>
          <div className="page-sub">
            Cada punto es una nota real de la base de conocimiento (<span className="mono">knowledge/*.md</span>) y cada línea,
            un enlace entre notas. Se genera automáticamente desde las memorias: no está dibujado a mano.
          </div>
        </div>
        <div className="row" style={{ flexShrink: 0, whiteSpace: 'nowrap' }}>
          <button className="btn btn-outline" onClick={() => setOscuro(o => !o)}>{oscuro ? '☀ Claro' : '☾ Oscuro'}</button>
          <a className="btn btn-primary" href={url} target="_blank" rel="noopener">Pantalla completa ↗</a>
        </div>
      </div>

      <div className="card" style={{ overflow: 'hidden' }}>
        <div className="filter-bar">
          {MEMORIA_VISTAS.map((x, i) => (
            <button key={x.k} className={"chip-toggle" + (vista === x.k ? ' active' : '')} onClick={() => setVista(x.k)} title={x.sub}>
              {i + 1} · {x.label}
            </button>
          ))}
          <div className="spacer"/>
          <span className="mono dim" style={{ fontSize: 11.5 }}>{v.sub}</span>
        </div>
        <iframe
          key={url}
          src={url + '&embed=1'}
          title={'Grafo de memorias · ' + v.label}
          style={{ display: 'block', width: '100%', height: 'max(560px, calc(100vh - 290px))', border: 0, background: oscuro ? '#050813' : '#eef0f4' }}
        />
      </div>
    </div>
  );
}

Object.assign(window, { ScreenMemoria });
