"""
Exract page text in various formats.
No checks performed - just contribute to code coverage.
"""
import os
import sys

import pymupdf

pymupdfdir = os.path.abspath(f'{__file__}/../..')
scriptdir = f'{pymupdfdir}/tests'
filename = os.path.join(scriptdir, "resources", "symbol-list.pdf")


def test_extract1():
    doc = pymupdf.open(filename)
    page = doc[0]
    text = page.get_text("text")
    blocks = page.get_text("blocks")
    words = page.get_text("words")
    d1 = page.get_text("dict")
    d2 = page.get_text("json")
    d3 = page.get_text("rawdict")
    d3 = page.get_text("rawjson")
    text = page.get_text("html")
    text = page.get_text("xhtml")
    text = page.get_text("xml")
    rects = pymupdf.get_highlight_selection(page, start=page.rect.tl, stop=page.rect.br)
    text = pymupdf.ConversionHeader("xml")
    text = pymupdf.ConversionTrailer("xml")

def _test_extract2():
    import sys
    import time
    path = f'{scriptdir}/../../PyMuPDF-performance/adobe.pdf'
    if not os.path.exists(path):
        print(f'test_extract2(): not running becase does not exist: {path}')
        return
    doc = pymupdf.open( path)
    for opt in (
            'dict',
            'dict2',
            'text',
            'blocks',
            'words',
            'html',
            'xhtml',
            'xml',
            'json',
            'rawdict',
            'rawjson',
            ):
        for flags in None, pymupdf.TEXTFLAGS_TEXT:
            t0 = time.time()
            for page in doc:
                page.get_text(opt, flags=flags)
            t = time.time() - t0
            print(f't={t:.02f}: opt={opt} flags={flags}')
            sys.stdout.flush()

def _test_extract3():
    import sys
    import time
    path = f'{scriptdir}/../../PyMuPDF-performance/adobe.pdf'
    if not os.path.exists(path):
        print(f'test_extract3(): not running becase does not exist: {path}')
        return
    doc = pymupdf.open( path)
    t0 = time.time()
    for page in doc:
        page.get_text('json')
    t = time.time() - t0
    print(f't={t}')
    sys.stdout.flush()
    
def test_extract4():
    '''
    Rebased-specific.
    '''
    if not hasattr(pymupdf, 'mupdf'):
        return
    path = f'{pymupdfdir}/tests/resources/2.pdf'
    document = pymupdf.open(path)
    page = document[4]
    
    out = 'test_stext.html'
    text = page.get_text('html')
    with open(out, 'w') as f:
        f.write(text)
    print(f'Have written to: {out}')
    
    out = 'test_extract.html'
    writer = pymupdf.mupdf.FzDocumentWriter(
            out,
            'html',
            pymupdf.mupdf.FzDocumentWriter.OutputType_DOCX,
            )
    device = pymupdf.mupdf.fz_begin_page(writer, pymupdf.mupdf.fz_bound_page(page))
    pymupdf.mupdf.fz_run_page(page, device, pymupdf.mupdf.FzMatrix(), pymupdf.mupdf.FzCookie())
    pymupdf.mupdf.fz_end_page(writer)
    pymupdf.mupdf.fz_close_document_writer(writer)
    print(f'Have written to: {out}')
    
    if pymupdf.mupdf_version_tuple >= (1, 23, 4):
        def get_text(page, space_guess):
            buffer_ = pymupdf.mupdf.FzBuffer( 10)
            out = pymupdf.mupdf.FzOutput( buffer_)
            writer = pymupdf.mupdf.FzDocumentWriter(
                    out,
                    'text,space-guess={space_guess}',
                    pymupdf.mupdf.FzDocumentWriter.OutputType_DOCX,
                    )
            device = pymupdf.mupdf.fz_begin_page(writer, pymupdf.mupdf.fz_bound_page(page))
            pymupdf.mupdf.fz_run_page(page, device, pymupdf.mupdf.FzMatrix(), pymupdf.mupdf.FzCookie())
            pymupdf.mupdf.fz_end_page(writer)
            pymupdf.mupdf.fz_close_document_writer(writer)
            text = buffer_.fz_buffer_extract()
            text = text.decode('utf8')
            n = text.count(' ')
            print(f'{space_guess=}: {n=}')
            return text, n
        page = document[4]
        text0, n0 = get_text(page, 0)
        text1, n1 = get_text(page, 0.5)
        text2, n2 = get_text(page, 0.001)
        text2, n2 = get_text(page, 0.1)
        text2, n2 = get_text(page, 0.3)
        text2, n2 = get_text(page, 0.9)
        text2, n2 = get_text(page, 5.9)
        assert text1 == text0

def test_2954():
    '''
    Check handling of unknow unicode characters, issue #2954, fixed in
    mupdf-1.23.9 with addition of FZ_STEXT_USE_CID_FOR_UNKNOWN_UNICODE.
    '''
    path = os.path.abspath(f'{__file__}/../../tests/resources/test_2954.pdf')
    flags0 = (0
            | pymupdf.TEXT_PRESERVE_WHITESPACE
            | pymupdf.TEXT_PRESERVE_LIGATURES
            | pymupdf.TEXT_MEDIABOX_CLIP
            )
    
    document = pymupdf.Document(path)
    
    expected_good = (
            "IT-204-IP (2021) Page 3 of 5\nNYPA2514    12/06/21\nPartner's share of \n"
            " modifications (see instructions)\n20\n State additions\nNumber\n"
            "A ' Total amount\nB '\n State allocated amount\n"
            "EA '\n20a\nEA '\n20b\nEA '\n20c\nEA '\n20d\nEA '\n20e\nEA '\n20f\n"
            "Total addition modifications (total of column A, lines 20a through 20f)\n"
            ". . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . \n"
            "21\n21\n22\n State subtractions\n"
            "Number\nA ' Total amount\nB '\n State allocated amount\n"
            "ES '\n22a\nES '\n22b\nES '\n22c\nES '\n22d\nES '\n22e\nES '\n22f\n23\n23\n"
            "Total subtraction modifications (total of column A, lines 22a through 22f). . . . . . . . . . . . . . . . . . . . . . . . . . . . \n"
            "Additions to itemized deductions\n24\nAmount\n"
            "Letter\n"
            "24a\n24b\n24c\n24d\n24e\n24f\n"
            "Total additions to itemized deductions (add lines 24a through 24f)\n"
            ". . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . \n"
            "25\n25\n"
            "Subtractions from itemized deductions\n"
            "26\nLetter\nAmount\n26a\n26b\n26c\n26d\n26e\n26f\n"
            "Total subtractions from itemized deductions (add lines 26a through 26f) . . . . . . . . . . . . . . . . . . . . . . . . . . . . \n"
            "27\n27\n"
            "This line intentionally left blank. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . \n"
            "28\n28\n118003213032\n"
            )
    
    def check_good(text):
        '''
        Returns true if `text` is approximately the same as `expected_good`.

        2024-01-09: MuPDF master and 1.23.x give slightly different 'good'
        output, differing in a missing newline. So we compare without newlines.
        '''
        return text.replace('\n', '') == expected_good.replace('\n', '')
    
    n_fffd_good = 0
    n_fffd_bad = 749
    
    def get(flags=None):
        text = [page.get_text(flags=flags) for page in document]
        assert len(text) == 1
        text = text[0]
        n_fffd = text.count(chr(0xfffd))
        if 0:
            # This print() fails on Windows with UnicodeEncodeError.
            print(f'{flags=} {n_fffd=} {text=}')
        return text, n_fffd
    
    text_none, n_fffd_none = get()
    text_0, n_fffd_0 = get(flags0)
    
    if pymupdf.mupdf_version_tuple >= (1, 23, 9):
        text_1, n_fffd_1 = get(flags0 | pymupdf.TEXT_CID_FOR_UNKNOWN_UNICODE)
        
        assert n_fffd_none == n_fffd_good
        assert n_fffd_0 == n_fffd_bad
        assert n_fffd_1 == n_fffd_good
        
        assert check_good(text_none)
        assert not check_good(text_0)
        assert check_good(text_1)
    else:
        assert n_fffd_none == n_fffd_bad
        assert n_fffd_0 == n_fffd_bad
        
        assert not check_good(text_none)
        assert not check_good(text_0)


def test_3027():
    path = path = f'{pymupdfdir}/tests/resources/2.pdf'
    doc = pymupdf.open(path)
    page = doc[0]
    textpage = page.get_textpage()
    pymupdf.utils.get_text(page=page, option="dict", textpage=textpage)["blocks"]


def test_3186():

    texts_expected = [
            "Assicurazione sulla vita di tipo Unit Linked\nDocumento informativo precontrattuale aggiuntivo\nper i prodotti d\x00investimento assicurativi\n(DIP aggiuntivo IBIP)\nImpresa: AXA MPS Financial DAC                                                    \nProdotto: Progetto Protetto New - Global Dividends\nContratto Unit linked (Ramo III)\nData di realizzazione: Aprile 2023\nIl presente documento contiene informazioni aggiuntive e complementari rispetto a quelle presenti nel documento \ncontenente le informazioni chiave per i prodotti di investimento assicurativi (KID) per aiutare il potenziale \ncontraente a capire più nel dettaglio le caratteristiche del prodotto, gli obblighi contrattuali e la situazione \npatrimoniale dell\x00impresa.\nIl Contraente deve prendere visione delle condizioni d\x00assicurazione prima della sottoscrizione del Contratto.\nAXA MPS Financial DAC, Wolfe Tone House, Wolfe Tone Street, Dublin, DO1 HP90, Irlanda; Tel: 00353-1-6439100; \nsito internet: www.axa-mpsfinancial.ie; e-mail: supporto@axa-mpsfinancial.ie;\nAXA MPS Financial DAC, società del Gruppo Assicurativo AXA Italia, iscritta nell\x00Albo delle Imprese di assicurazione \ncon il numero II.00234. \nLa Compagnia mette a disposizione dei clienti i seguenti recapiti per richiedere eventuali informazioni sia in merito alla \nCompagnia sia in relazione al contratto proposto: Tel: 00353-1-6439100; sito internet:  www.axa-mpsfinancial.ie; \ne-mail: supporto@axa-mpsfinancial.ie;\nAXA MPS Financial DAC è un\x00impresa di assicurazione di diritto Irlandese, Sede legale 33 Sir John Rogerson's Quay, \nDublino D02 XK09 Irlanda. L\x00Impresa di Assicurazione è stata autorizzata all\x00esercizio dell\x00attività assicurativa con \nprovvedimento n. C33602 emesso dalla Central Bank of Ireland (l\x00Autorità di vigilanza irlandese) in data 14/05/1999 \ned è iscritta in Irlanda presso il Companies Registration Office (registered nr. 293822). \nLa Compagnia opera in Italia esclusivamente in regime di libera prestazione di servizi ai sensi dell\x00art. 24 del D. Lgs. \n07/09/2005, n. 209 e può investire in attivi non consentiti dalla normativa italiana in materia di assicurazione sulla \nvita, ma in conformità con la normativa irlandese di riferimento in quanto soggetta al controllo della Central Bank of \nIreland.\nCon riferimento all\x00ultimo bilancio d\x00esercizio (esercizio 2021) redatto ai sensi dei principi contabili vigenti, il patrimonio \nnetto di AXA MPS Financial DAC ammonta a 139,6 milioni di euro di cui 635 mila euro di capitale sociale interamente \nversato e 138,9 milioni di euro di riserve patrimoniali compreso il risultato di esercizio.\nAl 31 dicembre 2021 il Requisito patrimoniale di solvibilità è pari a 90 milioni di euro (Solvency Capital Requirement, \nSCR). Sulla base delle valutazioni effettuate della Compagnia coerentemente con gli esistenti dettami regolamentari, il \nRequisito patrimoniale minimo al 31 dicembre 2021 ammonta a 40 milioni di euro (Minimum Capital Requirement, \nMCR).\nL'indice di solvibilità di AXA MPS Financial DAC, ovvero l'indice che rappresenta il rapporto tra l'ammontare del margine \ndi solvibilità disponibile e l'ammontare del margine di solvibilità richiesto dalla normativa vigente, e relativo all'ultimo \nbilancio approvato, è pari al   304% (solvency ratio). L'importo dei fondi propri ammissibili a copertura dei requisiti \npatrimoniali è pari a 276 milioni di euro (Eligible Own Funds, EOF).\nPer informazioni patrimoniali sulla società è possibile consultare il sito: www.axa-mpsfinancial.ie/chi-siamo\nSi rinvia alla relazione sulla solvibilità e sulla condizione finanziaria dell\x00impresa (SFCR) disponibile sul sito internet \ndella Compagnia al seguente link www.axa-mpsfinancial.ie/comunicazioni   \nAl contratto si applica la legge italiana\nDIP aggiuntivo IBIP - Progetto Protetto New - Global Dividends -   Pag. 1 di 9\n",
            "Quali sono le prestazioni?\nIl contratto prevede le seguenti prestazioni:\na)Prestazioni in caso di vita dell'assicurato\nPrestazione in caso di Riscatto Totale e parziale\nA condizione che siano trascorsi almeno 30 giorni dalla Data di Decorrenza (conclusione del Contratto) e fino all\x00ultimo \nGiorno Lavorativo della terzultima settimana precedente la data di scadenza, il Contraente può riscuotere, interamente \no parzialmente, il Valore di Riscatto. In caso di Riscatto totale, la liquidazione del Valore di Riscatto pone fine al \nContratto con effetto dalla data di ricezione della richiesta.\nIl Contraente ha inoltre la facoltà di esercitare parzialmente il diritto di Riscatto, nella misura minima di 500,00 euro, \nda esercitarsi con le stesse modalità previste per il Riscatto totale. In questo caso, il Contratto rimane in vigore per \nl\x00ammontare residuo, a condizione che il Controvalore delle Quote residue del Contratto non sia inferiore a 1.000,00 \neuro.\nb) Prestazione a Scadenza\nAlla data di scadenza, sempre che l\x00Assicurato sia in vita, l\x00Impresa di Assicurazione corrisponderà agli aventi diritto un \nammontare risultante dal Controvalore delle Quote collegate al Contratto alla scadenza, calcolato come prodotto tra il \nValore Unitario della Quota (rilevato in corrispondenza della data di scadenza) e il numero delle Quote attribuite al \nContratto alla medesima data.\nc) Prestazione in corso di Contratto\nPurché l\x00assicurato sia in vita, nel corso della durata del Contratto, il Fondo Interno mira alla corresponsione di due \nPrestazioni Periodiche. Le prestazioni saranno pari all\x00ammontare risultante dalla moltiplicazione tra il numero di Quote \nassegnate al Contratto il primo giorno Lavorativo della settimana successiva alla Data di Riferimento e 2,50% del \nValore Unitario della Quota registrato alla Data di istituzione del Fondo Interno.\nLe prestazioni verranno liquidate entro trenta giorni dalle Date di Riferimento.\nData di Riferimento\n 1° Prestazione Periodica\n24/04/2024\n 2° Prestazione Periodica\n23/04/2025\nLa corresponsione delle Prestazioni Periodiche non è collegata alla performance positiva o ai ricavi incassati dal Fondo \nInterno, pertanto, la corresponsione potrebbe comportare una riduzione del Controvalore delle Quote senza comportare \nalcuna riduzione del numero di Quote assegnate al Contratto.\nd) Prestazione assicurativa principale in caso di decesso dell'Assicurato\nIn caso di decesso dell\x00Assicurato nel corso della durata contrattuale, è previsto il pagamento ai Beneficiari di un \nimporto pari al Controvalore delle Quote attribuite al Contratto, calcolato come prodotto tra il Valore Unitario della \nQuota rilevato alla Data di Valorizzazione della settimana successiva alla data in cui la notifica di decesso \ndell\x00Assicurato perviene all\x00Impresa di Assicurazione e il numero delle Quote attribuite al Contratto alla medesima data, \nmaggiorato di una percentuale pari allo 0,1%.\nQualora il capitale così determinato fosse inferiore al Premio pagato, sarà liquidato un ulteriore importo pari alla \ndifferenza tra il Premio pagato, al netto della parte di Premio riferita a eventuali Riscatti parziali e l\x00importo caso morte \ncome sopra determinato. Tale importo non potrà essere in ogni caso superiore al 5% del Premio pagato.\nOpzioni contrattuali\nIl Contratto non prevede opzioni contrattuali.\nFondi Assicurativi\nLe prestazioni di cui sopra sono collegate, in base all\x00allocazione del premio come descritto alla sezione \x01Quando e \ncome devo pagare?\x02, al valore delle quote del Fondo Interno denominato PP27 Global Dividends.\nil Fondo interno mira al raggiungimento di un Obiettivo di Protezione del Valore Unitario di Quota, tramite il \nconseguimento di un Valore Unitario di Quota a scadenza almeno pari al 100% del valore di quota registrato alla Data \ndi istituzione dal Fondo Interno.\nIl regolamento di gestione del Fondo Interno è disponibile sul sito dell\x00Impresa di Assicurazione \nwww.axa-mpsfinancial.ie dove puo essere acquisito su supporto duraturo.\nDIP aggiuntivo IBIP - Progetto Protetto New - Global Dividends -   Pag. 2 di 9\n",
            'Che cosa NON è assicurato\nRischi esclusi\nIl rischio di decesso dell\x00Assicurato è coperto qualunque sia la causa, senza limiti territoriali e senza \ntenere conto dei cambiamenti di professione dell\x00Assicurato, ad eccezione dei seguenti casi:\n\x03 il decesso, entro i primi sette anni dalla data di decorrenza del Contratto, dovuto alla sindrome da \nimmunodeficienza acquisita (AIDS) o ad altra patologia ad essa associata;\n\x03 dolo del Contraente o del Beneficiario;\n\x03 partecipazione attiva dell\x00Assicurato a delitti dolosi;\n\x03 partecipazione dell\x00Assicurato a fatti di guerra, salvo che non derivi da obblighi verso lo Stato \nItaliano: in questo caso la garanzia può essere prestata su richiesta del Contraente, alle condizioni \nstabilite dal competente Ministero;\n\x03 incidente di volo, se l\x00Assicurato viaggia a bordo di un aeromobile non autorizzato al volo o con \npilota non titolare di brevetto idoneo e, in ogni caso, se viaggia in qualità di membro \ndell\x00equipaggio;\n\x03 suicidio, se avviene nei primi due anni dalla Data di Decorrenza del Contratto\nCi sono limiti di copertura?\nNon vi sono ulteriori informazioni rispetto al contenuto del KID.\nChe obblighi ho? Quali obblighi ha l\x00Impresa?\nCosa fare in caso \ndi evento?\nDenuncia\nCon riferimento alla liquidazione delle prestazioni dedotte in Contratto, il Contraente o, se del caso, \nil Beneficiario e il Referente Terzo, sono tenuti a recarsi presso la sede dell\x00intermediario presso il \nquale il Contratto è stato sottoscritto ovvero a inviare preventivamente, a mezzo di lettera \nraccomandata con avviso di ricevimento al seguente recapito:\n\x03 AXA MPS Financial DAC\n\x03 Wolfe Tone House, Wolfe Tone Street,\n\x03 Dublin, DO1 HP90 - Ireland\n\x03 Numero Verde: 800.231.187\n\x03 email: supporto@axa-mpsfinancial.ie\ni documenti di seguito elencati per ciascuna prestazione, al fine di consentire all\x00Impresa di \nAssicurazione di verificare l\x00effettiva esistenza dell\x00obbligo di pagamento.\nin caso di Riscatto totale, il Contraente deve inviare all\x00Impresa di Assicurazione:\n\x04 la richiesta di Riscatto totale firmata dal Contraente, indicando il conto corrente su cui il \npagamento deve essere effettuato. Nel caso il conto corrente sia intestato a persona diversa dal \nContraente o dai beneficiari o sia cointestato, il Contraente deve fornire anche I documenti del \ncointestatario e specificare la relazione con il terzo il cui conto viene indicato.\n\x04 copia di un valido documento di identità del Contraente o di un documento attestante i poteri di \nlegale rappresentante, nel caso in cui il Contraente sia una persona giuridica;\nin caso di Riscatto parziale, il Contraente deve inviare all\x00Impresa di Assicurazione:\n\x04 la richiesta di Riscatto parziale firmata dal Contraente, contenente l\x00indicazione dei Fondi \nInterni/OICR che intende riscattare e il relativo ammontare non ché l\x00indicazione del conto corrente \nbancario sul quale effettuare il pagamento;\n\x04 copia di un valido documento di identità del Contraente, o di un documento attestante i poteri di \nlegale rappresentante, nel caso in cui il Contraente sia una persona giuridica.\nIn caso di richiesta di Riscatto totale o parziale non corredata dalla sopra elencata documentazione, \nl\x00Impresa di Assicurazione effettuerà il disinvestimento delle Quote collegate al Contratto alla data \ndi ricezione della relativa richiesta. L\x00Impresa di Assicurazione provvederà tuttavia alla liquidazione \ndelle somme unicamente al momento di ricezione della documentazione mancante, prive degli \neventuali interessi che dovessero maturare;\nIn caso di decesso dell\x00Assicurato, il Beneficiario/i o il Referente Terzo deve inviare all\x00Impresa di \nAssicurazione:\nDIP aggiuntivo IBIP - Progetto Protetto New - Global Dividends -   Pag. 3 di 9\n',
            '\x04 la richiesta di pagamento sottoscritta da tutti i Beneficiari, con l\x00indicazione del conto corrente \nbancario sul quale effettuare il pagamento; Nel caso il conto corrente sia intestato a persona \ndiversa dal Contraente o dai beneficiari o sia cointestato, il Contraente deve fornire anche I \ndocumenti del cointestatario e specificare la relazione con il terzo il cui conto viene indicato.\n\x04 copia di un valido documento d\x00identità dei Beneficiari o di un documento attestante i poteri di \nlegale rappresentante, nel caso in cui il Beneficiario sia una persona giuridica;\n\x04 il certificato di morte dell\x00Assicurato;\n\x04 la relazione medica sulle cause del decesso;\n\x04 copia autenticata del testamento accompagnato da dichiarazione sostitutiva di atto di notorietà \ncon l\x00indicazione (i) della circostanza che il testamento è l\x00ultimo da considerarsi valido e non è \nstato impugnato e (ii) degli eredi testamentari, le relative età e capacità\ndi agire;\n\x04 in assenza di testamento, atto notorio (o dichiarazione sostitutiva di atto di notorietà) attestante \nche il decesso è avvenuto senza lasciare testamento e che non vi sono altri soggetti cui la legge \nriconosce diritti o quote di eredità;\n\x04 decreto del Giudice Tutelare nel caso di Beneficiari di minore età, con l\x00indicazione della persona \ndesignata alla riscossione;\n\x04 copia del Questionario KYC.\nPrescrizione: Alla data di redazione del presente documento, i diritti dei beneficiari dei contratti di \nassicurazione sulla vita si prescrivono nel termine di dieci anni dal giorno in cui si è verificato il fatto \nsu cui il diritto si fonda. Decorso tale termine e senza che la Compagnia abbia ricevuto alcuna \ncomunicazione e/o disposizione, gli importi derivanti dal contratto saranno devoluti al Fondo \ncostitutivo presso il Ministero dell\x00Economia e delle Finanze \x01depositi dormienti\x02.\nErogazione della prestazione\nL\x00Impresa di Assicurazione esegue il pagamento entro trenta giorni dal ricevimento della \ndocumentazione completa all\x00indirizzo sopra indicato.\n \nLe dichiarazioni del Contraente, e dell\x00Assicurato se diverso dal Contraente, devono essere esatte e \nveritiere. In caso di dichiarazioni inesatte o reticenti relative a circostanze tali che l\x00Impresa di \nAssicurazione non avrebbe dato il suo consenso, non lo avrebbe dato alle medesime condizioni se \navesse conosciuto il vero stato delle cose, l\x00Impresa di Assicurazione ha diritto a:\na) in caso di dolo o colpa grave:\n\x04 impugnare il Contratto dichiarando al Contraente di voler esercitare tale diritto entro tre mesi dal \ngiorno in cui ha conosciuto l\x00inesattezza della dichiarazione o le reticenze;\n\x04 trattenere il Premio relativo al periodo di assicurazione in corso al momento dell\x00impugnazione e, \nin ogni caso, il Premio corrispondente al primo anno;\n\x04 restituire, in caso di decesso dell\x00Assicurato, solo il Controvalore delle Quote acquisite al \nmomento del decesso, se l\x00evento si verifica prima che sia decorso il termine dianzi indicato per \nl\x00impugnazione;\nb) ove non sussista dolo o colpa grave:\n\x04 recedere dal Contratto, mediante dichiarazione da farsi al Contraente entro tre mesi dal giorno in \ncui ha conosciuto l\x00inesattezza della dichiarazione o le reticenze;\n\x04 se il decesso si verifica prima che l\x00inesattezza della dichiarazione o la reticenza sia conosciuta \ndall\x00Impresa di Assicurazione, o prima che l\x00Impresa abbia dichiarato di recedere dal Contratto, di \nridurre la somma dovuta in proporzione alla differenza tra il Premio convenuto e quello che sarebbe \nstato applicato se si fosse conosciuto il vero stato delle cose.\nIl Contraente è tenuto a inoltrare per iscritto alla Compagnia (posta ordinaria e mail) eventuali \ncomunicazioni inerenti:\n-modifiche dell\x00indirizzo presso il quale intende ricevere le comunicazioni relative al contratto;\n-variazione della residenza Europea nel corso della durata del contratto, presso altro Paese \nmembro della Unione Europea;\n-variazione degli estremi di conto corrente bancario.\nIn tal caso è necessario inoltrare la richiesta attraverso l\x00invio del modulo del mandato, compilato e \nsottoscritto dal contraente, reperibile nella sezione \x01comunicazioni\x02 sul sito internet della \ncompagnia all\x00indirizzo www.axa-mpsfinancial.ie\nFATCA (Foreign Account Tax Compliance Act) e CRS (Common Standard Reporting)\nLa normativa denominata rispettivamente FATCA (Foreign Account Tax Compliance Act - \nIntergovernmental Agreement sottoscritto tra Italia e Stati Uniti in data 10 gennaio 2014 e Legge n. \n95 del 18 giugno 2015) e CRS (Common Reporting Standard - Decreto Ministeriale del 28 \ndicembre 2015) impone agli operatori commerciali, al fine di contrastare la frode fiscale e \nl\x00evasione fiscale transfrontaliera, di eseguire la puntuale identificazione della propria clientela al \nfine di determinarne l\x00effettivo status di contribuente estero.\nDichiarazioni \ninesatte o \nreticenti\nDIP aggiuntivo IBIP - Progetto Protetto New - Global Dividends -   Pag. 4 di 9\n',
            "I dati anagrafici e patrimoniali dei Contraenti identificati come fiscalmente residenti negli USA e/o \nin uno o più Paesi aderenti al CRS, dovranno essere trasmessi all\x00autorità fiscale locale, tramite \nl\x00Agenzia delle Entrate.\nL\x00identificazione avviene in fase di stipula del contratto e deve essere ripetuta in caso di \ncambiamento delle condizioni originarie durante tutta la sua durata, mediante l\x00acquisizione di \nautocertificazione rilasciata dai Contraenti. Ogni contraente è tenuto a comunicare \ntempestivamente eventuali variazioni rispetto a quanto dichiarato o rilevato in fase di sottoscrizione \ndel contratto di assicurazione. La Società si riserva inoltre di verificare i dati raccolti e di richiedere \nulteriori informazioni. In caso di autocertificazione che risulti compilata parzialmente o in maniera \nerrata, nonché in caso di mancata/non corretta comunicazione dei propri dati anagrafici, la società \nqualora abbia rilevato indizi di americanità e/o residenze fiscali estere nelle informazioni in suo \npossesso, assocerà al cliente la condizione di contribuente estero, provvedendo alla comunicazione \ndovuta.\nAntiriciclaggio\nIl Contraente è tenuto a fornire alla Compagnia tutte le informazioni necessarie al fine \ndell\x00assolvimento dell\x00adeguata verifica ai fini antiriciclaggio. Qualora la Compagnia, in ragione \ndella mancata collaborazione del Contraente, non sia in grado di portare a compimento l\x00adeguata \nverifica, la stessa non potrà concludere il Contratto o dovrà porre fine allo stesso. In tali ipotesi le \nsomme dovute al Contraente dovranno essere allo stesso versate mediante bonifico a valere un \nconto corrente intestato al Contraente stesso. In tali ipotesi le disponibilità finanziarie \neventualmente già acquisite dalla Compagnia dovranno essere restituite al Contraente liquidando il \nrelativo importo tramite bonifico bancario su un conto corrente bancario indicato dal Contraente e \nallo stesso intestato.\nIn nessun caso l'Impresa di Assicurazione sarà tenuta a fornire alcuna copertura assicurativa, \nsoddisfare richieste di risarcimento o garantire alcuna indennità in virtù del presente contratto, \nqualora tale copertura, pagamento o indennità possa esporla a divieti, sanzioni economiche o \nrestrizioni ai sensi di Risoluzioni delle Nazioni Unite o sanzioni economiche o commerciali, leggi o \nnorme dell\x00Unione Europea, del Regno Unito o degli Stati Uniti d\x00America, ove applicabili in Italia.\nQuando e come devo pagare?\nPremio\nIl Contratto prevede il pagamento di un Premio Unico il cui ammontare minimo è pari a 2.500,00 \neuro, incrementabile di importo pari o in multiplo di 50,00 euro, da corrispondersi in un\x00unica \nsoluzione prima della conclusione del Contratto.\nNon è prevista la possibilità di effettuare versamenti aggiuntivi successivi.\nIl versamento del Premio Unico può essere effettuato mediante addebito su conto corrente \nbancario, indicato nel Modulo di Proposta, previa autorizzazione del titolare del conto corrente.\nIl pagamento dei Premio Unico può essere eseguito mediante addebito su conto corrente bancario, \nprevia autorizzazione, intestato al Contraente oppure tramite bonifico bancario sul conto corrente \ndell\x00Impresa di Assicurazione.\nRimborso\nIl rimborso del Premio Versato è previsto nel caso in cui il Contraente decida di revocare la proposta \nfinché il contratto non è concluso.\nSconti\nAl verificarsi di condizioni particolari ed eccezionali che potrebbero riguardare \x03 a titolo \nesemplificativo ma non esaustivo \x03 il Contraente e la relativa situazione assicurativo/finanziaria, \nl\x00ammontare del Premio pagato e gli investimenti selezionati dal Contraente, l\x00Impresa di \nAssicurazione si riserva la facoltà di applicare sconti sugli oneri previsti dal contratto, concordando \ntale agevolazione con il Contraente.\nQuando comincia la copertura e quando finisce?\nDurata\nIl Contratto ha una durata massima pari a 5 anni 11 mesi e 27 giorni, sino alla data di scadenza \n(11/04/2029, la \x01data di scadenza\x02).\nSospensione\nNon sono possibili delle sospensioni della copertura assicurativa\nDIP aggiuntivo IBIP - Progetto Protetto New - Global Dividends -   Pag. 5 di 9\n",
            'Come posso revocare la proposta, recedere dal contratto o risolvere il contratto? \nRevoca\nLa Proposta di assicurazione può essere revocata fino alle ore 24:00 del giorno in cui il Contratto è \nconcluso. In tal caso, l\x00Impresa di Assicurazione restituirà al Contraente il Premio pagato entro \ntrenta giorni dal ricevimento della comunicazione di Revoca.\nRecesso\nIl Contraente può recedere dal Contratto entro trenta giorni dalla sua conclusione. Il Recesso dovrà \nessere comunicato all\x00Impresa di Assicurazione mediante lettera raccomandata con avviso di \nricevimento.\nL\x00Impresa di Assicurazione, entro trenta giorni dal ricevimento della comunicazione relativa al \nRecesso, rimborserà al Contraente il Controvalore delle Quote attribuite al Contratto alla data di \nricevimento della richiesta di recesso incrementato dai caricamenti, ove previsti, e dedotte \neventuali agevolazioni.\nRisoluzione\nLa risoluzione del contratto è prevista tramite la richiesta di riscatto totale esercitabile in qualsiasi \nmomento della durata contrattuale\nSono previsti riscatti o riduzioni? Si\n no\nValori di\nriscatto e\nriduzione\nA condizione che siano trascorsi almeno 30 giorni dalla Data di Decorrenza (conclusione del \nContratto) e fino all\x00ultimo Giorno Lavorativo della terzultima settimana precedente la data di \nscadenza, il Contraente può riscuotere, interamente o parzialmente, il Valore di Riscatto. In caso di \nRiscatto totale, la liquidazione del Valore di Riscatto pone fine al Contratto con effetto dalla data di \nricezione della richiesta.\nL\x00importo che sarà corrisposto al Contraente in caso di Riscatto sarà pari al Controvalore delle \nQuote del Fondo Interno attribuite al Contratto alla data di Riscatto, al netto dei costi di Riscatto.\nIn caso di Riscatto, ai fini del calcolo del Valore Unitario della Quota, si farà riferimento alla Data di \nValorizzazione della settimana successiva alla data in cui la comunicazione di Riscatto del \nContraente perviene all\x00Impresa di Assicurazione, corredata di tutta la documentazione, al netto dei \ncosti di Riscatto, salvo il verificarsi di Eventi di Turbativa.\nIl Contraente assume il rischio connesso all\x00andamento negativo del valore delle Quote e, pertanto, \nesiste la possibilità di ricevere un ammontare inferiore all\x00investimento finanziario.\nIn caso di Riscatto del Contratto (totale o parziale), l\x00Impresa di Assicurazione non offre alcuna \ngaranzia finanziaria di rendimento minimo e pertanto il Contraente sopporta il rischio di ottenere un \nValore Unitario di Quota inferiore al 100% del Valore Unitario di Quota del Fondo Interno registrato \nalla Data di Istituzione in considerazione dei rischi connessi alla fluttuazione del valore di mercato \ndegli attivi in cui investe, direttamente o indirettamente, il Fondo Interno.\nRichiesta di\ninformazioni\nPer eventuali richieste di informazioni sul valore di riscatto, il Contraente può rivolgersi alla \nCompagnia AXA MPS Financial DAC \x03 Wolfe Tone House, Wolfe Tone Street, Dublin, DO1 HP90 \x03 \nIreland, Numero Verde 800.231.187, e-mail: supporto@axa-mpsfinancial.ie\nA chi è rivolto questo prodotto?\nL\x00investitore al dettaglio a cui è destinato il prodotto varia in funzione dell\x00opzione di investimento sottostante e \nillustrata nel relativo KID.\nIl prodotto è indirizzato a Contraenti persone fisiche e persone giuridiche a condizione che il Contraente (persona fisica) \ne l\x00Assicurato, al momento della sottoscrizione stessa, abbiano un\x00età compresa tra i 18 anni e i 85 anni.\nQuali costi devo sostenere?\nPer l\x00informativa dettagliata sui costi fare riferimento alle indicazioni del KID.\nIn aggiunta rispetto alle informazioni del KID , indicare i seguenti costi a carico del contraente.\nSpese di emissione:\nIl Contratto prevede una spesa fissa di emissione pari a 25 Euro.\nLa deduzione di tale importo avverrà contestualmente alla deduzione del premio.\nDIP aggiuntivo IBIP - Progetto Protetto New - Global Dividends -   Pag. 6 di 9\n',
            "L\x00obiettivo di protezione è da considerarsi al netto delle spese di emissione.\nCosti per riscatto\nIl Riscatto (totale e parziale) prevede un costo che varia in funzione della data di richiesta e secondo le percentuali di \nseguito indicate:\n1°Anno 5,00%; 2°Anno 3,50%; 3°Anno 2,00%; dal quarto anno in poi 0%;\nCosti di intermediazione\nla quota parte massima percepita dall\x00intermediario con riferimento all\x00intero flusso commissionale relativo al prodotto \nè pari al 35,17%.\nQuali sono i rischi e qual è il potenziale rendimento?\nSia con riferimento alla prestazione in caso di vita dell\x00assicurato, sia con riferimento al capitale caso morte riferito ai \nFondi Assicurativi Interni, la Compagnia non presta alcuna garanzia di rendimento minimo o di conservazione del \ncapitale. Pertanto il controvalore della prestazione della Compagnia potrebbe essere inferiore all\x00importo dei premi \nversati, in considerazione dei rischi connessi alla fluttuazione del valore di mercato degli attivi in cui investe, \ndirettamente o indirettamente il Fondo Interno.\nCOME POSSO PRESENTARE I RECLAMI E RISOLVERE LE CONTROVERSIE?\nAll\x00IVASS\nNel caso in cui il reclamo presentato all\x00impesa assicuratrice abbia esito insoddisfacente o risposta \ntardiva, è possibile rivolgersi all\x00IVASS, Via del Quirinale, 21 - 00187 Roma, fax 06.42133206, Info \nsu: www.ivass.it.\nEventuali reclami potranno inoltre essere indirizzati all\x00Autorità Irlandese competente al seguente \nindirizzo:\nFinancial Services Ombudsman 3rd Floor, Lincoln House, Lincoln Place, Dublin 2, D02 VH29 \x03 \nIreland\nPRIMA DI RICORRERE ALL\x00AUTORITÀ GIUDIZIARIA è possibile, in alcuni casi necessario, \navvalersi di sistemi alternativi di risoluzione delle controversie, quali:\nMediazione\nInterpellando un Organismo di Mediazione tra quelli presenti nell'elenco del Ministero della \nGiustizia, consultabile sul sito www.giustizia.it (Legge 9/8/2013, n.98)\nNegoziazione \nassistita\nTramite richiesta del proprio avvocato all\x00impresa\nAltri Sistemi \nalternative di \nrisoluzione delle \ncontroversie\nEventuali reclami relativi ad un contratto o servizio assicurativo nei confronti dell'Impresa di \nassicurazione o dell'Intermediario assicurativo con cui si entra in contatto, nonché qualsiasi \nrichiesta di informazioni, devono essere preliminarmente presentati per iscritto (posta, email) ad \nAXA MPS Financial DAC - Ufficio Reclami secondo seguenti modalità:\nEmail: reclami@axa-mpsfinancial.ie\nPosta: AXA MPS Financial DAC - Ufficio Reclami\nWolfe Tone House, Wolfe Tone Street,\nDublin DO1 HP90 - Ireland\nNumero Verde 800.231.187\navendo cura di indicare:\n-nome, cognome, indirizzo completo e recapito telefonico del reclamante;\n-numero della polizza e nominativo del contraente;\n-breve ed esaustiva descrizione del motivo di lamentela;\n-ogni altra indicazione e documento utile per descrivere le circostanze.\nSarà cura della Compagnia fornire risposta entro 45 giorni dalla data di ricevimento del reclamo, \ncome previsto dalla normativa vigente.\nNel caso di mancato o parziale accoglimento del reclamo, nella risposta verrà fornita una chiara \nspiegazione della posizione assunta dalla Compagnia in relazione al reclamo stesso ovvero della \nsua mancata risposta.\nQualora il reclamante non abbia ricevuto risposta oppure ritenga la stessa non soddisfacente, \nprima di rivolgersi all'Autorità Giudiziaria, può scrivere all'IVASS (Via del Quirinale, 21 - 00187 \nRoma; fax 06.42.133.745 o 06.42.133.353, ivass@pec.ivass.it) fornendo copia del reclamo già \nDIP aggiuntivo IBIP - Progetto Protetto New - Global Dividends -   Pag. 7 di 9\n",
            "inoltrato all'impresa ed il relativo riscontro anche utilizzando il modello presente nel sito dell'IVASS \nalla sezione per il Consumatore - come presentare un reclamo.\nEventuali reclami potranno inoltre essere indirizzati all'Autorità Irlandese competente al seguente \nindirizzo:\nFinancial Services Ombudsman\n3rd Floor, Lincoln House,\nLincoln Place, Dublin 2, D02 VH29 Ireland\nIl reclamante può ricorrere ai sistemi alternativi per la risoluzione delle controversie previsti a livello \nnormativo o convenzionale, quali:\n\x04 Mediazione: (Decreto Legislativo n.28/2010 e ss.mm.) puo' essere avviata presentando istanza \nad un Organismo di Mediazione tra quelle presenti nell'elenco del Ministero della Giustizia, \nconsultabile sul sito www.giustizia.it. La legge ne prevede l'obbligatorieta' nel caso in cui si intenda \nesercitare in giudizio i propri diritti in materia di contratti assicurativi o finanziari e di risarcimento \nda responsabilita'  medica e sanitaria, costituendo condizione di procedibilita' della domanda.\n\x04 Negoziazione Assistita: (Legge n.162/2014) tramite richiesta del proprio Avvocato all'Impresa. E' \nun accordo mediante il quale le parti convengono di cooperare in buona fede e con lealta' per \nrisolvere in via amichevole la controversia tramite l'assistenza di avvocati. Fine del procedimento e' \nla composizione bonaria della lite, con la sottoscrizione delle parti - assistite dai rispettivi difensori - \ndi un accordo detto convenzione di negoziazione. Viene prevista la sua obbligatorieta' nel caso in \ncui si intenda esercitare in giudizio i propri diritti per ogni controversia in materia di risarcimento del \ndanno da circolazione di veicoli e natanti, ovverosia e' condizione di procedibilita' per l'eventuale \ngiudizio civile. Invece e' facoltativa per ogni altra controversia in materia di risarcimenti o di contratti \nassicurativi o finanziari.\nIn caso di controversia relativa alla determinazione dei danni si puo' ricorrere alla perizia \ncontrattuale prevista dalle Condizioni di Assicurazione per la risoluzione di tale tipologia di \ncontroversie. L'istanza di attivazione della perizia contrattuale dovra' essere indirizzata alla \nCompagnia all' indirizzo\nAXA MPS Financial DAC \nWolfe Tone House, Wolfe Tone Street\nDublin DO1 HP90  - Ireland\nPer maggiori informazioni si rimanda a quanto presente nell'area Reclami del sito \nwww.axa-mpsfinancial.ie. \nPer la risoluzione delle liti transfrontaliere è possibile presentare reclamo all'IVASS o direttamente \nal sistema estero http://ec.europa.eu/internal_market/fin-net/members_en.htm competente \nchiedendo l'attivazione della procedura FIN-NET.\nEventuali reclami relativi la mancata osservanza da parte della Compagnia, degli intermediari e dei \nperiti assicurativi, delle disposizioni del Codice delle assicurazioni, delle relative norme di \nattuazione nonché delle norme sulla commercializzazione a distanza dei prodotti assicurativi \npossono essere presentati direttamente all'IVASS, secondo le modalità sopra indicate.\nSi ricorda che resta salva la facoltà di adire l'autorità giudiziaria.\nREGIME FISCALE\nTrattamento \nfiscale applicabile \nal contratto\nLe seguenti informazioni sintetizzano alcuni aspetti del regime fiscale applicabile al Contratto, ai \nsensi della legislazione tributaria italiana e della prassi vigente alla data di pubblicazione del \npresente documento, fermo restando che le stesse rimangono soggette a possibili cambiamenti che \npotrebbero avere altresì effetti retroattivi. Quanto segue non intende rappresentare un\x00analisi \nesauriente di tutte le conseguenze fiscali del Contratto. I Contraenti sono tenuti a consultare i loro \nconsulenti in merito al regime fiscale proprio del Contratto.\nTasse e imposte\nLe imposte e tasse presenti e future applicabili per legge al Contratto sono a carico del Contraente \no dei Beneficiari e aventi diritto e non è prevista la corresponsione al Contraente di alcuna somma \naggiuntiva volta a compensare eventuali riduzioni dei pagamenti relativi al Contratto.\nTassazione delle somme corrisposte a soggetti non esercenti attività d\x00impresa\n1. In caso di decesso dell\x00Assicurato\nLe somme corrisposte dall\x00Impresa di Assicurazione in caso di decesso dell\x00Assicurato non sono \nsoggette a tassazione IRPEF in capo al percettore e sono esenti dall\x00imposta sulle successioni. Si \nricorda tuttavia che, per effetto della legge 23 dicembre 2014 n. 190 (c.d.\x02Legge di Stabilità\x02), i \nDIP aggiuntivo IBIP - Progetto Protetto New - Global Dividends -   Pag. 8 di 9\n",
            'capitali percepiti in caso di morte, a decorrere dal 1 gennaio 2015, in dipendenza di contratti di \nassicurazione sulla vita, a copertura del rischio demografico, sono esenti dall\x00imposta sul reddito \ndelle persone fisiche.\n2. In caso di Riscatto totale o di Riscatto parziale.\nLe somme corrisposte dall\x05Impresa di Assicurazione in caso di Riscatto totale sono soggette ad \nun\x00imposta sostitutiva dell\x00imposta sui redditi nella misura prevista di volta in volta dalla legge. Tale \nimposta, al momento della redazione del presente documento, è pari al 26% sulla differenza \n(plusvalenza) tra il capitale maturato e l\x00ammontare dei premi versati (al netto di eventuali riscatti \nparziali), con l\x00eccezione dei proventi riferibili ai titoli di stato italiani ed equiparati (Paesi facenti \nparte della white list), per i quali l\x00imposta è pari al 12,5%.\nIn caso di Riscatto parziale, ai fini del computo del reddito di capitale da assoggettare alla predetta \nimposta sostitutiva, l\x00ammontare dei premi va rettificato in funzione del rapporto tra il capitale \nerogato ed il valore economico della polizza alla data del Riscatto parziale.\n3. In caso di Recesso\nLe somme corrisposte in caso di Recesso sono soggette all\x00imposta sostitutiva delle imposte sui \nredditi nella misura e con gli stessi criteri indicati per il Riscatto totale del Contratto.\nTassazione delle somme corrisposte a soggetti esercenti attività d\x00impresa\nLe somme corrisposte a soggetti che esercitano l\x00attività d\x00impresa non costituiscono redditi di \ncapitale, bensì redditi d\x00impresa. Su tali somme l\x00Impresa non applica l\x00imposta sostitutiva di cui \nall\x00art. 26-ter del D.P.R. 29 settembre 1973, n. 600.\nSe le somme sono corrisposte a persone fisiche o enti non commerciali in relazione a contratti \nstipulati nell\x00ambito dell\x00attività commerciale, l\x00Impresa non applica l\x00imposta sostitutiva, qualora gli \ninteressati presentino una dichiarazione in merito alla sussistenza di tale requisito.\nL\x00IMPRESA HA L\x00OBBLIGO DI TRASMETTERTI, ENTRO IL 31 MAGGIO DI OGNI ANNO, IL DOCUMENTO \nUNICO DI RENDICONTAZIONE ANNUALE DELLA TUA POSIZIONE ASSICURATIVA\nPER QUESTO CONTRATTO L\x00IMPRESA NON DISPONE DI UN\x00AREA INTERNET DISPOSITIVA RISERVATA \nAL CONTRAENTE (c.d. HOME INSURANCE), PERTANTO DOPO LA SOTTOSCRIZIONE  NON POTRAI \nGESTIRE TELEMATICAMENTE IL CONTRATTO MEDESIMO.\nDIP aggiuntivo IBIP - Progetto Protetto New - Global Dividends -   Pag. 9 di 9\n',
            ]

    path = os.path.abspath(f'{__file__}/../../tests/resources/test_3186.pdf')
    fitz_doc = pymupdf.open(path)
    texts = list()
    for page in fitz_doc:
        t = page.get_text()
        texts.append(t)
    assert texts == texts_expected, f'Unexpected output: {texts=}'


def test_3197():
    '''
    MuPDF's ActualText support fixes handling of test_3197.pdf.
    '''
    if pymupdf.mupdf_version_tuple < (1, 24):
        print(f'Not running on {pymupdf.mupdf_version_tuple=}.')
        return
    path = os.path.abspath(f'{__file__}/../../tests/resources/test_3197.pdf')
    
    text_utf8_expected = [
            b'NYSE - Nasdaq Real Time Price \xe2\x80\xa2 USD\nFord Motor Company (F)\n12.14 -0.11 (-0.90%)\nAt close: 4:00 PM EST\nAfter hours: 7:43 PM EST\nAll numbers in thousands\nAnnual\nQuarterly\nDownload\nSummary\nNews\nChart\nConversations\nStatistics\nHistorical Data\nProfile\nFinancials\nAnalysis\nOptions\nHolders\nSustainability\nInsights\nFollow\n12.15 +0.01 (+0.08%)\nIncome Statement\nBalance Sheet\nCash Flow\nSearch for news, symbols or companies\nNews\nFinance\nSports\nSign in\nMy Portfolio\nNews\nMarkets\nSectors\nScreeners\nPersonal Finance\nVideos\nFinance Plus\nBack to classic\nMore\n',
            b'Related Tickers\nTTM\n12/31/2023\n12/31/2022\n12/31/2021\n12/31/2020\n14,918,000\n14,918,000\n6,853,000\n15,787,000\n24,269,000\n-17,628,000\n-17,628,000\n-4,347,000\n2,745,000\n-18,615,000\n2,584,000\n2,584,000\n2,511,000\n-23,498,000\n2,315,000\n25,110,000\n25,110,000\n25,340,000\n20,737,000\n25,935,000\n-8,236,000\n-8,236,000\n-6,866,000\n-6,227,000\n-5,742,000\n51,659,000\n51,659,000\n45,470,000\n27,901,000\n65,900,000\n-41,965,000\n-41,965,000\n-45,655,000\n-54,164,000\n-60,514,000\n-335,000\n-335,000\n-484,000\n--\n--\n6,682,000\n6,682,000\n-13,000\n9,560,000\n18,527,000\n \nYahoo Finance Plus Essential\naccess required.\nUnlock Access\nBreakdown\nOperating Cash\nFlow\nInvesting Cash\nFlow\nFinancing Cash\nFlow\nEnd Cash Position\nCapital Expenditure\nIssuance of Debt\nRepayment of Debt\nRepurchase of\nCapital Stock\nFree Cash Flow\n12/31/2020 - 6/1/1972\nGM\nGeneral Motors Compa\xe2\x80\xa6\n39.49 +1.23%\n\xc2\xa0\nRIVN\nRivian Automotive, Inc.\n15.39 -3.15%\n\xc2\xa0\nNIO\nNIO Inc.\n5.97 +0.17%\n\xc2\xa0\nSTLA\nStellantis N.V.\n25.63 +0.91%\n\xc2\xa0\nLCID\nLucid Group, Inc.\n3.7000 +0.54%\n\xc2\xa0\nTSLA\nTesla, Inc.\n194.77 +0.52%\n\xc2\xa0\nTM\nToyota Motor Corporati\xe2\x80\xa6\n227.09 +0.14%\n\xc2\xa0\nXPEV\nXPeng Inc.\n9.08 +0.89%\n\xc2\xa0\nFSR\nFisker Inc.\n0.5579 -11.46%\n\xc2\xa0\nCopyright \xc2\xa9 2024 Yahoo.\nAll rights reserved.\nPOPULAR QUOTES\nTesla\nDAX Index\nKOSPI\nDow Jones\nS&P BSE SENSEX\nSPDR S&P 500 ETF Trust\nEXPLORE MORE\nCredit Score Management\nHousing Market\nActive vs. Passive Investing\nShort Selling\nToday\xe2\x80\x99s Mortgage Rates\nHow Much Mortgage Can You Afford\nABOUT\nData Disclaimer\nHelp\nSuggestions\nSitemap\n',
            ]
    
    with pymupdf.open(path) as document:
        for i, page in enumerate(document):
            text = page.get_text()
            #print(f'{i=}:')
            text_utf8 = text.encode('utf8')
            #print(f'                {text_utf8=}')
            #print(f'    {text_utf8_expected[i]=}')
            if pymupdf.mupdf_version_tuple >= (1, 24):
                assert text_utf8 == text_utf8_expected[i]
            else:
                assert text_utf8 != text_utf8_expected[i]


def test_document_text():
    import platform
    import time
    
    path = os.path.abspath(f'{__file__}/../../tests/resources/mupdf_explored.pdf')
    concurrency = None
    
    def llen(texts):
        l = 0
        for text in texts:
            l += len(text) if isinstance(text, str) else text
        return l

    results = dict()
    _stats = 1
    
    print('')
    method = 'single'
    t = time.time()
    document = pymupdf.Document(path)
    texts0 = pymupdf.get_text(path, _stats=_stats)
    t0 = time.time() - t
    print(f'{method}: {t0=} {llen(texts0)=}', flush=1)

    # Dummy run seems to avoid misleading stats with slow first run.
    method = 'mp'
    texts = pymupdf.get_text(path, concurrency=concurrency, method=method, _stats=_stats)

    method = 'mp'
    t = time.time()
    texts = pymupdf.get_text(path, concurrency=concurrency, method=method, _stats=_stats)
    t = time.time() - t
    print(f'{method}: {concurrency=} {t=} ({t0/t:.2f}x) {llen(texts)=}', flush=1)
    assert texts == texts0

    if platform.system() != 'Windows':
        method = 'fork'
        t = time.time()
        texts = pymupdf.get_text(path, concurrency=concurrency, method='fork', _stats=_stats)
        t = time.time() - t
        print(f'{method}: {concurrency=} {t=} ({t0/t:.2f}x) {llen(texts)=}', flush=1)
        assert texts == texts0
    
    if _stats:
        pymupdf._log_items_clear()


def test_3594():
    print()
    d = pymupdf.open(os.path.abspath(f'{__file__}/../../tests/resources/test_3594.pdf'))
    for i, p in enumerate(d.pages()):
        text = p.get_text()
        print('='*40)
        print(f'Page {i}:')
        for line in text.split('\n'):
            print(f'    {line!r}')
    if pymupdf.mupdf_version_tuple < (1, 24, 3):
        # We expect MuPDF warnings.
        wt = pymupdf.TOOLS.mupdf_warnings()
        assert wt
