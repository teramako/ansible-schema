#!/usr/bin/env python3
import json
import logging
import io

def create_action_schema(name:str, data:dict) -> dict:
    '''
    1アクションの定義を整形して返す
    '''
    if 'args' in data:
        data['args']['additionalProperties'] = False
        action_schema = {
            "properties": {
                name: data[name],
                "args": data["args"]
            }, "required": [name]
        }
    elif 'properties' in data:
        data['additionalProperties'] = False
        action_schema = {
            "properties": {
                name: data
            }, "required": [name]
        }
    else:
        action_schema = {
            "properties": {
                name: data
            }, "required": [name]
        }
    return {
        "allOf": [
            { "$ref": "#/definitions/task_properties" },
            action_schema
        ]
    }

def load(json_file:str) -> dict:
    '''
    jsonファイルを読み込んで返す
    '''
    with open(json_file, 'r') as jf:
        data = json.load(jf)
    return data
    
def get_actions(json_file:str) -> list:
    '''
    json.schemastore.org からダウンロードしたansible-roleのスキーマを読み込み、
    タスクのアクション部分の定義を整形し、リストで返す
    '''
    data = load(json_file)
    actions = []
    for item in data['items']['anyOf']:
        if 'required' in item and not 'name' in item['required']:
            name = item['required'][0]
            if name in item:
                if "type" in item[name] and item[name]['type'] == 'string':
                    if len(item['properties']) == 0:
                        '''
                        'properties' is not contained in `include`, `import_tasks`, `import_playbook`,
                        and argument is string type only.
                        '''
                        property_schema = { "type": "string", "description": item[name].get('description', '') }
                    else:
                        '''
                        The arguments of `include_vars` and `include_tasks` are either string type or object type
                        '''
                        property_schema = {
                            "oneOf": [
                                { "type": "string", "description": item[name].get('description', '') },
                                { "type": "object", "properties": item['properties'], "additionalProperties": False }
                            ]
                        }
                else:
                    property_schema = { "type": "object", "properties": item['properties'] }
            else:
                '''
                `shell`, `script`, `raw`, `command`
                '''
                property_schema:dict = item['properties']
                if 'name' in property_schema:
                    del property_schema['name']
            actions.append(create_action_schema(name, property_schema))
            continue
        if 'properties' in item:
            props = item['properties']
            for key in props:
                if key == "name":
                    continue
                actions.append(create_action_schema(key, props[key]))
    return actions

def create_task_schema(template_file:str, actions:list) -> dict:
    '''
    ansible-tasksのスキーマとなるテンプレートに、アクション部分の定義リストを加えたものを返す
    '''
    schema = load(template_file)
    for action in actions:
        schema['definitions']['tasks']["anyOf"].append(action)
    return schema

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Create JSON-Schema for Ansible-tasks')
    parser.add_argument('-o', '--output', help='output file', default='ansible-tasks-2.9.json')
    parser.add_argument('-t', '--template', help='template file', default='src/ansible-tasks-template.json')
    parser.add_argument('-r', '--role', help='role file', default='src/ansible-role-2.9')
    args = parser.parse_args()

    try:
        schema = create_task_schema(args.template, get_actions(args.role))
        with open(args.output, 'w') as schema_file:
            json.dump(schema, schema_file, indent=2)

        print("Complated successfully: '%s'." % args.output)
        exit(0)
    except Exception as e:
        logging.exception(e)
        exit(1)

if __name__ == "__main__":
    main()
