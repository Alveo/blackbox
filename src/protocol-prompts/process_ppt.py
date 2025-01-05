"""Process Powerpoint files to generate
 map files containing the prompt text.

 This should be run whenever the powerpoint files are updated."""


import zipfile
import re
import xml.etree.ElementTree as etree


def text_from_pptx_file(filename):
    """Process this pptx file to get a list of
    the slide texts for each slide"""

    if not zipfile.is_zipfile(filename):
        return []

    zip = zipfile.ZipFile(filename)

    names = zip.namelist()
    # find the names that look like slides
    slides = dict()
    slideFilePattern = re.compile("ppt/slides/slide(\d*).xml")
    for name in names:
        match = slideFilePattern.match(name)
        if match:
            id = match.group(1)
            # we ignore slide 1
            if id=='1':
                continue
            slides[name] = int(id)

    etree.register_namespace("a", "http://schemas.openxmlformats.org/drawingml/2006/main")
    result = dict()
    for slide in slides.keys():
        fh = zip.open(slide)
        et = etree.parse(fh)
        root = et.getroot()

        nodes = find_in_tree(root, "{http://schemas.openxmlformats.org/drawingml/2006/main}t")
        text = []
        for node in nodes:
            text.append( node.text)
        result[slides[slide]] = process_slide_text(text)
    return result

def process_slide_text(text):
    """text is a list of strings from a slide, we want back
    a reasonable guess at a prompt string"""

    import unicodedata

    # numbers: ['2301: \t\ttwo three zero one'], [u'\xa0', '7856: \t\tseven eight five six']
    # replace \u2019 with -
    text = " ".join(text)

    text = text.strip()

    # normaise unicode characters
    text = text.encode('ASCII', 'ignore')

    text = text.replace(u"\u2019", "-")
    #text = text.replace(" ", "_")
    text = text.replace("\t", "")
    return text


def find_in_tree(element, name):
    """Find all nodes named in the tree below element, return a list"""

    result = []
    children = element.getchildren()
    for child in children:
        if child.tag == name:
            result.append(child)
        else:
            result.extend(find_in_tree(child, name))
    return result



if __name__=='__main__':

    import sys, os, codecs

    for pptfile in os.listdir('.'):
        if pptfile.endswith('.pptx'):
            outfile = os.path.splitext(pptfile)[0]+".map"
            print "generating", outfile

            out = codecs.open(outfile, mode='w', encoding='utf8')

            text = text_from_pptx_file(pptfile)

            count = 1
            for key in sorted(text.keys()):
                out.write(u"%d|%s|Slide%s.JPG\n" % (count, text[key], key))
                count += 1
            out.close()
