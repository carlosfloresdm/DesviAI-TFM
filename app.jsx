/* eslint-disable */
const RECENTS = [
  { id: 'P-049', name: 'Torre Morazán · Tegucigalpa',       system: 'Concreto armado',    area: 3200, units: 64, deviation: 11.4, risk: 'MEDIO', score: 58, date: '14/08/2025' },
  { id: 'P-048', name: 'Conjunto El Merendón · San Pedro Sula', system: 'Mampostería',    area: 1450, units: 28, deviation:  4.2, risk: 'BAJO',  score: 32, date: '02/08/2025' },
  { id: 'P-047', name: 'Edificio Cangrejal · La Ceiba',     system: 'Estructura metálica',area: 2700, units: 52, deviation: 18.7, risk: 'ALTO',  score: 79, date: '21/07/2025' },
];

const ALL = [
  ...RECENTS,
  { id: 'P-046', name: 'Plaza Lempira · Comayagua',         system: 'Concreto armado',    area: 1900, units: 36, deviation:  6.8, risk: 'MEDIO', score: 51, date: '08/07/2025' },
  { id: 'P-045', name: 'Residencial Choloma · Choloma',     system: 'Prefabricado',       area: 4200, units: 88, deviation:  9.4, risk: 'MEDIO', score: 62, date: '23/06/2025' },
  { id: 'P-044', name: 'Torres del Ulúa · El Progreso',     system: 'Concreto armado',    area: 5600, units: 120,deviation: 22.3, risk: 'ALTO',  score: 84, date: '14/06/2025' },
  { id: 'P-043', name: 'Lofts Las Lomas · Tegucigalpa',     system: 'Mampostería',        area: 1100, units: 18, deviation:  3.1, risk: 'BAJO',  score: 28, date: '02/06/2025' },
  { id: 'P-042', name: 'Edificio Bay Islands · Roatán',     system: 'Estructura metálica',area: 2100, units: 40, deviation:  8.9, risk: 'MEDIO', score: 54, date: '24/05/2025' },
];

function App() {
  const initial = (location.hash || '#login').replace('#', '');
  const allRoutes = ROUTES;
  const [route, setRoute] = React.useState(allRoutes.includes(initial) ? initial : 'login');
  const [authed, setAuthed] = React.useState(initial !== 'login' && initial !== '');
  const [toasts, setToasts] = React.useState([]);

  // Estado del análisis real (proyecto enviado + resultados de la API).
  const [project, setProject] = React.useState(null);
  const [analysis, setAnalysis] = React.useState(null);
  const [analysisStatus, setAnalysisStatus] = React.useState('idle'); // idle|loading|done|error
  const [analysisError, setAnalysisError] = React.useState('');
  const [historico, setHistorico] = React.useState(null);

  // Carga la cartera histórica real una vez tras iniciar sesión.
  React.useEffect(() => {
    if (authed && !historico) {
      API.historico().then(setHistorico).catch(() => {});
    }
  }, [authed]);

  const runAnalysis = async (proj, obraId = null, checklist = null) => {
    setProject(proj);
    setAnalysis(null);
    setAnalysisStatus('loading');
    setAnalysisError('');
    try {
      const result = await API.analyze(proj, obraId, checklist);
      setAnalysis(result);
      setAnalysisStatus('done');
    } catch (e) {
      setAnalysisError(e.message || 'Error al analizar');
      setAnalysisStatus('error');
    }
  };

  // Abre una obra del histórico como reporte real (con su episodio si existe).
  const openObra = (obra) => {
    const proj = {
      sup_m2: obra.sup_m2, niveles: obra.niveles, unidades: obra.unidades,
      presupuesto_inicial: obra.presupuesto_inicial, tiempo_inicial: obra.tiempo_inicial,
      sistema_constructivo: obra.sistema_constructivo, nivel_acabado: obra.nivel_acabado,
      avance_proyecto: obra.avance_proyecto, proyectos_similares: obra.proyectos_similares,
      fecha_inicio: obra.fecha_inicio,
    };
    runAnalysis(proj, obra.id_proyecto);
    go('report');
  };

  const go = (r) => {
    setRoute(r);
    history.replaceState(null, '', '#' + r);
    window.scrollTo({ top: 0, behavior: 'instant' });
  };

  const handleLogin = () => { setAuthed(true); go('dashboard'); };
  const handleLogout = () => { setAuthed(false); go('login'); };

  const showToast = ({ kind, title, subtitle }) => {
    const id = Math.random().toString(36).slice(2);
    setToasts(t => [...t, { id, kind, title, subtitle }]);
    setTimeout(() => {
      setToasts(t => t.map(x => x.id === id ? { ...x, title: title.replace('Generando', 'Listo:'), subtitle } : x));
    }, 1500);
    setTimeout(() => {
      setToasts(t => t.filter(x => x.id !== id));
    }, 3500);
  };

  // Login screen is full-bleed — no app shell
  if (route === 'login' || (!authed && route !== 'login')) {
    return (
      <>
        <ScreenLogin onLogin={handleLogin}/>
        <ToastRoot toasts={toasts}/>
      </>
    );
  }

  return (
    <div className="app-shell">
      <Sidebar route={route} go={go}/>
      <div className="app-main">
        <TopBar route={route} go={go} onLogout={handleLogout}/>
        <SubNav route={route} go={go}/>
        <main className="app-content">
          {route === 'dashboard' && <ScreenDashboard go={go} historico={historico} openObra={openObra}/>}
          {route === 'form'      && <ScreenForm go={go} runAnalysis={runAnalysis}/>}
          {route === 'pipeline'  && <ScreenPipeline go={go} status={analysisStatus} error={analysisError}/>}
          {route === 'report'    && <ScreenReport go={go} showToast={showToast} project={project} analysis={analysis} status={analysisStatus}/>}
          {route === 'chat'      && <ScreenChat go={go} project={project} analysis={analysis}/>}
          {route === 'closeout'  && <ScreenCloseout go={go} showToast={showToast}/>}
          {route === 'history'   && <ScreenHistory go={go} historico={historico} openObra={openObra}/>}
          {route === 'settings'  && <ScreenSettings/>}
        </main>
      </div>
      <ToastRoot toasts={toasts}/>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
