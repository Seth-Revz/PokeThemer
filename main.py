import xml.etree.ElementTree as ET
import os
from PIL import Image


if __name__ == '__main__':
    tree = ET.parse('default/cursors.xml')
    root = tree.getroot()

    for element in tree.findall('images'):

        image_path = element.attrib['file']
        img = Image.open('default/' + image_path)

        for item in element:
            name = item.attrib['name']
            if 'xywh' in item.attrib:
                x, y, w, h = [int(x) for x in item.attrib['xywh'].split(',')]

                print(name, x, y, w, h)
                cut = img.crop((x, y, x+w, y+h))
                cut.save(f'{name}.png')