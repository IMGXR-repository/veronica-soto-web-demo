"""Portable editorial build. Python standard library only; no network or credentials."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import datetime as dt
import hashlib
import html
import json
import re
import shutil
import struct
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://draveronicasoto.es'
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')
ARTICLE_TAGS = {'p','h2','h3','h4','ul','ol','li','a','strong','em','br','sup','sub','div','blockquote','img'}
ARTICLE_CLASSES = {'q','a','sum','summary','close','closing','auth','author','rh','refs','up','top','related','faq'}
IMAGE_EXTENSIONS = {'.jpg':'jpeg','.jpeg':'jpeg','.png':'png','.webp':'webp'}


def read_json(path):
    def unique_pairs(pairs):
        fields = {}
        for key, field in pairs:
            if key in fields:
                raise ValueError(f'Duplicate JSON field: {path.name}: {key}')
            fields[key] = field
        return fields
    document=json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique_pairs)
    if not isinstance(document,dict):
        raise ValueError('Editorial JSON must be an object: '+path.name)
    return document


def json_script(document):
    return json.dumps(document, ensure_ascii=False).replace('<', '\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')


def escaped(text):
    return html.escape(text, quote=True)


def safe_url(url):
    if not isinstance(url,str) or not url or any(ord(char)<33 for char in url) or '\\' in url:
        raise ValueError('Unsafe URL')
    decoded = unquote(url)
    if any(ord(char)<33 for char in decoded) or '\\' in decoded:
        raise ValueError('Unsafe encoded URL')
    parsed = urlsplit(url)
    if parsed.username or parsed.password or parsed.netloc and parsed.scheme!='https':
        raise ValueError('Unsafe URL authority')
    if url.startswith('/') and not url.startswith('//'):
        if any(part in {'.','..'} for part in urlsplit(decoded).path.split('/')):
            raise ValueError('Unsafe URL path')
    elif parsed.scheme!='https' or not parsed.hostname or parsed.port not in {None,443}:
        raise ValueError('Only local absolute paths and HTTPS URLs are allowed')
    return url


class SafeBody(HTMLParser):
    def __init__(self, body):
        super().__init__(convert_charrefs=False)
        self.stack = []
        self.feed(body)
        self.close()
        if self.stack:
            raise ValueError('Unclosed article HTML')

    def handle_starttag(self, tag, attributes):
        if tag not in ARTICLE_TAGS:
            raise ValueError('Forbidden article element: '+tag)
        if len({key for key,_ in attributes})!=len(attributes):
            raise ValueError('Duplicate HTML attribute')
        for key, attribute in attributes:
            if key=='class' and attribute and all(token in ARTICLE_CLASSES for token in attribute.split()):
                continue
            if tag=='a' and key=='href':
                safe_url(attribute)
                continue
            if tag=='img' and key=='src' and attribute.startswith('/assets/articulos/'):
                safe_url(attribute)
                continue
            if tag=='img' and key=='alt' and attribute:
                continue
            if tag=='img' and key in {'width','height'} and attribute.isdigit() and 0<int(attribute)<=12000:
                continue
            raise ValueError('Forbidden article attribute: '+key)
        if tag=='img' and not {'src','alt'} <= dict(attributes).keys():
            raise ValueError('Article image requires local src and alt')
        if tag not in {'br','img'}:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attributes):
        if tag not in {'br','img'}:
            raise ValueError('Invalid self-closing article element')
        self.handle_starttag(tag,attributes)

    def handle_endtag(self, tag):
        if not self.stack or self.stack.pop()!=tag:
            raise ValueError('Invalid article HTML nesting')

    def handle_comment(self, comment):
        raise ValueError('Comments are not editorial content')

    def handle_pi(self, instruction):
        raise ValueError('Processing instructions are not editorial content')

    def handle_decl(self, declaration):
        raise ValueError('Declarations are not editorial content')


def jpeg_dimensions(payload):
    if not payload.startswith(b'\xff\xd8') or not payload.endswith(b'\xff\xd9'):
        raise ValueError('Invalid JPEG structure')
    offset=2
    while offset+4<=len(payload):
        if payload[offset]!=255:
            raise ValueError('Invalid JPEG marker')
        marker=payload[offset+1];offset+=2
        if marker in {0xd8,0xd9}:
            continue
        length=int.from_bytes(payload[offset:offset+2],'big')
        if length<2 or offset+length>len(payload):
            raise ValueError('Truncated JPEG segment')
        if marker in {0xc0,0xc1,0xc2,0xc3,0xc5,0xc6,0xc7,0xc9,0xca,0xcb,0xcd,0xce,0xcf}:
            return int.from_bytes(payload[offset+5:offset+7],'big'),int.from_bytes(payload[offset+3:offset+5],'big')
        offset+=length
    raise ValueError('JPEG dimensions missing')


def image_dimensions(path):
    payload=path.read_bytes()
    if len(payload)>20*1024*1024:
        raise ValueError('Editorial image exceeds 20 MB')
    image_type=IMAGE_EXTENSIONS.get(path.suffix.lower())
    if image_type=='png' and payload.startswith(b'\x89PNG\r\n\x1a\n') and payload[12:16]==b'IHDR' and payload.endswith(b'IEND\xaeB`\x82'):
        dimensions=struct.unpack('>II',payload[16:24])
    elif image_type=='jpeg':
        dimensions=jpeg_dimensions(payload)
    elif image_type=='webp' and payload[:4]==b'RIFF' and payload[8:12]==b'WEBP' and int.from_bytes(payload[4:8],'little')+8==len(payload):
        if payload[12:16]==b'VP8X':
            dimensions=(int.from_bytes(payload[24:27],'little')+1,int.from_bytes(payload[27:30],'little')+1)
        elif payload[12:16]==b'VP8 ' and payload[23:26]==b'\x9d\x01\x2a':
            dimensions=(int.from_bytes(payload[26:28],'little')&0x3fff,int.from_bytes(payload[28:30],'little')&0x3fff)
        elif payload[12:16]==b'VP8L' and payload[20:21]==b'\x2f':
            bits=int.from_bytes(payload[21:25],'little');dimensions=((bits&0x3fff)+1,((bits>>14)&0x3fff)+1)
        else:
            raise ValueError('Unsupported WebP frame')
    else:
        raise ValueError('Image extension does not match PNG/JPEG/WebP payload')
    if not all(0<dimension<=12000 for dimension in dimensions):
        raise ValueError('Image dimensions outside supported range')
    return dimensions


def local_image(root, image):
    if not isinstance(image,str) or not re.fullmatch(r'/assets/(?:[a-zA-Z0-9_-]+/)*[a-zA-Z0-9_.-]+\.(?:jpg|jpeg|png|webp)',image):
        raise ValueError('Image must be a local raster asset')
    path=root/'site/static'/image.lstrip('/')
    if not path.is_file() or path.is_symlink():
        raise ValueError('Missing image')
    return image_dimensions(path)


def required_text(document, key):
    if not isinstance(document.get(key),str) or not document[key].strip():
        raise ValueError('Missing editorial text field: '+key)
    return document[key]


def validate_date(article, imported):
    date=article.get('date','')
    if article['slug'] in imported:
        if date!=imported[article['slug']]['date']:
            raise ValueError('Imported historical date is protected; request a reviewed migration')
        return
    if not isinstance(date,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',date):
        raise ValueError('New articles require a real ISO editorial date')
    if dt.date.fromisoformat(date)>dt.date.today():
        raise ValueError('Future publication dates are not supported')


def article_documents(root, settings):
    articles=[];slugs=set();categories={category['id'] for category in settings['categories']}
    reserved=set(settings['reservedRoutes']);imported=settings['importedArticles']
    for path in sorted((root/'content/articles').glob('*.json')):
        article=read_json(path);slug=required_text(article,'slug')
        if not SLUG.fullmatch(slug) or slug!=path.stem or slug in slugs or slug in reserved:
            raise ValueError('Article slug is unsafe, duplicated, renamed or reserved: '+path.name)
        slugs.add(slug)
        for key in ['title','excerpt','body','category']:
            required_text(article,key)
        if article['category'] not in categories or type(article.get('published')) is not bool:
            raise ValueError('Invalid article category or published state: '+slug)
        validate_date(article,imported);SafeBody(article['body'])
        if article.get('image'):
            local_image(root,article['image']);required_text(article,'image_alt')
        article['editorialOrder']=imported.get(slug,{}).get('order',100000)
        article['latestOrder']=imported.get(slug,{}).get('latestOrder',-1)
        articles.append(article)
    if not set(imported)<=slugs:
        raise ValueError('Imported slugs cannot be deleted or renamed; use published:false')
    return articles


def instagram_documents(root):
    posts=[]
    for path in sorted((root/'content/instagram').glob('*.json')):
        post=read_json(path)
        if not SLUG.fullmatch(path.stem):
            raise ValueError('Unsafe Instagram identifier')
        for key in ['title','image','image_alt','url']:
            required_text(post,key)
        parsed=urlsplit(safe_url(post['url']))
        if parsed.scheme!='https' or parsed.hostname not in {'instagram.com','www.instagram.com'} or not parsed.path.startswith('/'):
            raise ValueError('Instagram URL host must be exact')
        if type(post.get('published')) is not bool or type(post.get('order')) is not int:
            raise ValueError('Invalid Instagram order or publication state')
        local_image(root,post['image']);post['id']=path.stem;posts.append(post)
    return sorted(posts,key=lambda post:(post['order'],post['id']))


def validate_static(root, settings):
    static=root/'site/static';editorial=static/'assets/articulos'
    if any(path.is_symlink() for path in static.rglob('*')):
        raise ValueError('Symlinked static resources are forbidden')
    actual={path.relative_to(static).as_posix() for path in static.rglob('*') if path.is_file()}
    added=actual-set(settings['staticManifest'])
    if any(not name.startswith('assets/articulos/') for name in added):
        raise ValueError('Unregistered static resource')
    for name,digest in settings['staticManifest'].items():
        path=static/name
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise ValueError('Static resource changed without reviewed migration: '+name)
    if editorial.exists():
        for path in editorial.rglob('*'):
            if path.is_symlink() or path.is_dir() or not re.fullmatch(r'[a-zA-Z0-9_.-]+\.(?:jpg|jpeg|png|webp)',path.name):
                raise ValueError('Unsafe editorial upload')
            image_dimensions(path)


def template(root,name,replacements):
    markup=(root/'site/templates'/name).read_text(encoding='utf-8')
    for key,replacement in replacements.items():
        if markup.count('{{'+key+'}}')!=1:
            raise ValueError('Template marker missing or duplicated: '+key)
        markup=markup.replace('{{'+key+'}}',replacement)
    if re.search(r'\{\{[A-Z_]+\}\}',markup):
        raise ValueError('Unresolved template marker')
    return markup


def article_markup(root, article, settings):
    url=ORIGIN+'/'+article['slug']+'/'
    schema=dict(settings['articleSchema']);schema.update(headline=article['title'],description=article['excerpt'],url=url)
    if article.get('date'):
        schema['datePublished']=article['date']
    reviewed=settings['importedArticles'].get(article['slug'],{}).get('reviewedMonth')
    if reviewed:
        schema['lastReviewed']=reviewed
    else:
        schema.pop('reviewedBy',None)
    legacy=settings['importedArticles'].get(article['slug'],{})
    prefix=legacy.get('prefix','')
    image=''
    if article.get('image'):
        width,height=local_image(root,article['image'])
        image=f'<img class="article-cover" src="{escaped(article["image"])}" alt="{escaped(article["image_alt"])}" width="{width}" height="{height}">'
    return template(root,'article.html',{'TITLE':escaped(article['title']+' | Dra. Verónica Soto'),'DESCRIPTION':escaped(article['excerpt']),'OG_TITLE':escaped(article['title']+' | Dra. Verónica Soto'),'OG_DESCRIPTION':escaped(article['excerpt']),'CANONICAL':url,'OG_URL':url,'SCHEMA':json_script(schema),'ARTICLE_OPEN':'<article class="medical-body">' if legacy.get('articleClass','medical-body') else '<article>','PREFIX':prefix,'HEADING':escaped(article['title']),'COVER':image,'BODY':article['body']})


def grouped_articles(articles, settings):
    return [(category,[article for article in articles if article['category']==category['id']]) for category in settings['categories']]


def index_markup(root, articles, settings):
    navigation=[];groups=[]
    for number,(category,members) in enumerate(grouped_articles(articles,settings),1):
        key=category['id'];label=escaped(category['label'])
        navigation.append(f'<a href="#{key}"><span aria-hidden="true">{number:02}</span>{label}<span aria-hidden="true">↗</span></a>')
        links=''.join('<li><a href="/'+article['slug']+'/">'+escaped(article['title'])+'<small>'+escaped(article['excerpt'])+'</small></a></li>\n' for article in members)
        groups.append(f'<section class="zone-group zone-{key}" aria-labelledby="{key}"><div class="zone-heading"><span class="zone-number" aria-hidden="true">{number:02}</span><h2 class="zone" id="{key}">{label}</h2></div><ul class="index">\n{links}</ul></section>')
    return template(root,'index-articles.html',{'ZONE_NAVIGATION':''.join(navigation),'ZONE_COLLECTION':''.join(groups)})


def explorer_markup(articles,settings):
    tabs=[];panels=[]
    for position,(category,members) in enumerate(grouped_articles(articles,settings)):
        key=category['id'];label=escaped(category['label'])
        tabs.append(f'<button type="button" role="tab" id="area-{key}" aria-controls="panel-{key}" aria-selected="{str(position==0).lower()}" tabindex="{0 if position==0 else -1}">{position+1:02} <span>{label}</span> ↗</button>')
        links=''.join('<li><a href="/'+article['slug']+'/">'+escaped(article['title'])+' ↗</a></li>' for article in members)
        panels.append(f'<article role="tabpanel" id="panel-{key}" aria-labelledby="area-{key}" tabindex="0"><p class="reading-guide"><span aria-hidden="true">↓</span> Lee sobre este tema</p><span class="tag">LECTURAS SOBRE EL DOLOR</span><h3>{label}</h3><ul class="article-links">{links}</ul></article>')
    return '<div class="explorer"><div role="tablist" aria-label="Áreas de valoración" aria-orientation="vertical" hidden>'+''.join(tabs)+'</div><div id="area-panel">'+''.join(panels)+'</div></div>'


def latest_markup(articles):
    latest=sorted(articles,key=lambda article:(article.get('date',''),article['latestOrder']==-1,-article['latestOrder'],article['slug']),reverse=True)[:3]
    if not latest:
        return ''
    links=''.join('<li><a href="/'+article['slug']+'/">'+escaped(article['title'])+' ↗</a></li>' for article in latest)
    return '<section class="new-readings" aria-labelledby="nuevas-lecturas"><p class="tag">NUEVO ARTÍCULO</p><h2 id="nuevas-lecturas">Nuevas lecturas</h2><ul>'+links+'</ul><a href="/articulos/">Todos los artículos ↗</a></section>'


def instagram_markup(root, posts):
    cards=[]
    for post in posts:
        width,height=local_image(root,post['image'])
        cards.append(f'<a class="post-card" href="{escaped(post["url"])}" target="_blank" rel="noopener noreferrer"><img width="{width}" height="{height}" src="{escaped(post["image"])}" alt="{escaped(post["image_alt"])}" loading="lazy"><span>{escaped(post["title"])} <b>↗</b></span><small>{escaped(post.get("caption","Ver publicación en Instagram"))}</small></a>')
    return ''.join(cards)


def write_page(stage, route, markup):
    path=stage/route.strip('/')/'index.html' if route!='/' else stage/'index.html'
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(markup,encoding='utf-8',newline='')


def write_sitemap(stage,articles,settings):
    namespace='http://www.sitemaps.org/schemas/sitemap/0.9';ET.register_namespace('',namespace)
    tree=ET.Element('{'+namespace+'}urlset')
    for route in settings['sitemapStaticRoutes']+['/'+article['slug']+'/' for article in articles]:
        node=ET.SubElement(tree,'{'+namespace+'}url');ET.SubElement(node,'{'+namespace+'}loc').text=ORIGIN+route
    (stage/'sitemap.xml').write_bytes(ET.tostring(tree,encoding='utf-8',xml_declaration=True)+b'\n')


def render_site(root,stage,settings,articles,posts):
    shutil.copytree(root/'site/static',stage,dirs_exist_ok=True)
    published=[article for article in articles if article['published']]
    published.sort(key=lambda article:(article['editorialOrder'],article['slug']))
    for article in published:
        write_page(stage,'/'+article['slug']+'/',article_markup(root,article,settings))
    write_page(stage,'/articulos/',index_markup(root,published,settings))
    home=template(root,'home.html',{'EXPLORER':explorer_markup(published,settings),'LATEST':latest_markup(published),'INSTAGRAM':instagram_markup(root,[post for post in posts if post['published']])})
    write_page(stage,'/',home);write_sitemap(stage,published,settings)
    for slug in settings['importedArticles']:
        alias=stage/(slug+'.html')
        if alias.exists() and not next(article['published'] for article in articles if article['slug']==slug):
            alias.write_text('<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Artículos</title><link rel="canonical" href="'+ORIGIN+'/articulos/"><meta http-equiv="refresh" content="0; url=/articulos/"></head><body><a href="/articulos/">Todos los artículos</a></body></html>',encoding='utf-8')


def build(root=ROOT):
    settings=read_json(root/'site/settings.json')
    validate_static(root,settings)
    articles=article_documents(root,settings);posts=instagram_documents(root)
    output=root/'_site'
    with tempfile.TemporaryDirectory(prefix='.build-',dir=root) as scratch:
        stage=Path(scratch)/'output';stage.mkdir()
        render_site(root,stage,settings,articles,posts)
        from check_site import check
        check(stage,articles,posts,settings)
        manifest={path.relative_to(stage).as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(stage.rglob('*')) if path.is_file()}
        (stage/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='')
        backup=Path(scratch)/'previous'
        if output.exists():output.rename(backup)
        try:
            stage.rename(output)
        except OSError:
            if backup.exists():backup.rename(output)
            raise
    return manifest


if __name__=='__main__':
    manifest=build()
    print(json.dumps({'files':len(manifest),'manifest_sha256':hashlib.sha256(json.dumps(manifest,indent=2).encode()+b'\n').hexdigest()}))
