#!/usr/bin/env python3
import json
import logging
import io
import copy

OTHER_RPROPERTIES = {
    "_": "#/definitions/task_properties",
    "import_role": "#/definitions/common_properties"
}
ACTION_LIST = {
    "set_fact": "src/action-set_fact.json"
}
EXCLUDE_ACTION_LIST = [
    "name",
    "import_playbook"
]
ACTION_DESCRIPTION = {
    "include_vars": "Load variables from files, dynamically within a task",
    "include_tasks": "Dynamically include a task list",
    "include": "Include a play or task list",
    "import_tasks": "Import a task list",
    "shell": "Execute shell commands on targets",
    "script": "Runs a local script on a remote node after transferring it",
    "raw": "Executes a low-down and dirty command",
    "command": "Execute commands on targets"
}
def get_additional_properties_ref(name:str) -> str:
    return OTHER_RPROPERTIES.get(name, OTHER_RPROPERTIES["_"])

def load(json_file:str) -> dict:
    '''
    jsonファイルを読み込んで返す
    '''
    with open(json_file, 'r') as jf:
        data = json.load(jf)
    return data

class ActionSchema:
    '''
    Ansible action-schema generator
    '''
    def __init__(self, name:str, description:str, arguments:dict,
                actionType:str='object', additionalProperties:bool=False):
        self.name = name
        if name in ACTION_DESCRIPTION and len(description) == 0:
            self.description = ACTION_DESCRIPTION[name]
        else:
            self.description = description
        self.arguments = arguments
        self.type = actionType
        self.additionalProperties= additionalProperties

    def update_schema(self, schema:dict):
        schema['definitions']['tasks']['anyOf'].append(self.get_property_scehma())

    def get_property_scehma(self) -> dict:
        '''
        generate action property schema
        '''
        args = copy.copy(self.arguments)
        args['additionalProperties'] = self.additionalProperties
        if self.type == 'string':
            return {
                "title": "Action: %s" % self.name,
                "allOf": [
                    {
                        "properties": {
                            self.name: { "type": "string", "description": self.description }
                        },
                        "required": [self.name]
                    },
                    { "$ref": get_additional_properties_ref(self.name) }
                ]
            }
        elif self.type == 'complex':
            return {
                "title": "Action: %s" % self.name,
                "allOf": [
                    {
                        "properties": {
                            self.name: {
                                "description": self.description,
                                "oneOf": [
                                    { "type": "string" },
                                    args
                                ]
                            }
                        },
                        "required": [self.name]
                    },
                    { "$ref": get_additional_properties_ref(self.name) }
                ]
            }
        elif self.type == 'shell':
            return {
                "title": "Action: %s" % self.name,
                "allOf": [
                    {
                        "properties": {
                            self.name: {
                                "type": "string",
                                "description": self.description
                            },
                            "args": args
                        },
                        "required": [self.name]
                    },
                    { "$ref": get_additional_properties_ref(self.name) }
                ]
            }
        else:
            args['description'] = self.description
            return {
                "title": "Action: %s" % self.name,
                "allOf": [
                    {
                        "properties": {
                            self.name: args
                        },
                        "required": [self.name]
                    },
                    { "$ref": get_additional_properties_ref(self.name) }
                ]
            }


def get_actions(json_file:str) -> iter:
    '''
    json.schemastore.org からダウンロードしたansible-roleのスキーマを読み込み、
    タスクのアクション部分の定義を整形し、リストで返す
    '''
    data = load(json_file)
    actions = []
    for item in data['items']['anyOf']:
        if 'name' in item.get('required', []):
            props = item.get('properties', {})
            for key in props:
                if key in EXCLUDE_ACTION_LIST:
                    continue
                prop = props[key]
                if key in ACTION_LIST:
                    data = load(ACTION_LIST[key])
                    prop = data['properties'][key]
                desc = prop.get('description', '')
                additionalProperties = prop.get('additionalProperties', False)
                if 'description' in prop:
                    del prop['description']
                yield ActionSchema(key, desc, prop, additionalProperties)

        else:
            name = item['required'][0]
            if name in EXCLUDE_ACTION_LIST:
                continue
            props = item.get('properties', {})
            if name in item:
                desc = item[name].get('description', '')
                if len(props) == 0:
                    yield ActionSchema(name, desc, {}, 'string')
                else:
                    yield ActionSchema(name, desc, {"type":"object", "properties": props}, 'complex')
            else:
                if 'name' in props:
                    del props['name']
                desc = props[name].get('description', '')
                yield ActionSchema(name, desc, props.get('args', {}), 'shell')

def create_task_schema(template_file:str, actions:list[ActionSchema]) -> dict:
    '''
    ansible-tasksのスキーマとなるテンプレートに、アクション部分の定義リストを加えたものを返す
    '''
    schema = load(template_file)
    for action in actions:
        action.update_schema(schema)
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
