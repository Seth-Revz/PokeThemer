from xml.dom.minidom import parse, Node
import os
import shutil
from PIL import Image


def decomp_xml_image_areas(file_path: str, top_level_dir: str):
    absolute_path = os.path.abspath(file_path)
    current_dir = os.path.dirname(absolute_path)
    file_name = os.path.basename(absolute_path)

    document = parse(absolute_path)

    for node in document.documentElement.childNodes:
        if node.nodeType != Node.ELEMENT_NODE:
            continue

        # if node.nodeName == 'constantDef':
        #     if node.firstChild.nodeValue:
        #         constant_definitions[node.getAttribute('name')] = node.firstChild.nodeValue

        if node.nodeName == 'images'and node.hasAttribute('file'):
            image_path = node.getAttribute('file')
            if '.png' not in image_path:
                continue # TODO Find REF to image

            img = Image.open(f'{current_dir}/{image_path}')
            coordinates = []
            output_folder_name = f"{top_level_dir}/theme_decomp/{image_path.split('/')[-1].removesuffix('.png')}"
                
            for child in node.childNodes:
                if child.nodeType != Node.ELEMENT_NODE:
                    continue

                if child.nodeName in ['area', 'cursor'] and child.hasAttribute('xywh'):
                    name = child.getAttribute('name')

                    if child.getAttribute('xywh') == '*':
                        if not os.path.exists(output_folder_name):
                            os.makedirs(output_folder_name)
                        shutil.copyfile(f'{current_dir}/{image_path}', f'{output_folder_name}/{name}.png')

                    if '*' in child.getAttribute('xywh'):
                        continue # TODO Wildcard, might fix later

                    x, y, w, h = [ int(x) for x in child.getAttribute('xywh').split(',') ]
                    if all(i == 0 for i in [x, y, w, h]):
                        continue
                    if (x, y, w, h) in coordinates:
                        continue
                    coordinates.append((x,y,w,h))
                    if w < 0:
                        continue 

                    if h < 0:
                        h = abs(h)
                    
                    sprite = img.crop((x, y, x+w, y+h))
                    if not os.path.exists(output_folder_name):
                        os.makedirs(output_folder_name)
                    sprite.save(f'{output_folder_name}/{name}.png')
                
                elif child.nodeName in ['select', 'grid', 'composed']:
                    name = child.getAttribute('name')
                    index = 0
                    for area in [ node for node in child.childNodes if node.nodeName == 'area' and node.hasAttribute('xywh') ]:
                        if area.getAttribute('xywh') == '*':
                            if not os.path.exists(f'{output_folder_name}/{name}'):
                                os.makedirs(f'{output_folder_name}/{name}')
                            shutil.copyfile(f'{current_dir}/{image_path}', f'{output_folder_name}/{name}/{name}_{index}.png')

                        if '*' in area.getAttribute('xywh'):
                            continue # TODO Wildcard, might fix later

                        x, y, w, h = [int(x) for x in area.getAttribute('xywh').split(',') ]

                        if all(i == 0 for i in [x, y, w, h]):
                            continue
                        if (x, y, w, h) in coordinates:
                            continue
                        coordinates.append((x,y,w,h))

                        if w < 0:
                            continue 

                        if h < 0:
                            h = abs(h)
                        
                        sprite = img.crop((x, y, x+w, y+h))
                        if not os.path.exists(f'{output_folder_name}/{name}'):
                            os.makedirs(f'{output_folder_name}/{name}')
                        # print(f'{output_folder_name}/{name}/{name}_{index}.png')
                        sprite.save(f'{output_folder_name}/{name}/{name}_{index}.png')
                        index += 1
                else:
                    search = child.getElementsByTagName('area')
                    if search:
                        for i in search:
                            print(i, i.parentNode.nodeName, i.parentNode.getAttribute('name'))

        if node.nodeName == 'include' and node.hasAttribute('filename'):
            decomp_xml_image_areas(f"{current_dir}/{node.getAttribute('filename')}", top_level_dir)
    
def rebuild_xml_image_areas(file_path: str, top_level_dir: str):
    absolute_path = os.path.abspath(file_path)
    current_dir = os.path.dirname(absolute_path)
    file_name = os.path.basename(absolute_path)

    document = parse(absolute_path)

    for node in document.documentElement.childNodes:
        if node.nodeType != Node.ELEMENT_NODE:
            continue
        if node.nodeName == 'constantDef':
            continue # TODO

        if node.nodeName == 'images'and node.hasAttribute('file'):
            image_path = node.getAttribute('file')
            if '.png' not in image_path:
                continue # TODO Find REF to image

            img = Image.open(f'{current_dir}/{image_path}')
            coordinates = []
            output_folder_name = f"{top_level_dir}/theme_decomp/{image_path.split('/')[-1].removesuffix('.png')}"
                
            for child in node.childNodes:
                if child.nodeType != Node.ELEMENT_NODE:
                    continue

                if child.nodeName in ['area', 'cursor'] and child.hasAttribute('xywh'):
                    name = child.getAttribute('name')

                    if child.getAttribute('xywh') == '*':
                        shutil.copyfile(f'{output_folder_name}/{name}.png', f'{current_dir}/{image_path}')

                    if '*' in child.getAttribute('xywh'):
                        continue # TODO Wildcard, might fix later

                    x, y, w, h = [ int(x) for x in child.getAttribute('xywh').split(',') ]
                    if all(i == 0 for i in [x, y, w, h]):
                        continue
                    if (x, y, w, h) in coordinates:
                        continue
                    coordinates.append((x,y,w,h))
                    if w < 0:
                        continue 

                    if h < 0:
                        h = abs(h)
                    
                    remove_area = Image.new("RGBA", (w, h), (255, 255, 255, 0))
                    img.paste(remove_area, (x, y))

                    replacement_sprite = Image.open(f'{output_folder_name}/{name}.png')
                    img.paste(replacement_sprite, (x, y))

                    img.save(f'{current_dir}/{image_path}')
                
                elif child.nodeName in ['select', 'grid', 'composed']:
                    name = child.getAttribute('name')
                    index = 0
                    for area in [ node for node in child.childNodes if node.nodeName == 'area' and node.hasAttribute('xywh') ]:
                        if area.getAttribute('xywh') == '*':
                            shutil.copyfile(f'{output_folder_name}/{name}/{name}_{index}.png', f'{current_dir}/{image_path}')

                        if '*' in area.getAttribute('xywh'):
                            continue # TODO Wildcard, might fix later

                        x, y, w, h = [int(x) for x in area.getAttribute('xywh').split(',')]
                        if all(i == 0 for i in [x, y, w, h]):
                            continue
                        if (x, y, w, h) in coordinates:
                            continue
                        coordinates.append((x,y,w,h))

                        if w < 0:
                            continue 

                        if h < 0:
                            h = abs(h)
                        
                        remove_area = Image.new("RGBA", (w, h), (255, 255, 255, 0))
                        img.paste(remove_area, (x, y))

                        replacement_sprite = Image.open(f'{output_folder_name}/{name}/{name}_{index}.png')
                        img.paste(replacement_sprite, (x, y))

                        img.save(f'{current_dir}/{image_path}')
                        index += 1
                else:
                    search = child.getElementsByTagName('area')
                    if search:
                        for i in search:
                            print(i)

        if node.nodeName == 'include' and node.hasAttribute('filename'):
            rebuild_xml_image_areas(f"{current_dir}/{node.getAttribute('filename')}", top_level_dir)

if __name__ == '__main__':
    theme_folder = 'themes'
    temp_folder = 'temp'
    output_folder = 'output'
    
    # theme = 'themes/default'
    theme ='themes/archetype'

    print(os.path.basename(theme))

    if os.path.exists(f'{theme}/twl-themer-load.xml'):
        entry_file = 'twl-themer-load.xml'
    elif os.path.exists(f'{theme}/theme.xml'):
        entry_file = 'theme.xml'
    else:
        print('unknown entry file')
        exit()

    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)
    
    if os.path.exists(f'{temp_folder}/{os.path.basename(theme)}'):
        shutil.rmtree(f'{temp_folder}/{os.path.basename(theme)}')
    modifiable_theme = shutil.copytree(theme, f'{temp_folder}/{os.path.basename(theme)}')

    decomp_xml_image_areas(f'{modifiable_theme}/{entry_file}', os.path.abspath(modifiable_theme))
    
    # modifiable_theme = f'{temp_folder}/{theme}'
    rebuild_xml_image_areas(f'{modifiable_theme}/{entry_file}', os.path.abspath(modifiable_theme))

    if os.path.exists(f'{output_folder}/{theme}'):
        shutil.rmtree(f'{output_folder}/{theme}')
    shutil.copytree(modifiable_theme, f'{output_folder}/{theme}')
    shutil.rmtree(f'{output_folder}/{theme}/theme_decomp')



