from xml.dom.minidom import parse, Node
import os
from glob import glob
from PIL import Image

def dump_theme(theme: str):
    result = [y for x in os.walk(theme) for y in glob(os.path.join(x[0], '*.xml'))]
    # print(*result, sep='\n')

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
                if item.tag in ['area', 'cursor']:
                    name = item.attrib['name']
                    if 'xywh' in item.attrib and item.attrib['xywh'] != '*':
                        x, y, w, h = [int(x) for x in item.attrib['xywh'].split(',')]

                        # print(name, x, y, w, h)

                        if w < 0:
                            continue 

                        if h < 0:
                            h = abs(h)
                        
                        cut = img.crop((x, y, x+w, y+h))
                        if not os.path.exists(output_folder_name):
                            os.makedirs(output_folder_name)
                        cut.save(f'{output_folder_name}/{name}.png')

                elif item.tag == 'select':
                    name = item.attrib['name']
                    areas = item.findall('area')
                    index = 0
                    for area in areas:
                        if 'xywh' in area.attrib and area.attrib['xywh'] != '*':
                            x, y, w, h = [int(x) for x in area.attrib['xywh'].split(',')]

                            # print(name, x, y, w, h)

                            if w < 0:
                                continue 

                            if h < 0:
                                h = abs(h)
                            
                            cut = img.crop((x, y, x+w, y+h))
                            if not os.path.exists(f'{output_folder_name}/{name}'):
                                os.makedirs(f'{output_folder_name}/{name}')
                            cut.save(f'{output_folder_name}/{name}/{name}_{index}.png')
                            index += 1
                elif item.tag == 'grid':
                    name = item.attrib['name']
                    areas = item.findall('area')
                    index = 0
                    for area in areas:
                        if 'xywh' in area.attrib and area.attrib['xywh'] != '*':
                            x, y, w, h = [int(x) for x in area.attrib['xywh'].split(',')]

                            # print(name, x, y, w, h)

                            if w < 0:
                                continue 

                            if h < 0:
                                h = abs(h)
                            
                            cut = img.crop((x, y, x+w, y+h))
                            if not os.path.exists(f'{output_folder_name}/{name}'):
                                os.makedirs(f'{output_folder_name}/{name}')
                            cut.save(f'{output_folder_name}/{name}/{name}_{index}.png')
                            index += 1
                else:
                    search = item.findall('area')
                    for i in search:
                        print(i)


def read_xml(file: str):
    xml_complete = None

    tree = ET.parse(f'{theme}/twl-themer-load.xml', )

    elem_list = []
    elem_dict = {}

    for top_level_elem in tree.getroot():
        elem_list.append(top_level_elem.tag)
        if top_level_elem.tag not in elem_dict:
            elem_dict[top_level_elem.tag] = []
        
        if top_level_elem.tag == 'constantDef':
            for e in [elem for elem in top_level_elem.iter() if elem is not top_level_elem]:
                pass
            elem_dict[top_level_elem.tag].append({top_level_elem.attrib['name']: top_level_elem.text})

    print(elem_dict)
    
def testing(theme_dir: str, file: str):
    print(file)

    document = parse(f'{theme_dir}/{file}')

    for node in document.documentElement.childNodes:
        if node.nodeType == Node.ELEMENT_NODE:
            


            if node.nodeName == 'include' and node.hasAttribute('filename'):
                testing(theme_dir, node.getAttribute('filename'))

if __name__ == '__main__':
    theme = 'default'
    testing(theme, 'twl-themer-load.xml')

    # result = [y for x in os.walk(theme) for y in glob(os.path.join(x[0], '*.xml'))]

    # node_names = []

    # for f in result:
    #     document = parse(f'{f}')

    #     for node in document.documentElement.childNodes:
    #         if node.nodeType == Node.ELEMENT_NODE:
    #             if node.nodeName not in node_names:
    #                 node_names.append(node.nodeName)
    #                 print(node.nodeName)
