# Probar DesviAI con Docker (sin instalar Python)

Esta es la forma más sencilla de ejecutar el prototipo: no necesitas instalar Python, ni
dependencias, ni configurar nada. Todo corre aislado dentro de un contenedor.

## Requisito único

**Docker Desktop** — descárgalo gratis de https://www.docker.com/products/docker-desktop/
e instálalo (en Windows/Mac es un instalador normal). Ábrelo una vez para que arranque.

## Pasos

1. Obtén el proyecto: clónalo con git o descomprime el `.zip` que te enviaron.
2. Abre una terminal **en la carpeta del proyecto** (la que contiene el archivo `Dockerfile`).
3. Ejecuta:

   ```
   docker compose up --build
   ```

   > La **primera vez tarda unos minutos**: descarga la imagen base, instala las librerías y
   > entrena el modelo dentro del contenedor. Las siguientes veces es casi instantáneo.

4. Cuando en la terminal aparezca:

   ```
   Starting development server at http://0.0.0.0:8200/
   ```

   abre en el navegador:

   ```
   http://localhost:8200
   ```

5. **Login:** es una demo — cualquier correo y contraseña te dejan entrar.

## Qué probar

- **Nueva predicción** → completa el formulario → *Analizar con el modelo* → verás el reporte
  real (score de riesgo contextual, desvío de costo y plazo, SHAP, casos similares).
- **Chat** con el agente (botón "Abrir agente conversacional"): pregúntale por los drivers,
  la fiabilidad o cómo mitigar el riesgo; verás la traza de herramientas que consulta.
- En el **historial**, abre una obra marcada con "● episodio" para ver la **evidencia directa**
  (órdenes de cambio) y pregúntale al agente *"¿por qué se desvió esta obra?"*.
- **Diagrama de arquitectura:** http://localhost:8200/arquitectura.html

## Detener

- En la terminal: **Ctrl + C**, y luego:

  ```
  docker compose down
  ```

## Notas

- No instala nada en tu sistema aparte de la imagen de Docker (la puedes borrar después con
  `docker compose down --rmi all`).
- El agente funciona en **modo demo** (respuestas deterministas, sin coste ni claves).
