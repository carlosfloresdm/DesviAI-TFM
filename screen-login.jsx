/* eslint-disable */
function ScreenLogin({ onLogin }) {
  const [email, setEmail] = React.useState('lucia.reyes@constructora-lempira.hn');
  const [password, setPassword] = React.useState('••••••••••••');
  const [remember, setRemember] = React.useState(true);
  const [show, setShow] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState('');

  const submit = (e) => {
    if (e) e.preventDefault();
    setError('');
    if (!email.includes('@') || password.length < 4) {
      setError('Credenciales inválidas. Verifica tu correo y contraseña.');
      return;
    }
    setLoading(true);
    setTimeout(() => { setLoading(false); onLogin(); }, 900);
  };

  return (
    <div className="login-shell">
      <aside className="login-aside">
        <div className="login-aside-top">
          <div className="side-brand" style={{ fontSize: 18 }}>
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
          <div className="mono" style={{ fontSize: 11, color: '#9CA0AC' }}>
            <span className="ok-dot"/>API · v1.4.2 · online
          </div>
        </div>

        <div className="login-aside-mid">
          <div className="eyebrow" style={{ color: '#9CA0AC' }}>v1.4.2 · Predicción de costos para construcción</div>
          <h1 className="login-headline">
            Anticipa la <span style={{ color: 'var(--orange)' }}>desviación de costos</span> antes de poner la primera piedra.
          </h1>
          <p className="login-blurb">
            Modelo Random Forest entrenado con 200 obras históricas. Explicaciones SHAP, score de riesgo contextual y agente conversacional con memoria y narrativa en lenguaje natural.
          </p>

          <div className="login-preview">
            <div className="lp-head">
              <div className="lp-id">› run · r-2025-0901-064</div>
              <div className="mono" style={{ fontSize: 10.5, color: '#9CA0AC', letterSpacing: '0.06em', textTransform: 'uppercase' }}>en vivo</div>
            </div>
            <div className="lp-bar">
              <div className="lp-bar-fill"/>
              <div className="lp-bar-point" style={{ left: '54%' }}/>
            </div>
            <div className="lp-row">
              <span style={{ fontSize: 12, color: '#9CA0AC' }}>Desviación estimada</span>
              <span className="mono" style={{ color: 'var(--orange)', fontSize: 17, fontWeight: 700 }}>+14.2%</span>
            </div>
            <div className="lp-row">
              <span style={{ fontSize: 12, color: '#9CA0AC' }}>IC 80%</span>
              <span className="mono" style={{ fontSize: 13, color: '#C9CDD7' }}>[+8.2%, +20.2%]</span>
            </div>
            <div className="lp-row">
              <span style={{ fontSize: 12, color: '#9CA0AC' }}>Score</span>
              <span className="badge med" style={{ fontSize: 10 }}>MEDIO · 64/100</span>
            </div>
          </div>
        </div>

        <div className="login-aside-bot">
          <div className="mono" style={{ fontSize: 11, letterSpacing: '0.04em', color: '#7C8398' }}>
            © 2025 DesviAI · Constructora Lempira · Honduras
          </div>
        </div>

        <div className="login-grid-bg" aria-hidden="true"/>
      </aside>

      <main className="login-main">
        <div className="login-card">
          <div className="login-card-head">
            <div className="page-eyebrow" style={{ marginBottom: 4 }}>Acceso al workspace</div>
            <h2 className="login-title">Inicia sesión</h2>
            <div className="page-sub">Usa tu correo corporativo para acceder a tus predicciones.</div>
          </div>

          <form className="login-form" onSubmit={submit}>
            <div className="field">
              <label htmlFor="email">Correo electrónico</label>
              <div className="input">
                <span className="prefix">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                    <path d="M3 6h18v12H3z M3 6l9 7 9-7" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" fill="none"/>
                  </svg>
                </span>
                <input
                  id="email" type="email" value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="tu@constructora.hn" autoComplete="email"
                  style={{ fontSize: 13.5 }}
                />
              </div>
            </div>

            <div className="field">
              <label htmlFor="password">
                Contraseña
                <span className="help" style={{ cursor: 'pointer', color: 'var(--blue)' }} onClick={() => alert('Enlace de recuperación enviado al correo')}>
                  ¿Olvidaste tu contraseña?
                </span>
              </label>
              <div className="input">
                <span className="prefix">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                    <rect x="4" y="11" width="16" height="10" rx="2" stroke="currentColor" strokeWidth="1.8"/>
                    <path d="M8 11V8a4 4 0 018 0v3" stroke="currentColor" strokeWidth="1.8"/>
                  </svg>
                </span>
                <input
                  id="password" type={show ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="Tu contraseña" autoComplete="current-password"
                />
                <button type="button" className="login-eye" onClick={() => setShow(s => !s)}>
                  {show ? (
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M3 3l18 18M10.6 10.6a3 3 0 004.2 4.2M9.9 5.1A10 10 0 0112 5c5 0 9 4 10 7-0.5 1.5-1.7 3.2-3.4 4.6M6.4 6.4C4 8 2.5 10.3 2 12c1 3 5 7 10 7 1.4 0 2.7-.3 4-.8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg>
                  ) : (
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z" stroke="currentColor" strokeWidth="1.8"/><circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.8"/></svg>
                  )}
                </button>
              </div>
            </div>

            <div className="row login-row">
              <label className="check">
                <input type="checkbox" checked={remember} onChange={e => setRemember(e.target.checked)}/>
                <span className="box"/>
                <span>Mantener sesión iniciada</span>
              </label>
              <div className="spacer"/>
              <span className="mono" style={{ fontSize: 10.5, color: 'var(--ink-4)' }}>
                <span className="ok-dot"/>TLS 1.3
              </span>
            </div>

            {error && (
              <div className="login-error">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2"/><path d="M12 7v6M12 16v.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
                {error}
              </div>
            )}

            <button className="btn btn-primary login-submit" type="submit" disabled={loading}>
              {loading ? (
                <>
                  <Spinner/>
                  <span>Autenticando…</span>
                </>
              ) : (
                <>
                  <span>Iniciar sesión</span>
                  {I.arrowRight()}
                </>
              )}
            </button>

            <div className="login-divider"><span>o continúa con</span></div>

            <div className="sso-row">
              <button type="button" className="sso-btn">
                <svg width="16" height="16" viewBox="0 0 48 48"><path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.2 7.9 3l5.7-5.7C34.1 6.1 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.4-.4-3.5z"/><path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 16 19 13 24 13c3.1 0 5.8 1.2 7.9 3l5.7-5.7C34.1 6.1 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"/><path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2c-2 1.4-4.5 2.4-7.2 2.4-5.3 0-9.7-3.3-11.3-8l-6.5 5C9.5 39.6 16.2 44 24 44z"/><path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.1-4.1 5.4l6.2 5.2C40.8 36.4 44 30.7 44 24c0-1.3-.1-2.4-.4-3.5z"/></svg>
                Google Workspace
              </button>
              <button type="button" className="sso-btn">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M11.4 24H0V12.6h11.4V24zM24 24H12.6V12.6H24V24zM11.4 11.4H0V0h11.4v11.4zM24 11.4H12.6V0H24v11.4z"/></svg>
                Microsoft 365
              </button>
            </div>

            <div className="login-foot">
              ¿No tienes cuenta? <a href="#" onClick={e => e.preventDefault()}>Solicita acceso a tu admin</a>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}

window.ScreenLogin = ScreenLogin;
