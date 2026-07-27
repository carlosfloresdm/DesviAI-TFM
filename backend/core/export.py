"""
export.py — Genera el reporte descargable en Excel (openpyxl) y PDF (reportlab).

Recibe la obra + las salidas ya calculadas (predicción, explicación SHAP, contexto
de gestión y episodio si existe) y produce los bytes del archivo. La lógica de
armado del contenido vive aquí; los endpoints (views_api) solo recalculan y sirven.

Ambos formatos comparten la misma estructura de contenido:
  1. Datos de la obra (10 campos)
  2. Predicción por objetivo (desvío, banda, probabilidad, IC80%, valor final est.)
  3. Atribución SHAP (costo y plazo)
  4. Análisis de contexto de gestión (si el usuario lo completó)
  5. Episodio documentado (si es una obra del histórico)
"""
from __future__ import annotations
from io import BytesIO
from datetime import datetime

# --- Etiquetas legibles de los 10 campos de entrada ---------------------------
CAMPO_LABEL = {
    'sup_m2': 'Superficie (m2)', 'niveles': 'Niveles', 'unidades': 'Unidades',
    'presupuesto_inicial': 'Presupuesto inicial (USD)', 'tiempo_inicial': 'Plazo inicial (días)',
    'sistema_constructivo': 'Sistema constructivo', 'nivel_acabado': 'Nivel de acabado',
    'avance_proyecto': 'Avance del proyecto (%)', 'proyectos_similares': 'Proyectos similares del equipo',
    'fecha_inicio': 'Fecha de inicio',
}
CAUSA_NOMBRE = {
    'alcance': 'Cambio de alcance', 'diseño': 'Error u omisión de diseño',
    'sitio': 'Condición de sitio', 'proveedor': 'Proveedor / suministro',
    'normativa': 'Ajuste normativo', 'clima': 'Clima',
}
DIMS = [('costo', 'desvio_costo', 'Desvío de costo', 'presupuesto_final_est', 'Presupuesto final est. (USD)'),
        ('tiempo', 'desvio_tiempo', 'Desvío de plazo', 'tiempo_final_est_dias', 'Plazo final est. (días)')]


def _pct(v):
    return f"{'+' if v > 0 else ''}{v:.1f}%"


# ══════════════════════════════════════════════════════════════════════════════
# EXCEL  (openpyxl)
# ══════════════════════════════════════════════════════════════════════════════
def build_excel(project: dict, pred: dict, exp: dict, contexto=None, episodio=None) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment

    wb = Workbook()
    head_fill = PatternFill('solid', fgColor='1A1A2E')
    head_font = Font(bold=True, color='FFFFFF')
    title_font = Font(bold=True, size=13, color='1A1A2E')

    def _headerrow(ws, row, cols):
        for i, c in enumerate(cols, 1):
            cell = ws.cell(row=row, column=i, value=c)
            cell.fill, cell.font = head_fill, head_font

    # — Hoja 1: Resumen (proyecto + predicción) —
    ws = wb.active
    ws.title = 'Resumen'
    ws['A1'] = 'DesviAI — Reporte de predicción'
    ws['A1'].font = title_font
    ws['A2'] = f"Generado {datetime.now():%d/%m/%Y %H:%M}"
    ws['A2'].font = Font(italic=True, color='888888')

    ws['A4'] = 'Datos de la obra'
    ws['A4'].font = Font(bold=True, size=11)
    _headerrow(ws, 5, ['Campo', 'Valor'])
    r = 6
    for k, label in CAMPO_LABEL.items():
        ws.cell(row=r, column=1, value=label)
        ws.cell(row=r, column=2, value=project.get(k))
        r += 1

    r += 1
    ws.cell(row=r, column=1, value='Predicción del modelo').font = Font(bold=True, size=11)
    r += 1
    _headerrow(ws, r, ['Objetivo', 'Desvío est.', 'Banda', 'Prob. desvío alto', 'IC80%', 'Valor final est.'])
    r += 1
    for dim, tgt, titulo, final_key, _ in DIMS:
        d = pred[dim]
        ws.cell(row=r, column=1, value=titulo)
        ws.cell(row=r, column=2, value=_pct(d['desvio_estimado_pct']))
        ws.cell(row=r, column=3, value=d['riesgo'])
        ws.cell(row=r, column=4, value=f"{round(d['probabilidad_alto'] * 100)}%")
        ws.cell(row=r, column=5, value=f"[{_pct(d['ic80_pct'][0])}, {_pct(d['ic80_pct'][1])}]")
        ws.cell(row=r, column=6, value=d[final_key])
        r += 1
    ws.column_dimensions['A'].width = 32
    for col in 'BCDEF':
        ws.column_dimensions[col].width = 18

    # — Hoja 2: SHAP —
    ws2 = wb.create_sheet('Atribución SHAP')
    row = 1
    for dim, tgt, titulo, *_ in DIMS:
        e = exp.get(tgt)
        if not e:
            continue
        ws2.cell(row=row, column=1, value=titulo).font = Font(bold=True, size=11)
        row += 1
        _headerrow(ws2, row, ['Variable', 'Contribución (pts %)', 'Efecto'])
        row += 1
        for c in e['contribuciones']:
            ws2.cell(row=row, column=1, value=c['variable'])
            ws2.cell(row=row, column=2, value=c['contribucion_pts'])
            ws2.cell(row=row, column=3, value='Aumenta' if c['sentido'] == 'sube' else 'Reduce')
            row += 1
        row += 1
    ws2.column_dimensions['A'].width = 34
    ws2.column_dimensions['B'].width = 20
    ws2.column_dimensions['C'].width = 12

    # — Hoja 3: Contexto de gestión (si existe) —
    if contexto:
        ws3 = wb.create_sheet('Contexto de gestión')
        ws3['A1'] = f"Riesgo de gestión: {contexto['banda']}  ·  índice {contexto['indice']} sobre 2"
        ws3['A1'].font = Font(bold=True, size=11)
        ws3['A2'] = f"riesgo base {contexto['riesgo_base']} × factor del equipo {contexto['factor_amplificador']}"
        _headerrow(ws3, 4, ['Factor', 'Nivel', 'Respuesta'])
        row = 5
        for clave, d in contexto['desglose'].items():
            ws3.cell(row=row, column=1, value=d.get('etiqueta', clave))
            ws3.cell(row=row, column=2, value=d['nivel'])
            ws3.cell(row=row, column=3, value=d['opcion_texto'])
            row += 1
        ws3.column_dimensions['A'].width = 34
        ws3.column_dimensions['B'].width = 10
        ws3.column_dimensions['C'].width = 60

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# PDF  (reportlab)
# ══════════════════════════════════════════════════════════════════════════════
def _safe(t: str) -> str:
    """La fuente estándar de reportlab no dibuja «²»; se pasa a «2» solo en PDF."""
    return str(t).replace('m²', 'm2').replace('²', '2')


def build_pdf(project: dict, pred: dict, exp: dict, contexto=None, episodio=None) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

    base = getSampleStyleSheet()
    st_title = ParagraphStyle('t', parent=base['Title'], fontSize=20, textColor=colors.HexColor('#1A1A2E'), spaceAfter=2)
    st_sub = ParagraphStyle('s', parent=base['Normal'], fontSize=9.5, textColor=colors.HexColor('#888888'), spaceAfter=2)
    st_h2 = ParagraphStyle('h2', parent=base['Heading2'], fontSize=13, textColor=colors.HexColor('#1A1A2E'), spaceBefore=14, spaceAfter=6)
    st_body = ParagraphStyle('b', parent=base['Normal'], fontSize=10, leading=14, spaceAfter=6)
    st_aviso = ParagraphStyle('a', parent=base['Normal'], fontSize=8.5, leading=12, textColor=colors.HexColor('#9A6700'))

    def _tbl(filas, widths, aligns=None):
        t = Table(filas, colWidths=widths)
        style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A1A2E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F4F5F7')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DDDDDD')),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]
        for col, a in (aligns or {}).items():
            style.append(('ALIGN', (col, 0), (col, -1), a))
        t.setStyle(TableStyle(style))
        return t

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm,
                            leftMargin=2.2 * cm, rightMargin=2.2 * cm)
    el = []
    el.append(Paragraph('DesviAI — Reporte de predicción', st_title))
    el.append(Paragraph(f"Generado el {datetime.now():%d/%m/%Y %H:%M}", st_sub))
    el.append(Paragraph(_safe(f"{project.get('sup_m2'):,} m² · {project.get('niveles')} niveles · "
                              f"{project.get('sistema_constructivo')} · acabado {project.get('nivel_acabado')}"), st_sub))
    el.append(Spacer(1, 6))
    el.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#DDDDDD')))

    # Datos de la obra
    el.append(Paragraph('Datos de la obra', st_h2))
    filas = [['Campo', 'Valor']] + [[_safe(lbl), _safe(project.get(k))] for k, lbl in CAMPO_LABEL.items()]
    el.append(_tbl(filas, [7.5 * cm, 8.5 * cm]))

    # Predicción
    el.append(Paragraph('Predicción del modelo', st_h2))
    filas = [['Objetivo', 'Desvío', 'Banda', 'Prob.', 'IC80%', 'Valor final est.']]
    for dim, tgt, titulo, final_key, _ in DIMS:
        d = pred[dim]
        filas.append([titulo, _pct(d['desvio_estimado_pct']), d['riesgo'],
                      f"{round(d['probabilidad_alto'] * 100)}%",
                      f"[{_pct(d['ic80_pct'][0])}, {_pct(d['ic80_pct'][1])}]",
                      f"{d[final_key]:,}"])
    el.append(_tbl(filas, [3.3 * cm, 2 * cm, 1.8 * cm, 1.6 * cm, 3.5 * cm, 3.8 * cm],
                   aligns={1: 'CENTER', 2: 'CENTER', 3: 'CENTER'}))

    # SHAP
    for dim, tgt, titulo, *_ in DIMS:
        e = exp.get(tgt)
        if not e:
            continue
        el.append(Paragraph(f'Atribución SHAP · {titulo.lower()}', st_h2))
        el.append(Paragraph(_safe(e['resumen']), st_body))
        filas = [['Variable', 'Contribución (pts %)', 'Efecto']]
        for c in e['contribuciones']:
            filas.append([_safe(c['variable']), f"{c['contribucion_pts']:+.2f}",
                          'Aumenta' if c['sentido'] == 'sube' else 'Reduce'])
        el.append(_tbl(filas, [8 * cm, 4 * cm, 4 * cm], aligns={1: 'CENTER', 2: 'CENTER'}))

    # Contexto de gestión
    if contexto:
        el.append(Paragraph('Análisis de contexto de gestión', st_h2))
        el.append(Paragraph(f"Riesgo de gestión: <b>{contexto['banda']}</b> · índice {contexto['indice']} sobre 2 "
                            f"(riesgo base {contexto['riesgo_base']} × factor del equipo {contexto['factor_amplificador']}).", st_body))
        filas = [['Factor', 'Nivel', 'Respuesta']]
        for clave, d in contexto['desglose'].items():
            filas.append([_safe(d.get('etiqueta', clave)), d['nivel'], _safe(d['opcion_texto'])])
        el.append(_tbl(filas, [4.5 * cm, 1.8 * cm, 9.7 * cm]))

    # Episodio
    if episodio and episodio.get('meta'):
        m = episodio['meta']
        el.append(Paragraph('Episodio documentado · evidencia directa', st_h2))
        cd = CAUSA_NOMBRE.get(m.get('causa_dominante'), m.get('causa_dominante'))
        el.append(Paragraph(
            f"Obra #{episodio.get('obra_id')} · causa dominante: <b>{cd}</b> · "
            f"desvío real costo {m.get('desvio_costo_real')}% · plazo {m.get('desvio_tiempo_real')}%.", st_body))

    # Aviso
    el.append(Spacer(1, 10))
    el.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#E0C000')))
    el.append(Spacer(1, 4))
    el.append(Paragraph(
        '<b>Aviso:</b> reporte de un prototipo (PoC). Las predicciones son orientativas, '
        'basadas en un modelo entrenado con datos parcialmente sintéticos. No reemplazan el '
        'juicio profesional ni un análisis presupuestario formal.', st_aviso))

    doc.build(el)
    return buf.getvalue()
