import markdown
import pdfkit
import os


def md2html(mdstr):
    exts = ['markdown.extensions.extra', 'markdown.extensions.codehilite', 'markdown.extensions.tables',
            'markdown.extensions.toc']

    html = '''
    <html lang="zh-cn">
    <head>
    <meta content="text/html; charset=utf-8" http-equiv="content-type" />
    <link href="default.css" rel="stylesheet">
    <link href="github-markdown.css" rel="stylesheet">
    </head>
    <body>
    %s
    </body>
    </html>
    '''

    ret = markdown.markdown(mdstr, extensions=exts)
    return html % ret


if __name__ == '__main__':
    infile_name = 'proposal.md'
    html_name = 'proposal.html'
    pdf_name = 'proposal.pdf'
    infile = open(infile_name, 'r')
    md = infile.read()
    infile.close()

    if os.path.exists(html_name):
        os.remove(html_name)

    outfile = open(html_name, 'a')
    outfile.write(md2html(md))
    outfile.close()

    if os.path.exists(pdf_name):
        os.remove(pdf_name)

    config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
    pdfkit.from_file(html_name, pdf_name, configuration=config)