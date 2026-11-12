# Dra. Verónica Soto — web divulgativa y fuente editorial

La web se genera desde los artículos y las tarjetas de Instagram de este repositorio. GitHub Actions valida el contenido y publica únicamente el artefacto _site en GitHub Pages, conservando draveronicasoto.es.

## Qué se edita

- content/articles/<slug>.json: título, resumen, categoría, cuerpo, fecha editorial, imagen opcional y visibilidad.
- content/instagram/<identificador>.json: enlace de Instagram, título, portada local, alternativa, orden y visibilidad. Portada manual; no hay sincronización automática con Instagram.
- site/templates/ y site/static/: plantillas y recursos del diseño; no son campos de edición habitual.
- .pages.yml: configuración del editor externo Pages CMS. Instalación y acceso de cada editora se gestionan por separado; este archivo no contiene contraseñas.

El panel escribe cambios en el repositorio. Guardar inicia la validación y publicación; comprobar el resultado en Actions y en la URL pública. Si falla la validación, la versión pública anterior se conserva.

## Reglas editoriales

Conservar el identificador URL de los artículos publicados. Las altas requieren fecha editorial real YYYY-MM-DD, no futura. No completar fechas históricas desconocidas ni convertir publicación en revisión médica.

published:false excluye el contenido de páginas, índice, portada y sitemap. No hace privado un borrador en este repositorio público ni su historial. No introducir pacientes, consentimientos, datos clínicos privados, contraseñas ni material confidencial. Las imágenes públicas siguen siendo públicas aunque su artículo no se publique.

No se puede retirar un artículo mientras otro contenido público siga enlazándolo: la compilación falla y mantiene la versión anterior. Consultar origen y destino en el error de Actions, localizar referencias por identificador URL y resolverlas con una decisión editorial antes de volver a publicar. Si la referencia procede de una plantilla, solicitar ajuste técnico. No sustituir enlaces clínicos silenciosamente por el índice.

Imágenes nuevas en site/static/assets/articulos/: PNG, JPEG o WebP, con alternativa y derechos de uso. El generador comprueba formato y dimensiones; no determina derechos ni sustituye revisión visual. El cuerpo admite HTML editorial limitado, sin scripts, eventos, estilos ni recursos remotos.

## Construcción y comprobación

Con Python 3.12.14 y sin paquetes externos:

    python tools/build_site.py
    python tools/check_site.py
    python tools/test_editorial.py

La prueba editorial usa una copia temporal. La compilación valida toda la entrada antes de sustituir _site; los recursos históricos se protegen por inventario en site/settings.json.

Los HTML y recursos antiguos de la raíz se conservan como referencia de la migración estática. La fuente vigente es content/ y site/; modificar aquellos HTML no actualiza la publicación de Actions. El commit 5e61787 conserva la entrega estática anterior para recuperación.

Rutas /<slug>/; los alias .html heredados usan redirección HTML inmediata, no HTTP301. Información divulgativa que no sustituye valoración profesional. Créditos y licencias en /creditos/ y los archivos de licencias de los recursos.
