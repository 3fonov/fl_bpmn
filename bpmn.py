from lxml import etree
# Обработка исходных строк
def process_line(line,result, current_participant):
    # если строка начинается с PARTICIPANTS, то берем второую половину
    # строки и вытаскиваем из нее участников, разделенных запятыми
    if line.startswith('PARTICIPANTS'):
        participants = line.split('PARTICIPANTS')[1].split(',')
        for participant in participants:
            result[participant.strip()] = {'tasks':[]}
            
    # если строка заканчивается двоеточием, то это пользователь. Обрезаем
    # двоеточие и возвращаем текущего участника
    if line.endswith(':'):
        return line.rstrip(':')
    
    # если строка начинается с START WITH, то берем второую половину
    # строки и вытаскиваем из нее событие начала
    if line.startswith('START WITH'):
        start_event = line.split('START WITH ')[1]
        result[current_participant]['start_event'] = start_event
        
    # если строка начинается с DO, то берем второую половину
    # строки и вытаскиваем из нее действие
    if line.startswith('DO'):
        task = line.split('DO ')[1]
        result[current_participant]['tasks'].append(task)
        
    # если строка начинается с END WITH, то берем второую половину
    # строки и вытаскиваем из нее событие окончания
    if line.startswith('END WITH'):
        end_event = line.split('END WITH ')[1]
        result[current_participant]['end_event'] = end_event

    # возвращаем текущего участника
    return current_participant
  
def parse_data(data):
    # текущий участник
    current_participant = ''
    result = {}
    # обрабатвыаем все не пустые строки
    for line in data.split('\n'):
        if line:
            current_participant = process_line(line.strip(),
                                               result, 
                                               current_participant)
    return result
def make_xml(result):
    # задаем пространства имен xml
    NSMAP = {None : "http://www.omg.org/spec/BPMN/20100524/MODEL",
            'omgdi':"http://www.omg.org/spec/DD/20100524/DI",
             'bpmndi':"http://www.omg.org/spec/BPMN/20100524/DI",
            'omgdc':"http://www.omg.org/spec/DD/20100524/DC",
            'xsi':'http://www.w3.org/2001/XMLSchema-instance'}

    # создаем корневые элементы документа
    root = etree.Element("definitions", nsmap=NSMAP)
    collaboration  = etree.SubElement(root,'collaboration',id="Collaboration_1")
     # создаем базовые элементы графического отображения процесса
    bpmndi_diagram  = etree.SubElement(root,
                                       "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNDiagram",
                                id=f'BpmnDiagram_1')
    bpmndi_plane  = etree.SubElement(bpmndi_diagram,
                                       "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNPlane",
                                     bpmnElement=collaboration.get('id'),
                                id=f'BPMNPlane_1')
    # определяем индексы для идентификаторов элементов
    i = 1
    flow_id=1
    edge_id = 1
    shape_id=1

    # начальные параметры для размещения элементов
    total_width = 0
    total_height = 0
    lane_start = 30
    element_center = 58

    # проходим по каждому участнику
    for participant in result:
        # добавляем участника в блок collaboration
        etree.SubElement(collaboration,
                         'participant',
                         id=f"Participant_{participant}",
                        name=participant,
                        processRef=f'Process_{i:02d}')

       

        # создаем создаем элемента процесса
        process  = etree.SubElement(root,
                                    'process',
                                    id=f'Process_{i:02d}',
                                   isExecutable='false')

        # создаем графическое отображение участника
        bpmndi_user = etree.SubElement(bpmndi_plane,
                                      "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNShape",
                                       bpmnElement="Participant_"+participant,
                           isHorizontal="true"

                                      )
        bpmndi_user_plane_bounds = etree.SubElement(bpmndi_user,
                          "{http://www.omg.org/spec/DD/20100524/DC}Bounds", 
                         x='130', y=str(lane_start),
                         width='0', height='0'                       
                          )
        # увеличиваем общую ширину
        total_width += 130

        # добавляем начальное событие
        start_event = etree.SubElement(process,
                        'startEvent',
                        id=f"StartEvent_{result[participant]['start_event'].replace(' ','_')}",
                       name=result[participant]['start_event'])

        # его графическое отображение
        bpmndi_start_event = etree.SubElement(bpmndi_plane,
                                      "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNShape",
                                       bpmnElement=start_event.get('id') )
        etree.SubElement(bpmndi_start_event,
                          "{http://www.omg.org/spec/DD/20100524/DC}Bounds", 
                         x=str(total_width+80), y=str(lane_start+element_center-18),
                         width='36', height='36')

        # обновляем общую ширину и высоту
        total_width += 80+36
        total_height += element_center + 20

        # и подпись
        bpmndi_start_event_label = etree.SubElement(bpmndi_start_event,
                          "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNLabel")
        etree.SubElement(bpmndi_start_event_label,
                          "{http://www.omg.org/spec/DD/20100524/DC}Bounds", 
                         x=str(total_width-18-35), y=str(lane_start+element_center+20),
                         width='70', height='70')
        total_height += 50

        # задаем исходящую связь
        etree.SubElement(start_event, 'outgoing').text = f"Flow_{flow_id:04d}"
        # и сохраняем идентификатор начального события для следующих связей
        flow_source = start_event.get('id')

        # обрабатываем все задачи в процессе
        for task_name in result[participant]['tasks']:

            # создаем задачу
            task = etree.SubElement(process,
                        'task',
                        id=f"Task_{task_name.replace(' ','_')}",
                       name=task_name)
            # и ее отображение
            bpmndi_task = etree.SubElement(bpmndi_plane,
                                      "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNShape",
                                       bpmnElement=task.get('id'))

            etree.SubElement(bpmndi_task,
                          "{http://www.omg.org/spec/DD/20100524/DC}Bounds", 
                         x=str(total_width+50), y=str(lane_start+element_center-40),
                         width='100', height='80')

            # обновляем ширину
            total_width += 50 + 100

            # задаем идентификатор окончания связи
            flow_target = task.get('id')

            # создаем связь между элементами
            flow = etree.SubElement(process,
                        'sequenceFlow',
                        id=f"Flow_{flow_id:04d}",
                             sourceRef=flow_source,
                             targetRef=flow_target)

            # и ее графическое отображение
            bpmndi_edge = etree.SubElement(bpmndi_plane,
                                      "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNEdge",
                                       bpmnElement=flow.get('id'),
                                          id=f'Edge_{edge_id:04d}')
            etree.SubElement(bpmndi_edge,
                                      "{http://www.omg.org/spec/DD/20100524/DI}waypoint",
                                       x=str(total_width-100-50),y=str(lane_start+element_center))
            etree.SubElement(bpmndi_edge,
                                      "{http://www.omg.org/spec/DD/20100524/DI}waypoint",
                                       x=str(total_width-100),y=str(lane_start+element_center))

            # обновляем счетчики связей и идентификаторы для следующих элементов
            edge_id += 1
            etree.SubElement(task, 'incoming').text = f"Flow_{flow_id:04d}"
            flow_id += 1
            etree.SubElement(task, 'outgoing').text = f"Flow_{flow_id:04d}"
            flow_source = flow_target

        # создаем элемент окончания процесса
        end_event = etree.SubElement(process,
                        'endEvent',
                        id=f"EndEvent_{result[participant]['end_event'].replace(' ','_')}",
                       name=result[participant]['end_event'])

        # его графическое отображение
        bpmndi_end_event = etree.SubElement(bpmndi_plane,
                                      "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNShape",
                                       bpmnElement=end_event.get('id') )
        etree.SubElement(bpmndi_end_event,
                          "{http://www.omg.org/spec/DD/20100524/DC}Bounds", 
                         x=str(total_width+50), y=str(lane_start+element_center - 18),
                         width='36', height='36'

                          )
        # и подпись
        bpmndi_end_event_label = etree.SubElement(bpmndi_end_event,
                          "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNLabel")
        etree.SubElement(bpmndi_end_event_label,
                          "{http://www.omg.org/spec/DD/20100524/DC}Bounds", 
                         x=str(total_width+50-18), y=str(lane_start+element_center+20),
                         width='70', height='70'

                          )
        # обновляем ширину
        total_width += 50
        flow_target = end_event.get('id')

        # создаем связь до окончания процесса
        flow = etree.SubElement(process,
                        'sequenceFlow',
                        id=f"Flow_{flow_id:04d}",
                             sourceRef=flow_source,
                             targetRef=flow_target)
        etree.SubElement(end_event, 'incoming').text = f"Flow_{flow_id:04d}"
        bpmndi_edge = etree.SubElement(bpmndi_plane,
                                      "{http://www.omg.org/spec/BPMN/20100524/DI}BPMNEdge",
                                       bpmnElement=flow.get('id'),
                                          id=f'Edge_{edge_id:04d}')
        etree.SubElement(bpmndi_edge,
                                  "{http://www.omg.org/spec/DD/20100524/DI}waypoint",
                                   x=str(total_width-50),y=str(lane_start+element_center))
        etree.SubElement(bpmndi_edge,
                                  "{http://www.omg.org/spec/DD/20100524/DI}waypoint",
                                   x=str(total_width),y=str(lane_start+element_center))

        # устанавливаем высоту и ширину дорожки процесса
        bpmndi_user_plane_bounds.set('height',str(total_height)) 
        bpmndi_user_plane_bounds.set('width',str(total_width)) 

        # обновляем счетчики
        lane_start += total_height
        total_width = 0
        total_height = 0
        edge_id+=1
        flow_id += 1

        i+=1
        # сохраняем в файл
    with open("bpmn.xml", "wb") as xml_file:
        xml_file.write(etree.tostring(root,xml_declaration=True,
                                      encoding='UTF-8',pretty_print=True))
        
data = """
PARTICIPANTS user
user:
START WITH hunger noticed 
DO open the fridge 
END WITH hunger satisfied
"""
result = parse_data(data)
make_xml(result)
