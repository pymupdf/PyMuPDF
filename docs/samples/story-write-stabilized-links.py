"""
Demo script for PyMuPDF's `fitz.Story.write_stabilized_with_links()`.

`fitz.Story.write_stabilized_links()` is similar to
`fitz.Story.write_stabilized()` except that it creates a PDF `fitz.Document`
that contains PDF links generated from all internal links in the original html.
"""

import textwrap

import fitz


def rectfn(rect_num, filled):
    '''
    We return one rect per page.
    '''
    rect = fitz.Rect(10, 20, 290, 380)
    mediabox = fitz.Rect(0, 0, 300, 400)
    #print(f'rectfn(): rect_num={rect_num} filled={filled}')
    return mediabox, rect, None


def contentfn(positions):
    '''
    Returns html content, with a table of contents derived from `positions`.
    '''
    ret = ''
    ret += textwrap.dedent('''
            <!DOCTYPE html>
            <body>
            <h2>Contents</h2>
            <ul>
            ''')
    
    # Create table of contents with links to all <h1..6> sections in the
    # document.
    for position in positions:
        if position.heading and (position.open_close & 1):
            text = position.text if position.text else ''
            if position.id:
                ret += f"    <li><a href=\"#{position.id}\">{text}</a>\n"
            else:
                ret += f"    <li>{text}\n"
            ret += f"        <ul>\n"
            ret += f"        <li>page={position.page_num}\n"
            ret += f"        <li>depth={position.depth}\n"
            ret += f"        <li>heading={position.heading}\n"
            ret += f"        <li>id={position.id!r}\n"
            ret += f"        <li>href={position.href!r}\n"
            ret += f"        <li>rect={position.rect}\n"
            ret += f"        <li>text={text!r}\n"
            ret += f"        <li>open_close={position.open_close}\n"
            ret += f"        </ul>\n"
    
    ret += '</ul>\n'
    
    # Main content.
    ret += textwrap.dedent(f'''
    
            <h1>First section</h1>
            <p>Contents of first section.
            <ul>
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
    ret = ret.strip()
    with open(__file__.replace('.py', '.html'), 'w') as f:
        f.write(ret)
    return ret;


out_path = __file__.replace('.py', '.pdf')
document = fitz.Story.write_stabilized_with_links(contentfn, rectfn)
document.save(out_path)
