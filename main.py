import xml.etree.ElementTree as ET
import os
from glob import glob
from PIL import Image


if __name__ == '__main__':
    theme = 'default'

    result = [y for x in os.walk(theme) for y in glob(os.path.join(x[0], '*.xml'))]
    print(*result, sep='\n')

    for file in result:

        tree = ET.parse(file)
        root = tree.getroot()

        for element in tree.findall('images'):

            image_path = element.attrib['file']
            if '.png' not in image_path:
                continue

            output_folder_name = 'output/' + image_path.split('/')[-1].rstrip('.png')

            img = Image.open(f'{theme}/{image_path}')

            for item in element:
                name = item.attrib['name']
                if 'xywh' in item.attrib and item.attrib['xywh'] != '*':
                    x, y, w, h = [int(x) for x in item.attrib['xywh'].split(',')]

                    print(name, x, y, w, h)

                    if w < 0:
                        continue 
                    
                    cut = img.crop((x, y, x+w, y+h))
                    if not os.path.exists(output_folder_name):
                        os.makedirs(output_folder_name)
                    cut.save(f'{output_folder_name}/{name}.png')