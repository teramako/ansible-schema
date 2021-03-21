#!/usr/bin/env python3

import json
import logging
import io

def load(json_file:str) -> dict:
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data

def update_tasks_filepath(path:str, data):
    if type(data) == list:
        for item in data:
            if type(item) in [list,dict]:
                update_tasks_filepath(path, item)
    elif type(data) == dict:
        for key in data:
            value:str = data[key]
            if key == "$ref" and value.startswith("ansible-tasks.json"):
                data[key] = value.replace('ansible-tasks.json', path)
                continue
            if type(data[key]) in [list, dict]:
                update_tasks_filepath(path, data[key])

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Create JSON-Schema for Ansible-Playbook')
    parser.add_argument('-o', '--output', default='ansible-playbook.2.9.json', help='output file')
    parser.add_argument('-t', '--template', default='src/ansible-playbook-template.json', help='template file')
    parser.add_argument('-s', '--taskschema', default='ansible-tasks-2.9.json', help='ansible-tasks schema file')
    args = parser.parse_args()

    try:
        template = load(args.template)
        update_tasks_filepath(args.taskschema, template)
        with open(args.output, 'w') as playbook:
            json.dump(template, playbook, indent=2)
            
        print("Complated successfully: '%s'" % args.output)
        exit(0)
    except Exception as e:
        logging.exception(e)
        exit(1)

if __name__ == '__main__':
    main()