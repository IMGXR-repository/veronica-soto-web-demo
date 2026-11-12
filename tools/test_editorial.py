"""Exercise editorial state changes and reject unsafe content in an isolated source copy."""
from pathlib import Path
import copy
import datetime as dt
import hashlib
import json
import shutil
import tempfile
import unittest

from build_site import ROOT, build, read_json


class EditorialLifecycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch=tempfile.TemporaryDirectory(prefix='cms-editorial-tests-')
        cls.root=Path(cls.scratch.name)/'portable'
        shutil.copytree(ROOT,cls.root,ignore=shutil.ignore_patterns('_site','__pycache__','.build-*'))
        cls.article_path=cls.root/'content/articles/prueba-editorial.json'
        cls.post_path=cls.root/'content/instagram/prueba-instagram.json'
        cls.article={'slug':'prueba-editorial','title':'Prueba <editorial> & título','excerpt':'Resumen de prueba para comprobar la publicación editorial.','body':'<p>Contenido de prueba <strong>editable</strong>.</p>','category':'tratamientos','date':dt.date.today().isoformat(),'published':False,'image':'','image_alt':''}
        cls.post={'title':'Publicación de prueba','url':'https://www.instagram.com/p/prueba/','image':'/assets/instagram-hombro.webp','image_alt':'Portada de prueba','order':0,'published':False}

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    def write_json(self,path,document):
        path.write_text(json.dumps(document,ensure_ascii=False),encoding='utf-8')

    def manifest_digest(self):
        return hashlib.sha256((self.root/'_site/manifest.json').read_bytes()).hexdigest()

    def assert_rejected_without_output_change(self,document):
        self.write_json(self.article_path,document)
        before=self.manifest_digest()
        with self.assertRaises((ValueError,TypeError,KeyError,FileNotFoundError)):
            build(self.root)
        self.assertEqual(before,self.manifest_digest())
        self.article_path.unlink()

    def test_01_article_create_edit_publish_withdraw_restore(self):
        baseline=build(self.root)
        self.write_json(self.article_path,self.article);build(self.root)
        self.assertFalse((self.root/'_site/prueba-editorial').exists())
        published=copy.deepcopy(self.article);published['published']=True
        published['image']='/assets/instagram-hombro.webp';published['image_alt']='Imagen & alternativa'
        self.write_json(self.article_path,published);build(self.root)
        for relative in ['index.html','articulos/index.html','sitemap.xml']:
            self.assertIn('/prueba-editorial/',(self.root/'_site'/relative).read_text(encoding='utf-8'))
        page=(self.root/'_site/prueba-editorial/index.html').read_text(encoding='utf-8')
        self.assertIn('/prueba-editorial/',page)
        self.assertIn('/prueba-editorial/',(self.root/'_site/index.html').read_text(encoding='utf-8').split('id="nuevas-lecturas"')[1])
        self.assertIn('class="article-cover"',page);self.assertIn('Imagen &amp; alternativa',page)
        self.assertIn('Prueba &lt;editorial&gt; &amp; título',page)
        published['title']='Título editado';published['body']='<p>Contenido modificado.</p>'
        self.write_json(self.article_path,published);build(self.root)
        self.assertIn('Título editado',(self.root/'_site/index.html').read_text(encoding='utf-8'))
        self.assertIn('Contenido modificado.',(self.root/'_site/prueba-editorial/index.html').read_text(encoding='utf-8'))
        published['published']=False;self.write_json(self.article_path,published);build(self.root)
        self.assertFalse((self.root/'_site/prueba-editorial').exists())
        self.assertNotIn('/prueba-editorial/',(self.root/'_site/sitemap.xml').read_text(encoding='utf-8'))
        self.article_path.unlink();self.assertEqual(baseline,build(self.root))

    def test_02_instagram_create_edit_reorder_withdraw(self):
        baseline=build(self.root)
        self.write_json(self.post_path,self.post);build(self.root)
        self.assertNotIn(self.post['url'],(self.root/'_site/index.html').read_text(encoding='utf-8'))
        post=copy.deepcopy(self.post);post['published']=True;self.write_json(self.post_path,post);build(self.root)
        home=(self.root/'_site/index.html').read_text(encoding='utf-8')
        self.assertEqual(home.count('class="post-card"'),7)
        self.assertLess(home.index(post['url']),home.index('https://www.instagram.com/dra_veronica_soto/p/DefJdzNkR__/'))
        post.update(title='Título Instagram editado',order=99);self.write_json(self.post_path,post);build(self.root)
        home=(self.root/'_site/index.html').read_text(encoding='utf-8')
        self.assertIn('Título Instagram editado',home)
        self.assertGreater(home.index(post['url']),home.index('https://www.instagram.com/dra_veronica_soto/p/DefJdzNkR__/'))
        post['published']=False;self.write_json(self.post_path,post);build(self.root)
        self.assertNotIn(post['url'],(self.root/'_site/index.html').read_text(encoding='utf-8'))
        self.post_path.unlink();self.assertEqual(baseline,build(self.root))

    def test_03_zero_and_one_instagram_card(self):
        originals={path:path.read_bytes() for path in (self.root/'content/instagram').glob('*.json')}
        try:
            for path in originals:
                post=read_json(path);post['published']=False;self.write_json(path,post)
            build(self.root);self.assertEqual((self.root/'_site/index.html').read_text(encoding='utf-8').count('class="post-card"'),0)
            first=next(iter(originals));post=read_json(first);post['published']=True;self.write_json(first,post)
            build(self.root);self.assertEqual((self.root/'_site/index.html').read_text(encoding='utf-8').count('class="post-card"'),1)
        finally:
            for path,payload in originals.items():path.write_bytes(payload)
        build(self.root)

    def test_04_determinism_and_jsonld_escaping(self):
        self.assertEqual(build(self.root),build(self.root))
        article=copy.deepcopy(self.article);article.update(published=True,title='Título </script><script>alert(1)</script>')
        self.write_json(self.article_path,article);build(self.root)
        page=(self.root/'_site/prueba-editorial/index.html').read_text(encoding='utf-8')
        self.assertNotIn('<script>alert(1)</script>',page);self.assertIn('\\u003c/script>',page)
        self.article_path.unlink();build(self.root)

    def test_05_invalid_articles_leave_last_output_unchanged(self):
        build(self.root)
        invalid_changes=[
            {'slug':'../escape'},{'slug':'articulos'},{'slug':'slug-renombrado'},
            {'category':'inexistente'},{'date':''},{'date':'2026-02-30'},
            {'date':(dt.date.today()+dt.timedelta(days=1)).isoformat()},
            {'published':'true'},{'body':'<script>alert(1)</script>'},
            {'body':'<iframe src="https://example.com"></iframe>'},
            {'body':'<p onclick="alert(1)">Texto</p>'},
            {'body':'<a href="javascript:alert(1)">Enlace</a>'},
            {'body':'<a href="//example.com">Enlace</a>'},
            {'body':'<a href="https://user:pass@example.com/">Enlace</a>'},
            {'body':'<a href="/assets/%2e%2e/escape">Enlace</a>'},
            {'body':'<a href="https://example.com" href="javascript:alert(1)">Enlace</a>'},
            {'body':'<h1>Título duplicado</h1>'},{'body':'<p><strong>Mal cierre</p></strong>'},
            {'body':'<img src="https://example.com/a.png" alt="Remota">'},
            {'image':'/assets/favicon.svg','image_alt':'SVG'},
            {'image':'/assets/instagram-hombro.webp','image_alt':''},
            {'body':'<p><a href="/ruta-que-no-existe/">Enlace roto</a></p>'},
        ]
        for changes in invalid_changes:
            with self.subTest(changes=changes):
                article=copy.deepcopy(self.article);article.update(changes,published=changes.get('published',True))
                self.assert_rejected_without_output_change(article)

    def test_06_upload_type_and_unknown_static(self):
        build(self.root)
        editorial=self.root/'site/static/assets/articulos';editorial.mkdir(exist_ok=True)
        before=self.manifest_digest()
        for filename,payload in [('ejecutable.svg',b'<svg/>'),('falso.png',b'<svg/>'),('roto.jpg',b'\xff\xd8\xff\xd9')]:
            with self.subTest(filename=filename):
                path=editorial/filename;path.write_bytes(payload)
                with self.assertRaises(ValueError):build(self.root)
                self.assertEqual(before,self.manifest_digest());path.unlink()
        path=editorial/'valida.webp';shutil.copyfile(self.root/'site/static/assets/instagram-hombro.webp',path)
        build(self.root);self.assertTrue((self.root/'_site/assets/articulos/valida.webp').is_file());path.unlink()
        intruder=self.root/'site/static/intruso.js';intruder.write_text('alert(1)',encoding='utf-8')
        with self.assertRaises(ValueError):build(self.root)
        intruder.unlink();build(self.root)

    def test_07_instagram_host_validation(self):
        for url in ['http://www.instagram.com/p/x/','https://www.instagram.com.evil.test/p/x/','https://user@www.instagram.com/p/x/','javascript:alert(1)']:
            with self.subTest(url=url):
                post=copy.deepcopy(self.post);post['url']=url;self.write_json(self.post_path,post)
                with self.assertRaises(ValueError):build(self.root)
                self.post_path.unlink()

    def test_08_protected_legacy_dates_slugs_and_duplicate_json(self):
        path=self.root/'content/articles/epicondilitis.json';original=path.read_bytes();article=read_json(path)
        try:
            article['date']='2026-11-12';self.write_json(path,article)
            with self.assertRaises(ValueError):build(self.root)
            path.write_bytes(original);renamed=path.with_name('renombrado.json');path.rename(renamed)
            with self.assertRaises(ValueError):build(self.root)
            renamed.rename(path)
        finally:
            path.write_bytes(original)
        self.article_path.write_text('{"slug":"prueba-editorial","slug":"duplicado"}',encoding='utf-8')
        with self.assertRaises(ValueError):build(self.root)
        self.article_path.unlink();build(self.root)


if __name__=='__main__':
    unittest.main(verbosity=2)
