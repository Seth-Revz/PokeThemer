from xml.dom.minidom import parse, Node
import os
import shutil
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
            output_folder_name = f"{theme_dir}/theme_decomp/{image_path.split('/')[-1].removesuffix('.png')}"
                
            for child in node.childNodes:
                if child.nodeType != Node.ELEMENT_NODE:
                    continue

                if child.nodeName in ['area', 'cursor'] and child.hasAttribute('xywh'):
                    name = child.getAttribute('name')

                    if child.getAttribute('xywh') == '*':
                        if not os.path.exists(output_folder_name):
                            os.makedirs(output_folder_name)
                        shutil.copyfile(f'{theme_dir}/{image_path}', f'{output_folder_name}/{name}.png')

                    if '*' in child.getAttribute('xywh'):
                        continue # TODO Wildcard, might fix later

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
                        if child.getAttribute('xywh') == '*':
                            if not os.path.exists(f'{output_folder_name}/{name}'):
                                os.makedirs(f'{output_folder_name}/{name}')
                            shutil.copyfile(f'{theme_dir}/{image_path}', f'{output_folder_name}/{name}/{name}_{index}.png')

                        if '*' in child.getAttribute('xywh'):
                            continue # TODO Wildcard, might fix later

                        x, y, w, h = [int(x) for x in area.getAttribute('xywh').split(',')]
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
                        sprite.save(f'{output_folder_name}/{name}/{name}_{index}.png')
                        index += 1
                else:
                    search = child.getElementsByTagName('area')
                    if search:
                        for i in search:
                            print(i)

        if node.nodeName == 'include' and node.hasAttribute('filename'):
            decomp_xml_image_areas(theme_dir, node.getAttribute('filename'), constant_definitions)
    
def rebuild_xml_image_areas(theme_dir: str, file: str):
    document = parse(f'{theme_dir}/{file}')

    for node in document.documentElement.childNodes:
        if node.nodeType != Node.ELEMENT_NODE:
            continue

        if node.nodeName == 'constantDef':
            continue # TODO

        if node.nodeName == 'images'and node.hasAttribute('file'):
            image_path = node.getAttribute('file')
            if '.png' not in image_path:
                continue # TODO Find REF to image

            img = Image.open(f'{theme_dir}/{image_path}')
            coordinates = []
            output_folder_name = f"{theme_dir}/theme_decomp/{image_path.split('/')[-1].removesuffix('.png')}"
                
            for child in node.childNodes:
                if child.nodeType != Node.ELEMENT_NODE:
                    continue

                if child.nodeName in ['area', 'cursor'] and child.hasAttribute('xywh'):
                    name = child.getAttribute('name')

                    if child.getAttribute('xywh') == '*':
                        shutil.copyfile(f'{output_folder_name}/{name}.png', f'{theme_dir}/{image_path}')

                    if '*' in child.getAttribute('xywh'):
                        continue # TODO Wildcard, might fix later

                    x, y, w, h = [int(x) for x in child.getAttribute('xywh').split(',')]

                    if w < 0:
                        continue 

                    if h < 0:
                        h = abs(h)
                    
                    remove_area = Image.new("RGBA", (w, h), (255, 255, 255, 0))
                    img.paste(remove_area, (x, y))

                    replacement_sprite = Image.open(f'{output_folder_name}/{name}.png')
                    img.paste(replacement_sprite, (x, y))

                    img.save(f'{theme_dir}/{image_path}')
                
                elif child.nodeName in ['select', 'grid']:
                    name = child.getAttribute('name')
                    index = 0
                    for area in [ node for node in child.childNodes if node.nodeName == 'area' and node.hasAttribute('xywh') ]:
                        if child.getAttribute('xywh') == '*':
                            shutil.copyfile(f'{output_folder_name}/{name}/{name}_{index}.png', f'{theme_dir}/{image_path}')

                        if '*' in child.getAttribute('xywh'):
                            continue # TODO Wildcard, might fix later

                        x, y, w, h = [int(x) for x in area.getAttribute('xywh').split(',')]
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

                        img.save(f'{theme_dir}/{image_path}')
                        index += 1
                else:
                    search = child.getElementsByTagName('area')
                    if search:
                        for i in search:
                            print(i)

        if node.nodeName == 'include' and node.hasAttribute('filename'):
            rebuild_xml_image_areas(theme_dir, node.getAttribute('filename'))

if __name__ == '__main__':
    theme_folder = 'themes'
    temp_folder = 'temp'
    output_folder = 'output'

    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)
    
    # theme = 'default'
    # entry_file = 'twl-themer-load.xml'

    theme = 'archetype'
    entry_file = 'theme.xml'
    # IN UI ASK FOR ENTRY FILE
    
    if os.path.exists(f'{temp_folder}/{theme}'):
        shutil.rmtree(f'{temp_folder}/{theme}')
    modifiable_theme = shutil.copytree(f'{theme_folder}/{theme}', f'{temp_folder}/{theme}')

    decomp_xml_image_areas(modifiable_theme, entry_file)
    
    # modifiable_theme = f'{temp_folder}/{theme}'
    # rebuild_xml_image_areas(modifiable_theme, entry_file)

    # if os.path.exists(f'{output_folder}/{theme}'):
    #     shutil.rmtree(f'{output_folder}/{theme}')
    # shutil.copytree(modifiable_theme, f'{output_folder}/{theme}')
    # shutil.rmtree(f'{output_folder}/{theme}/theme_decomp')



