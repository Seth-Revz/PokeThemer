from xml.dom.minidom import parse, Node
import os
from PIL import Image


def decomp_xml_image_areas(theme_dir: str, file: str, constant_definitions = {}):
    document = parse(f'{theme_dir}/{file}')

    for node in document.documentElement.childNodes:
        if node.nodeType != Node.ELEMENT_NODE:
            continue

        if node.nodeName == 'constantDef':
            if node.firstChild.nodeValue:
                constant_definitions[node.getAttribute('name')] = node.firstChild.nodeValue

        if node.nodeName == 'images'and node.hasAttribute('file'):
            image_path = node.getAttribute('file')
            if '.png' not in image_path:
                continue # TODO Find REF to image

            img = Image.open(f'{theme_dir}/{image_path}')
            coordinates = []
            output_folder_name = f"output/{theme_dir}_decomp/{image_path.split('/')[-1].rstrip('.png')}"
                
            for child in node.childNodes:
                if child.nodeType != Node.ELEMENT_NODE:
                    continue

                if child.nodeName in ['area', 'cursor'] and child.hasAttribute('xywh'):
                    name = child.getAttribute('name')

                    if '*' in child.getAttribute('xywh'):
                        continue # TODO Wildcard used for full images

                    x, y, w, h = [int(x) for x in child.getAttribute('xywh').split(',')]

                    if w < 0:
                        continue 

                    if h < 0:
                        h = abs(h)
                    
                    sprite = img.crop((x, y, x+w, y+h))
                    if not os.path.exists(output_folder_name):
                        os.makedirs(output_folder_name)
                    sprite.save(f'{output_folder_name}/{name}.png')
                
                elif child.nodeName in ['select', 'grid']:
                    name = child.getAttribute('name')
                    index = 0
                    for area in [ node for node in child.childNodes if node.nodeName == 'area' and node.hasAttribute('xywh') ]:
                        if '*' in child.getAttribute('xywh'):
                            continue # TODO Wildcard used for full images

                        x, y, w, h = [int(x) for x in area.getAttribute('xywh').split(',')]
                        if (x, y, w, h) in coordinates:
                            continue
                        coordinates.append((x,y,w,h))
                        # print(name, x, y, w, h)

                        if w < 0:
                            continue 

                        if h < 0:
                            h = abs(h)
                        
                        sprite = img.crop((x, y, x+w, y+h))
                        if not os.path.exists(f'{output_folder_name}/{name}'):
                            os.makedirs(f'{output_folder_name}/{name}')
                        sprite.save(f'{output_folder_name}/{name}/{name}_{index}.png')
                        index += 1
                else:
                    search = child.getElementsByTagName('area')
                    if search:
                        for i in search:
                            print(i)

        if node.nodeName == 'include' and node.hasAttribute('filename'):
            decomp_xml_image_areas(theme_dir, node.getAttribute('filename'), constant_definitions)
    
    print(*constant_definitions.values(), sep='\n')

def rebuild_xml_image_areas():
    pass

if __name__ == '__main__':
    theme = 'default'
    decomp_xml_image_areas(theme, 'twl-themer-load.xml')
