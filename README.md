# CMS portable — fuente local

Esta carpeta contiene una fuente autocontenida: 29 artículos, seis tarjetas Instagram y los recursos de la candidata R2. No requiere baselines, el proyecto histórico ni paquetes Python externos. No se ha instalado Pages CMS ni cambiado GitHub Pages.

Desde esta carpeta, con Python 3.12.14:

```text
python tools/build_site.py
python tools/check_site.py
python tools/test_editorial.py
```

El primer comando valida toda la entrada y genera `_site`. Si hay un error, conserva la salida anterior. El segundo comprueba rutas, enlaces, fragmentos, recursos, metadatos y sincronía editorial. El tercero prueba el ciclo editorial en una copia temporal, sin modificar los documentos de esta carpeta.

## Edición

Artículos: `content/articles/<slug>.json`. El título, resumen, categoría, cuerpo e imagen opcional se generan en la web. El identificador debe coincidir con el fichero; no se cambia al retitular. El cuerpo admite párrafos, subtítulos h2–h4, listas, enlaces HTTPS o internos, negrita, cursiva, citas e imágenes locales PNG/JPEG/WebP con alternativa. No admite HTML ejecutable, estilos o recursos remotos. La imagen de cabecera exige alternativa y aparece antes del cuerpo.

Las once categorías están en `site/settings.json`. Las altas requieren una fecha editorial real `YYYY-MM-DD` que no sea futura. Las fechas importadas, incluso cuando solo consta el mes o no consta fecha, se conservan; no se rellenan con el día de importación. El formulario deja el campo como texto para conservar esa precisión. El generador aplica la regla de altas. Los artículos nuevos no reciben una declaración automática de revisión médica. La fecha de publicación editorial corresponde al día real de publicación y es distinta del mes o fecha de revisión médica. Los 16 artículos aún no publicados se preparan para el 13-11-2026; si el despliegue pasa a otro día, revisar esa fecha antes de publicar sin alterar la revisión médica.

`published: false` excluye el artículo del árbol HTML, del índice, del explorador, de destacados y del sitemap. Si otros artículos o bloques de la web todavía enlazan ese destino, el build falla y conserva la salida anterior. Localiza las referencias mediante el slug, resuélvelas con una decisión editorial y vuelve a compilar antes de despublicar. El generador no redirige automáticamente esos enlaces al índice. Un borrador en un repositorio público sigue siendo público en Git y su historial. No introducir pacientes, datos clínicos, consentimientos o material confidencial. El build no publica los JSON editoriales, pero los recursos cargados en la carpeta pública son públicos aunque su artículo sea borrador.

Instagram: `content/instagram/<identificador>.json`. Título, URL de instagram.com exacta, portada local con derechos de uso y alternativa, orden entero y estado publicado. La portada se carga manualmente; la web no consulta Instagram. Empate por orden: identificador del fichero. Se admiten cero, una o múltiples tarjetas. El carrusel mantiene sus recursos y comportamiento originales con varias tarjetas.

Las nuevas imágenes se guardan en `site/static/assets/articulos/`. Solo raster PNG/JPEG/WebP, hasta 20 MB y 12000 píxeles por dimensión; extensión y estructura de cabecera coherentes. SVG y ficheros desconocidos se rechazan. Esta comprobación no determina derechos ni sustituye revisión visual de la imagen.

Los recursos históricos se protegen por hash en `site/settings.json`; cambios de diseño o archivos estáticos requieren una migración revisada de ese inventario. No se sobrescriben para editar artículos o tarjetas.

## Servicio pendiente de activación

`.pages.yml` y `.github/workflows/publish.yml` son propuestas locales. Activar exige revisión independiente de esta salida, aprobación de proveedor/permisos de la App y migración concreta del repositorio de publicación, conservando dominio y fuente Pages. El workflow compila y comprueba antes de subir exclusivamente `_site`; el deploy depende del build. No contiene PAT, claves de navegador ni integración pública del CMS.

Tras activar, guardar contenido hace commit y lanza un build. Un guardado no acredita despliegue: comprobar el resultado del workflow y la URL pública. Si falla, corregir la entrada; la versión pública anterior sigue desplegada. La experiencia real del editor —incluida conservación de HTML al abrir/guardar y permisos de colaboradoras— sigue pendiente de prueba en servicio.
