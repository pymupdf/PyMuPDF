"""
Demo script for PyMuPDF's `fitz.Story.write_stabilized()`.

`fitz.Story.write_stabilized()` is similar to `fitz.Story.write()`,
except instead of taking a fixed html document, it does iterative layout
of dynamically-generated html content (provided by a callback) to a
`fitz.DocumentWriter`.

For example this allows one to add a dynamically-generated table of contents
section while ensuring that page numbers are patched up until stable.
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
            
            <h1>Second section</h1>
            <p>Contents of second section.
            <h2>Second section first subsection</h2>
            
            <p>Contents of second section first subsection.
            
            <h1>Third section</h1>
            <p>Contents of third section.
            
            </body>
            ''')
    ret = ret.strip()
    with open(__file__.replace('.py', '.html'), 'w') as f:
        f.write(ret)
    return ret;


out_path = __file__.replace('.py', '.pdf')
writer = fitz.DocumentWriter(out_path)
fitz.Story.write_stabilized(writer, contentfn, rectfn)
writer.close()
