"""Validate the generated public tree before it replaces the previous build."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET


class Page(HTMLParser):
    def __init__(self,markup):
        super().__init__();self.links=[];self.resources=[];self.ids=[];self.h1=0;self.feed(markup)
    def handle_starttag(self,tag,attributes):
        attributes=dict(attributes)
        if attributes.get('id'):self.ids.append(attributes['id'])
        if tag=='h1':self.h1+=1
        if tag=='a' and 'href' in attributes:self.links.append(attributes['href'])
        if tag in {'img','script','iframe','source'} and attributes.get('src'):self.resources.append(attributes['src'])
        if tag=='link' and attributes.get('rel') in {'stylesheet','icon','alternate icon','preload'}:self.resources.append(attributes.get('href',''))


def check(output,articles,posts,settings):
    origin='https://draveronicasoto.es'
    manifest_path=output/'manifest.json'
    if manifest_path.exists():
        declared=json.loads(manifest_path.read_text(encoding='utf-8'))
        actual={path.relative_to(output).as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in output.rglob('*') if path.is_file() and path!=manifest_path}
        if declared!=actual:raise ValueError('Output manifest does not match generated tree')
    pages={}
    for path in sorted(output.rglob('*.html')):
        route='/'+path.relative_to(output).as_posix()
        if route.endswith('/index.html'):route=route[:-10]
        if route=='/index.html':route='/'
        markup=path.read_text(encoding='utf-8');pages[route]=(path,markup,Page(markup))
    for route,(path,markup,page) in pages.items():
        if len(page.ids)!=len(set(page.ids)):raise ValueError('Duplicate page ID: '+route)
        for resource in page.resources:
            if resource.startswith('data:'):continue
            if not resource.startswith('/') or resource.startswith('//') or not (output/resource.lstrip('/')).is_file():
                raise ValueError('Missing or remote page resource: '+route+' '+resource)
        for link in page.links:
            parsed=urlsplit(link)
            if parsed.scheme or parsed.netloc:continue
            target=unquote(parsed.path) or route
            if not target.startswith('/'):raise ValueError('Relative internal link: '+route)
            target_path=output/target.lstrip('/')
            if not target_path.exists():raise ValueError('Missing internal link: '+route+' '+target)
            if parsed.fragment and target in pages and unquote(parsed.fragment) not in pages[target][2].ids:
                raise ValueError('Missing fragment: '+route+' '+link)
        for payload in re.findall(r'<script type="application/ld\+json">(.*?)</script>',markup,re.S):json.loads(payload)
        if route.endswith('/'):
            if page.h1!=1:raise ValueError('Canonical page must have exactly one h1: '+route)
            if f'rel="canonical" href="{origin}{route}"' not in markup:raise ValueError('Wrong canonical: '+route)
            if 'href="/assets/favicon.svg"' not in markup:raise ValueError('Missing favicon: '+route)
    published=[article for article in articles if article['published']]
    home=pages['/'][1];index=pages['/articulos/'][1]
    for article in articles:
        route='/'+article['slug']+'/'
        if article['published']:
            if route not in pages:raise ValueError('Published article missing')
            if route not in pages['/articulos/'][2].links or route not in pages['/'][2].links:raise ValueError('Published article missing from discovery')
            markup=pages[route][1]
            if article['body'] not in markup:raise ValueError('Article body changed')
            schema=json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',markup,re.S)[1])
            if schema['headline']!=article['title'] or schema['url']!=origin+route:raise ValueError('Article schema differs from content')
            if article.get('date','')!=schema.get('datePublished',''):raise ValueError('Article publication date changed')
        elif route in pages or route in pages['/articulos/'][2].links or route in pages['/'][2].links:
            raise ValueError('Unpublished article leaked into generated pages')
    namespace={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
    sitemap=ET.fromstring((output/'sitemap.xml').read_text(encoding='utf-8'))
    locations=[node.text for node in sitemap.findall('s:url/s:loc',namespace)]
    expected={origin+route for route in settings['sitemapStaticRoutes']}|{origin+'/'+article['slug']+'/' for article in published}
    if set(locations)!=expected or len(locations)!=len(expected):raise ValueError('Sitemap differs from published pages')
    if home.count('role="tab"')!=len(settings['categories']) or home.count('role="tabpanel"')!=len(settings['categories']):raise ValueError('Explorer taxonomy mismatch')
    visible_posts=[post for post in posts if post['published']]
    if home.count('class="post-card"')!=len(visible_posts):raise ValueError('Instagram card mismatch')
    for post in visible_posts:
        if post['url'] not in pages['/'][2].links:raise ValueError('Instagram destination missing')
    if (output/'CNAME').read_text(encoding='utf-8').strip()!='draveronicasoto.es':raise ValueError('Custom domain changed')
    for alias in settings['legacyAliases']:
        if not (output/alias).is_file():raise ValueError('Legacy alias missing')
    return {'pages':len(pages),'articles':len(published),'instagram_cards':len(visible_posts),'legacy_aliases':len(settings['legacyAliases'])}


if __name__=='__main__':
    from build_site import ROOT,article_documents,instagram_documents,read_json
    settings=read_json(ROOT/'site/settings.json')
    print(json.dumps(check(ROOT/'_site',article_documents(ROOT,settings),instagram_documents(ROOT),settings),indent=2))
