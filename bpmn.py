from lxml import etree
ids = {}
# Обработка исходных строк
def process_line(line,r, current_participant,last_node, current_object):
    if current_participant in r:
        p = r[current_participant]
        if current_object in p['data_objects']:
            d_o = p['data_objects'][current_object]
    # если строка начинается с PARTICIPANTS, то берем второую половину
    # строки и вытаскиваем из нее участников, разделенных запятыми
    
    if line.startswith('PARTICIPANTS'):
        participants = line.split('PARTICIPANTS')[1].split(',')
        for participant in participants:
            r[participant.strip()]={'tasks':{},
                                    'links':[],
                                   'data_objects':{},
                                   'id':get_id('Process')}

    # если строка начинается с DATA OBJECT, то берем второую половину
    # строки и вытаскиваем из нее объекты и их владельцев
    if line.startswith('DATA OBJECT'):
        data_objects = line.split('DATA OBJECT')[1].split(',')
        for data_object in data_objects:
            
            participant = data_object.split(':')[0].strip()
            d_o = data_object.split(':')[1].strip()
            r[participant]['data_objects'][d_o] = {'id':get_id('DataObject')}
      
    # если строка заканчивается двоеточием, то это пользователь. Обрезаем
    # двоеточие и возвращаем текущего участника
    if line.endswith(':'):
        o = line.rstrip(':')
        if o in r:
            return (o,'','')
        else:
            return (current_participant,'',o)
    
    # если строка начинается с START WITH, то берем второую половину
    # строки и вытаскиваем из нее событие начала
    if line.startswith('START WITH'):
        start_event = line.split('START WITH ')[1]
        p['tasks'][start_event] = {'is_start': True,
                      'id': get_id('StartEvent')}
        return (current_participant, start_event,'')
    
    # если строка начинается с END WITH, то берем второую половину
    # строки и вытаскиваем из нее событие окончания
    if line.startswith('END WITH'):
        end_event = line.split('END WITH ')[1]
        p['tasks'][end_event] = {'is_end': True,
                      'id': get_id('EndEvent')}
        link = {'from':last_node,
                'from_id': p['tasks'][last_node]['id'],
                'to':end_event,
                'to_id': p['tasks'][end_event]['id'],
               'id': get_id('Flow')}
        
        p['links'].append(link)
        return (current_participant, '','')
    
    # если строка начинается с DO, то берем второую половину
    # строки и вытаскиваем из нее действие, если есть ключевое слово
    # after, то добавляем ссылки с предыдущих действий
    if line.startswith('DO'):

        do = line.split('DO ')[1].split('AFTER')
        task = do[0].strip()
        p['tasks'][task]={'id':get_id('Task')}
        
        if len(do)==2:
            links = do[1].split('AND')
            for l in links:
                link = {'from':l.strip(),'to':task,
               'id': get_id('Flow'),
                       'from_id':p['tasks'][l.strip()]['id'],
                       'to_id': p['tasks'][task]['id']}
                p['links'].append(link)
        else:
            link = {'from':last_node,'to':task,
               'id': get_id('Flow'),
                   'from_id':p['tasks'][last_node]['id'],
                       'to_id': p['tasks'][task]['id']}
            p['links'].append(link)
        return (current_participant, task,'')
    # если строка начинается с DECIDEOR, то берем второую половину
    # строки и вытаскиваем из нее задачи "или"
    
    if line.startswith('DECIDEOR'):
        decedeor = get_id('DECIDEOR')
        p['tasks'][decedeor]={'id':get_id('Gateway')}        
        link = {'from':last_node,
                'from_id': p['tasks'][last_node]['id'],
                'to':decedeor,
                'to_id': p['tasks'][decedeor]['id'],
               'id': get_id('Flow')}
        p['links'].append(link)
        decedeors = line.split('DECIDEOR ')[1].split('OR')
        for task in decedeors:
            sp = task.split('DO')
            link_name = sp[0].split('IF')[1].strip()
            task_name = sp[1].strip()
            p['tasks'][task_name]={'id':get_id('Task')}
            link = {'from':decedeor,
                    'from_id': p['tasks'][decedeor]['id'],
                    'to':task_name, 
                    'to_id': p['tasks'][task_name]['id'],
                    'name':link_name,
                    'id':get_id('Flow')}
            p['links'].append(link)
            last_node = task_name
        return (current_participant,last_node,'')
    # если строка начинается с DECIDEAND, то берем второую половину
    # строки и вытаскиваем из нее задачи "и"
    if line.startswith('DECIDEAND'):
        decedeand = get_id('DECIDEAND')
        p['tasks'][decedeand]={'id':get_id('Gateway')}                
        link = {'from':last_node,
                'from_id': p['tasks'][last_node]['id'],
                'to':decedeand,
                'to_id': p['tasks'][decedeand]['id'],
                'id': get_id('Flow')}
        p['links'].append(link)
        
        decedeands = line.split('DECIDEAND ')[1].split('AND')
        for task in decedeands:
            sp = task.split('DO')
            link_name = sp[0].split('IF')[1].strip()
            task_name = sp[1].strip()
            p['tasks'][task_name]={'id':get_id('Task')}
            link = {'from':decedeand,
                    'from_id': p['tasks'][decedeand]['id'],
                    'to':task_name, 
                    'to_id': p['tasks'][task_name]['id'],
                    'name':link_name,
               'id': get_id('Flow')}
            p['links'].append(link)
        return (current_participant,'','') 
    # если строка начинается с FROM, то берем второую половину
    # строки и вытаскиваем из нее объект и задачу на него ссылающуюся
    if line.startswith('FROM'):
        task_from = line.split('DO ')[1]
        task_to = current_object
        link = {'from':task_from,
                'from_id':p['tasks'][task_from]['id'],
                    'to':task_to,
                'to_id':p['data_objects'][task_to]['id'],
                'is_do':True,
               'id': get_id('Flow')}
        p['links'].append(link)
    # если строка начинается с FROM, то берем второую половину
    # строки и вытаскиваем из нее объект и задачу на него ссылающуюся        
    if line.startswith('TO'):
        task_to = line.split('DO ')[1]
        task_from = current_object
        link = {'from':task_from,
                'from_id':p['data_objects'][task_from]['id']    ,            
                    'to':task_to,
                'to_id':p['tasks'][task_to]['id']  ,              
                'is_do':True,
               'id': get_id('Flow')}
        p['links'].append(link)
        
    # возвращаем текущего участника
    return (current_participant,last_node, current_object)


def parse_data(data):
    result = {}
    # текущий участник
    current_participant = ''
    current_object = ''
    last_node = ''
    # обрабатвыаем все не пустые строки
    for line in data.split('\n'):
        if line:
            (current_participant,last_node, current_object) = process_line(line.strip(),
                                               result, 
                                               current_participant,
                                               last_node,
                                                current_object)
    return result

# генерируем последовательные идентификаторы
def get_id(name):
    if name in ids:
        ids[name] += 1
    else:
        ids[name] = 1
        
    return f'{name}_{ids[name]:03}'



# ищем все ссылки на (от) этот объект    
def find_flow(name, is_from, p):
    links = []
    for f in p['links']:
        if is_from and f['from']==name:
            links.append(f)
        elif  not is_from and f['to']==name:
            links.append(f)
    return links

# создаем заголовок хмл файла
def generate_xml_base():
    # задаем пространства имен xml
    NSMAP = {None : "http://www.omg.org/spec/BPMN/20100524/MODEL",
            'omgdi':"http://www.omg.org/spec/DD/20100524/DI",
             'bpmndi':"http://www.omg.org/spec/BPMN/20100524/DI",
            'omgdc':"http://www.omg.org/spec/DD/20100524/DC",
            'xsi':'http://www.w3.org/2001/XMLSchema-instance'}
    root = etree.Element("definitions", nsmap=NSMAP)
    return root
    
# разбираем участников
def generate_collaboration(root,data):
    collaboration  = etree.SubElement(root,'collaboration',id="Collaboration_01")
    diagram = root.find("{http://www.omg.org/spec/BPMN/20100524/DI}BPMNDiagram")
    bpmndi_plane  = etree.SubElement(diagram,
                                       "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNPlane",
                                     bpmnElement=collaboration.get('id'),
                                id=f'BPMNPlane_1')
   

    for p in data:
        etree.SubElement(collaboration,
                         'participant',
                         id=f"Participant_{p}",
                        name=p,
                        processRef=data[p]['id'])
        
        

# добавляем связи между объектами
def add_flows(el, name,obj, p, process):

    flows = find_flow(name,True,p)
    for f in flows:
        if 'is_do' in f:
            id = get_id('DataOutputAssociation')
            ass = etree.SubElement(el, 
                             'dataOutputAssociation',
                            id=id)
            f['ass_id'] = id            
            etree.SubElement(ass, 
                             'targetRef').text = p['data_objects'][f['to']]['ref_id']
            
        else:
            etree.SubElement(el, 'outgoing').text = f['id']
            etree.SubElement(process,
                         'sequenceFlow',
                         id=f['id'],
                        targetRef=f['to_id'],
                        sourceRef=f['from_id'])
            
    flows = find_flow(name,False,p)
    for f in flows:
        if 'is_do' in f:
            prop_id = get_id('Property')
            ref_id = get_id('targetRef')
            ass = etree.SubElement(el,
                                   'property',
                            id=prop_id,
                            name=ref_id)
            id = get_id('DataInputAssociation')
            f['ass_id'] = id            
            ass = etree.SubElement(el, 
                             'dataInputAssociation',
                            id=id)
            etree.SubElement(ass, 
                             'sourceRef').text = p['data_objects'][f['from']]['ref_id']
            etree.SubElement(ass, 
                             'targetRef').text = prop_id
        
        else:
            etree.SubElement(el, 'incoming').text = f['id']

# добавляем связи для элементов выбора
def add_decede_sequence_flows(process,t,p,is_exclusive):
    flows = find_flow(t,True,p)
    for f in flows:
        if is_exclusive:
            etree.SubElement(process,
                         'sequenceFlow',
                         id=f['id'],
                        name=f['name'],
                        sourceRef=f['from_id'],
                        targetRef=f['to_id'])
        else:
            etree.SubElement(process,
                         'sequenceFlow',
                         id=f['id'],
                        name=f['name'],
                        targetRef=f['to_id'],
                        sourceRef=f['from_id'])
# создаем задачи
def generate_tasks(process,p):
    for t in p['tasks']:
        task_obj = p['tasks'][t]
        is_exclusive=False
        is_inclusive=False
        if 'is_start' in task_obj:
            task = etree.SubElement(process,
                        'startEvent',
                        id=task_obj['id'],
                       name=t)
        elif 'is_end' in task_obj:
            task = etree.SubElement(process,
                        'endEvent',
                        id=task_obj['id'],
                       name=t)
        
        elif t.startswith('DECIDEOR'):
            task = etree.SubElement(process,
                                    'exclusiveGateway',
                                    id=task_obj['id'])
            is_exclusive = True
        elif t.startswith('DECIDEAND'):
            task = etree.SubElement(process,
                                    'inclusiveGateway',
                                    id=task_obj['id'])
            is_inclusive = True

        else:
            task = etree.SubElement(process,
                                    'task',
                                    id=task_obj['id'],
                                    name=t)
        

        if is_exclusive or is_inclusive:
            add_decede_sequence_flows(process,t,p,is_exclusive)
        else:
            add_flows(task, t,task_obj,p,process)            
# создаем объекты данных
def generate_data_objects(process,p):
    for d_o in p['data_objects']:
        etree.SubElement(process,
                        'dataObject',
                        id=p['data_objects'][d_o]['id'])
        id = get_id('DataObjectReference')
        p['data_objects'][d_o]['ref_id'] = id
        etree.SubElement(process,
                        'dataObjectReference',
                        id=id,
                        name=d_o,
                        dataObjectRef=p['data_objects'][d_o]['id'])
        

# возвращаем габариты объектов на схеме        
def get_element_size(obj):
    if 'is_start' in obj or 'is_end' in obj:
        return {
            'width':36,
            'height':36            
        }
    elif obj['id'].startswith('Gateway'):
        return {
            'width':50,
            'height':50            
        }
    
    return {
            'width':100,
            'height':80            
        }
# получаем следующие за этой задачей задачи
def get_next_tasks(obj,p):
    links = find_flow(obj['name'],True,p)
    tasks = []
    for l in links:
        if 'is_do' in l:
            continue
        task = p['tasks'][l['to']]
        task['name'] = l['to']
        tasks.append(task)
    return tasks

# рисуем объекты
def draw_element(el, obj,p, 
                 left=0,top=0, 
                 total_width=0, total_height=0):
    
    horizontal_offset = 70
    vertical_offset = 50
    size = get_element_size(obj)
    obj['left_x'] = left

    obj['right_x'] = left+size['width']
    
    if 'bounds' in obj:
        obj['bounds'].attrib['x'] = str(left)     
    else:
        shape = etree.SubElement(el,
                                  "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNShape",
                                   bpmnElement=obj['id'],
                                   id=f'{obj["id"]}_id') 

        bounds =  etree.SubElement(shape,
                                  "{http://www.omg.org/spec/DD/20100524/DC}Bounds",
                                   width=str(size['width']),
                                   height=str(size['height']),
                                  x=str(left),
                                  y=str(top - size['height']/2))
        obj['left_y'] = top
        obj['bounds'] = bounds
    
    tasks = get_next_tasks(obj,p)
    for t in tasks:   
        (total_width, total_height) = draw_element(el,t,p,left+ size['width']+horizontal_offset, top,total_width, total_height)        
        top += size['height']+vertical_offset
        
    if left+ size['width'] > total_width:
        total_width = left+ size['width']
    if top> total_height:
        total_height = top
    return (total_width, total_height)
     

# рисуем связи объектов
def draw_edges(el, p):
    for l in p['links']:
        edge_id = get_id('Edge')

        is_do = False
        is_do_from = True
        if 'is_do' in l:
            if l['from_id'].startswith('DataObject'):
                from_obj = p['data_objects'][l['from']]
                to_obj = p['tasks'][l['to']]

            else:
                from_obj = p['tasks'][l['from']]
                to_obj = p['data_objects'][l['to']]

                is_do_from = False
            id = l['ass_id']
            is_do=True
        else:
            from_obj = p['tasks'][l['from']]
            to_obj = p['tasks'][l['to']]
            id = l['id']
        
        edge = etree.SubElement(el,
                              "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNEdge",
                               bpmnElement=id,
                               id=edge_id)
        if is_do and not is_do_from:
            etree.SubElement(edge,
                          "{http://www.omg.org/spec/DD/20100524/DI}waypoint",
                           x=str(from_obj['right_x']-50),
                           y=str(from_obj['left_y']+40))


        else:
            etree.SubElement(edge,
                          "{http://www.omg.org/spec/DD/20100524/DI}waypoint",
                           x=str(from_obj['right_x']),
                           y=str(from_obj['left_y']))
        if not is_do:
            etree.SubElement(edge,
                              "{http://www.omg.org/spec/DD/20100524/DI}waypoint",
                               x=str(from_obj['right_x']+(to_obj['left_x']-from_obj['right_x'])/2),
                               y=str(from_obj['left_y']))
            etree.SubElement(edge,
                              "{http://www.omg.org/spec/DD/20100524/DI}waypoint",
                               x=str(from_obj['right_x']+(to_obj['left_x']-from_obj['right_x'])/2),
                               y=str(to_obj['left_y']))
        if is_do and is_do_from:
            etree.SubElement(edge,
                          "{http://www.omg.org/spec/DD/20100524/DI}waypoint",
                           x=str(to_obj['left_x']+50),
                           y=str(to_obj['left_y']+40))
        else:
            etree.SubElement(edge,
                          "{http://www.omg.org/spec/DD/20100524/DI}waypoint",
                           x=str(to_obj['left_x']),
                           y=str(to_obj['left_y']))
        
        label = etree.SubElement(edge,
                      "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNLabel") 
        etree.SubElement(label,
                          "{http://www.omg.org/spec/DD/20100524/DC}Bounds",
                           x=str(from_obj['right_x']+2),
                           y=str(to_obj['left_y']+2),
                         width='66', height='27')
       
# рисуем объекты данных
def draw_data_objects(el,p, x, y):
    i = 0
    for o in p['data_objects']:

        shape = etree.SubElement(el,
                                  "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNShape",
                                   bpmnElement=p['data_objects'][o]['ref_id'],
                                   id=f'{p["data_objects"][o]["id"]}_id') 

        bounds =  etree.SubElement(shape,
                                  "{http://www.omg.org/spec/DD/20100524/DC}Bounds",
                                   width='36',
                                   height='50',
                                  x=str(i*100 + x - 18),
                                  y=str(y))
        
        p["data_objects"][o]["left_x"] = i*100 + x
        p["data_objects"][o]["right_x"] = i*100 + x
        p["data_objects"][o]["left_y"] = y
        label = etree.SubElement(shape,
                      "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNLabel") 
        etree.SubElement(label,
                          "{http://www.omg.org/spec/DD/20100524/DC}Bounds",
                           x=str(i*100 + x - 28),
                           y=str(y+50),
                         width='56', height='14')
        i+=1
# визуализируем схему
def generate_vizualization(root,p,user):
    bpmndi_plane = root.find("{http://www.omg.org/spec/BPMN/20100524/DI}BPMNDiagram").find("{http://www.omg.org/spec/BPMN/20100524/DI}BPMNPlane")
    bpmndi_user = etree.SubElement(bpmndi_plane,
                                  "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNShape",
                                   bpmnElement=f"Participant_{user}",
                                   id=f"Participant_{user}_id",                                   
                                   isHorizontal="true")    
    bpmndi_user_plane_bounds = etree.SubElement(bpmndi_user,
                          "{http://www.omg.org/spec/DD/20100524/DC}Bounds", 
                         x='130', y='30',
                         width='0', height='0'                       
                          )
    #find start event
    start = {}
    for t in p['tasks']:
        if 'is_start' in p['tasks'][t]:
            start = p['tasks'][t]
            start['name'] = t
            break

    #draw element
    (total_width,total_height) = draw_element(bpmndi_plane, start,p,230,100)
    
    bpmndi_user_plane_bounds.set('height',str(total_height)) 
    bpmndi_user_plane_bounds.set('width',str(total_width)) 
    draw_data_objects(bpmndi_plane,p,230,total_height-70)
    draw_edges(bpmndi_plane, p)



# генерируем процесс  
def generate_process(root,p,user):
    # создаем создаем элемента процесса
    process  = etree.SubElement(root,
                                'process',
                                id=p['id'],
                               isExecutable='false')


    generate_data_objects(process, p)
    generate_tasks(process,p)
    generate_vizualization(root,p,user)
# создаем элемент диаграммы
def generate_diagram(root):
    bpmndi_diagram  = etree.SubElement(root,
                                       "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNDiagram",
                                       id=f'BpmnDiagram_1')
    
    return bpmndi_diagram

#создаем хмл файо
def make_xml(data):
    root = generate_xml_base()

    generate_diagram(root)
    generate_collaboration(root,data)

    for p in data:
        generate_process(root,data[p],p)
        
    with open("bpmn.xml", "wb") as xml_file:
        xml_file.write(etree.tostring(root,xml_declaration=True,
                                      encoding='UTF-8',pretty_print=True))
    

def generate_bpmn(data):
    result = parse_data(data)
    make_xml(result)
    
