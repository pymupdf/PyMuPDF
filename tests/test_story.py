import pymupdf
import os
import textwrap


def test_story():
    otf = os.path.abspath(f'{__file__}/../resources/PragmaticaC.otf')
    # 2023-12-06: latest mupdf throws exception if path uses back-slashes.
    otf = otf.replace('\\', '/')
    CSS = f"""
        @font-face {{font-family: test; src: url({otf});}}
    """

    HTML = """
    <p style="font-family: test;color: blue">We shall meet again at a place where there is no darkness.</p>
    """

    MEDIABOX = pymupdf.paper_rect("letter")
    WHERE = MEDIABOX + (36, 36, -36, -36)
    # the font files are located in /home/chinese
    arch = pymupdf.Archive(".")
    # if not specfied user_css, the output pdf has content
    story = pymupdf.Story(HTML, user_css=CSS, archive=arch)  

    writer = pymupdf.DocumentWriter("output.pdf")

    more = 1

    while more:
        device = writer.begin_page(MEDIABOX)
        more, _ = story.place(WHERE)
        story.draw(device)
        writer.end_page()

    writer.close()


def test_2753():
    
    def rectfn(rect_num, filled):
        return pymupdf.Rect(0, 0, 200, 200), pymupdf.Rect(50, 50, 100, 100), None
    
    def make_pdf(html, path_out):
        story = pymupdf.Story(html=html)
        document = story.write_with_links(rectfn)
        print(f'Writing to: {path_out=}.')
        document.save(path_out)
        return document
    
    doc_before = make_pdf(
            textwrap.dedent('''
                <p>Before</p>
                <p style="page-break-before: always;"></p>
                <p>After</p>
                '''),
            os.path.abspath(f'{__file__}/../../tests/test_2753-out-before.pdf'),
            )
        
    doc_after = make_pdf(
            textwrap.dedent('''
                <p>Before</p>
                <p style="page-break-after: always;"></p>
                <p>After</p>
                '''),
            os.path.abspath(f'{__file__}/../../tests/test_2753-out-after.pdf'),
            )
    
    assert len(doc_before) == 2
    assert len(doc_after) == 2


springer_html = '''
<article>
<aside>
<img src="springer.jpg">
<br><i>Michael Springer ist Schriftsteller und Wis&#173;sen&#173;schafts&#173;publizist. Eine Sammlung seiner Einwürfe ist 2019 als Buch unter dem Titel <b>»Lauter Überraschungen. Was die Wis&#173;senschaft weitertreibt«</b> erschienen.<br><a>www.spektrum.de/artikel/2040277</a></i>
</aside>
<h1>SPRINGERS EINWÜRFE: INTIME VERBINDUNGEN</h1>

<h2>Wieso kann unsereins so vieles, was eine Maus nicht kann? Unser Gehirn ist nicht bloß größer, sondern vor allem überraschend vertrackt verdrahtet.</h2>

<p>Der Heilige Gral der Neu&#173;ro&#173;wis&#173;sen&#173;schaft ist die komplette Kartierung des menschlichen Gehirns – die ge&#173;treue Ab&#173;bildung des Ge&#173;strüpps der Nervenzellen mit den baum&#173;för&#173;mi&#173;gen Ver&#173;ästel&#173;ungen der aus ihnen sprie&#173;ßen&#173;den Den&#173;dri&#173;ten und den viel län&#173;ge&#173;ren Axo&#173;nen, wel&#173;che oft der Sig&#173;nal&#173;über&#173;tragung von einem Sin&#173;nes&#173;or&#173;gan oder zu einer Mus&#173;kel&#173;fa&#173;ser die&#173;nen. Zum Gesamtbild gehören die winzigen Knötchen auf den Dendriten; dort sitzen die Synapsen. Das sind Kontakt- und Schalt&#173;stel&#173;len, leb&#173;haf&#173;te Ver&#173;bin&#173;dungen zu anderen Neuronen.</p>

<p>Dieses Dickicht bis zur Ebene einzelner Zel&#173;len zu durchforsten und es räumlich dar&#173;zu&#173;stel&#173;len, ist eine gigantische Aufgabe, die bis vor Kurzem utopisch anmuten musste. Neu&#173;er&#173;dings vermag der junge For&#173;schungs&#173;zweig der Konnektomik (von Englisch: con&#173;nect für ver&#173;bin&#173;den) das Zusammenspiel der Neurone immer besser zu verstehen. Das gelingt mit dem Einsatz dreidimensionaler Elek&#173;tro&#173;nen&#173;mik&#173;ros&#173;ko&#173;pie. Aus Dünn&#173;schicht&#173;auf&#173;nah&#173;men von zerebralen Ge&#173;we&#173;be&#173;pro&#173;ben lassen sich plastische Bil&#173;der ganzer Zellverbände zu&#173;sam&#173;men&#173;setzen.</p>

<p>Da frisches menschliches Hirn&#173;ge&#173;we&#173;be nicht ohne Wei&#173;te&#173;res zu&#173;gäng&#173;lich ist – in der Regel nur nach chirurgischen Eingriffen an Epi&#173;lep&#173;sie&#173;pa&#173;tien&#173;ten –, hält die Maus als Mo&#173;dell&#173;or&#173;ga&#173;nis&#173;mus her. Die evolutionäre Ver&#173;wandt&#173;schaft von Mensch und Nager macht die Wahl plau&#173;sibel. Vor allem das Team um Moritz Helmstaedter am Max-Planck-Institut (MPI) für Hirnforschung in Frankfurt hat in den ver&#173;gangenen Jahren Expertise bei der kon&#173;nek&#173;tomischen Analyse entwickelt.</p>

<p>Aber steckt in unserem Kopf bloß ein auf die tausendfache Neu&#173;ro&#173;nen&#173;an&#173;zahl auf&#173;ge&#173;bläh&#173;tes Mäu&#173;se&#173;hirn? Oder ist menschliches Ner&#173;ven&#173;ge&#173;we&#173;be viel&#173;leicht doch anders gestrickt? Zur Beantwortung dieser Frage unternahm die MPI-Gruppe einen detaillierten Vergleich von Maus, Makake und Mensch (Science 377, abo0924, 2022).</p>

<p>Menschliches Gewebe stammte diesmal nicht von Epileptikern, son&#173;dern von zwei wegen Hirntumoren operierten Patienten. Die For&#173;scher wollten damit vermeiden, dass die oft jahrelange Behandlung mit An&#173;ti&#173;epi&#173;lep&#173;ti&#173;ka das Bild der synaptischen Verknüpfungen trübte. Sie verglichen die Proben mit denen eines Makaken und von fünf Mäusen.</p>

<p>Einerseits ergaben sich – einmal ab&#173;ge&#173;se&#173;hen von den ganz of&#173;fen&#173;sicht&#173;li&#173;chen quan&#173;titativen Unterschieden wie Hirngröße und Neu&#173;ro&#173;nen&#173;anzahl – recht gute Über&#173;ein&#173;stim&#173;mun&#173;gen, die somit den Gebrauch von Tier&#173;modellen recht&#173;fer&#173;ti&#173;gen. Doch in einem Punkt erlebte das MPI-Team eine echte Über&#173;raschung.</p>

<p>Gewisse Nervenzellen, die so genannten In&#173;ter&#173;neurone, zeichnen sich dadurch aus, dass sie aus&#173;schließ&#173;lich mit anderen Ner&#173;ven&#173;zel&#173;len in&#173;ter&#173;agieren. Solche »Zwi&#173;schen&#173;neu&#173;rone« mit meist kurzen Axonen sind nicht primär für das Verarbeiten externer Reize oder das Aus&#173;lösen körperlicher Reaktionen zuständig; sie be&#173;schäf&#173;ti&#173;gen sich bloß mit der Ver&#173;stär&#173;kung oder Dämpfung interner Signale.</p>

<p>Just dieser Neuronentyp ist nun bei Makaken und Menschen nicht nur mehr als doppelt so häufig wie bei Mäusen, sondern obendrein be&#173;son&#173;ders intensiv untereinander ver&#173;flochten. Die meisten Interneurone kop&#173;peln sich fast ausschließlich an ihresgleichen. Dadurch wirkt sich ihr konnektomisches Ge&#173;wicht ver&#173;gleichs&#173;weise zehnmal so stark aus.</p>

<p>Vermutlich ist eine derart mit sich selbst be&#173;schäf&#173;tigte Sig&#173;nal&#173;ver&#173;ar&#173;beitung die Vor&#173;be&#173;ding&#173;ung für ge&#173;stei&#173;gerte Hirn&#173;leis&#173;tungen. Um einen Ver&#173;gleich mit verhältnismäßig pri&#173;mi&#173;ti&#173;ver Tech&#173;nik zu wagen: Bei küns&#173;tli&#173;chen neu&#173;ro&#173;na&#173;len Netzen – Algorithmen nach dem Vor&#173;bild verknüpfter Nervenzellen – ge&#173;nü&#173;gen schon ein, zwei so genannte ver&#173;bor&#173;ge&#173;ne Schich&#173;ten von selbst&#173;be&#173;züg&#173;li&#173;chen Schaltstellen zwischen Input und Output-Ebene, um die ver&#173;blüf&#173;fen&#173;den Erfolge der künstlichen Intel&#173;ligenz her&#173;vor&#173;zu&#173;bringen.</p>
</article>
'''
def test_fit_springer():
    
    if not hasattr(pymupdf, 'mupdf'):
        print(f'test_fit_springer(): not running on classic.')
        return
    
    story = pymupdf.Story(springer_html)
    
    def check(call, expected):
        '''
        Checks that eval(call) returned parameter=expected. Also creates PDF
        using path that contains `call` in its leafname,
        '''
        fit_result = eval(call)
        
        print(f'test_fit_springer(): {call=} => {fit_result=}.')
        if expected is None:
            assert not fit_result.big_enough
        else:
            document = story.write_with_links(lambda rectnum, filled: (fit_result.rect, fit_result.rect, None))
            path = os.path.abspath(f'{__file__}/../../tests/test_fit_springer_{call}_{fit_result.parameter=}_{fit_result.rect=}.pdf')
            document.save(path)
            print(f'Have saved document to {path}.')
            assert abs(fit_result.parameter-expected) < 0.001, f'{expected=} {fit_result.parameter=}'
    
    check('story.fit_scale(pymupdf.Rect(0, 0, 200, 200), scale_min=1, verbose=1)', 3.685728073120117)
    check('story.fit_scale(pymupdf.Rect(0, 0, 595, 842), scale_min=1, verbose=1)', 1.0174560546875)
    check('story.fit_scale(pymupdf.Rect(0, 0, 300, 421), scale_min=1, verbose=1)', 2.02752685546875)
    check('story.fit_scale(pymupdf.Rect(0, 0, 600, 900), scale_min=1, scale_max=1, verbose=1)', 1)
    
    check('story.fit_height(20, verbose=1)', 10782.3291015625)
    check('story.fit_height(200, verbose=1)', 2437.4990234375)
    check('story.fit_height(2000, verbose=1)', 450.2998046875)
    check('story.fit_height(5000, verbose=1)', 378.2998046875)
    check('story.fit_height(5500, verbose=1)', 378.2998046875)
    
    check('story.fit_width(3000, verbose=1)', 167.30859375)
    check('story.fit_width(2000, verbose=1)', 239.595703125)
    check('story.fit_width(1000, verbose=1)', 510.85546875)
    check('story.fit_width(500, verbose=1)', 1622.1272945404053)
    check('story.fit_width(400, verbose=1)', 2837.507724761963)
    check('story.fit_width(300, width_max=200000, verbose=1)', None)
    check('story.fit_width(200, width_max=200000, verbose=1)', None)

    # Run without verbose to check no calls to log() - checked by assert.
    check('story.fit_scale(pymupdf.Rect(0, 0, 600, 900), scale_min=1, scale_max=1, verbose=0)', 1)
    check('story.fit_scale(pymupdf.Rect(0, 0, 300, 421), scale_min=1, verbose=0)', 2.02752685546875)


def test_write_stabilized_with_links():

    def rectfn(rect_num, filled):
        '''
        We return one rect per page.
        '''
        rect = pymupdf.Rect(10, 20, 290, 380)
        mediabox = pymupdf.Rect(0, 0, 300, 400)
        #print(f'rectfn(): rect_num={rect_num} filled={filled}')
        return mediabox, rect, None

    def contentfn(positions):
        ret = ''
        ret += textwrap.dedent('''
                <!DOCTYPE html>
                <body>
                <h2>Contents</h2>
                <ul>
                ''')
        for position in positions:
            if position.heading and (position.open_close & 1):
                text = position.text if position.text else ''
                if position.id:
                    ret += f'    <li><a href="#{position.id}">{text}</a>'
                else:
                    ret += f'    <li>{text}'
                ret += f' page={position.page_num}\n'
        ret += '</ul>\n'
        ret += textwrap.dedent(f'''
                <h1>First section</h1>
                <p>Contents of first section.
                <ul>
                <li>External <a href="https://artifex.com/">link to https://artifex.com/</a>.
                <li><a href="#idtest">Link to IDTEST</a>.
                <li><a href="#nametest">Link to NAMETEST</a>.
                </ul>
            
                <h1>Second section</h1>
                <p>Contents of second section.
                <h2>Second section first subsection</h2>
            
                <p>Contents of second section first subsection.
                <p id="idtest">IDTEST
            
                <h1>Third section</h1>
                <p>Contents of third section.
                <p><a name="nametest">NAMETEST</a>.
            
                </body>
                ''')
        return ret.strip()
    
    document = pymupdf.Story.write_stabilized_with_links(contentfn, rectfn)
    
    # Check links.
    links = list()
    for page in document:
        links += page.get_links()
    print(f'{len(links)=}.')
    external_links = dict()
    for i, link in enumerate(links):
        print(f'    {i}: {link=}')
        if link.get('kind') == pymupdf.LINK_URI:
            uri = link['uri']
            external_links.setdefault(uri, 0)
            external_links[uri] += 1

    # Check there is one external link.
    print(f'{external_links=}')
    if hasattr(pymupdf, 'mupdf'):
        assert len(external_links) == 1
        assert 'https://artifex.com/' in external_links
    
    out_path = __file__.replace('.py', '.pdf')
    document.save(out_path)
    
def test_archive_creation():
    s = pymupdf.Story(archive=pymupdf.Archive('.'))
    s = pymupdf.Story(archive='.')
