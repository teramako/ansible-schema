
TASK_SCHEMA := ansible-tasks-2.9.json
PLAYBOOK_SCHEMA := ansible-playbook-2.9.json

TASK_SCHEMA_TEMPLATE := src/ansible-tasks-template.json
PLAYBOOK_SCHEMA_TEMPLATE := src/ansible-playbook-template.json

ROLE_URL := 'https://json.schemastore.org/ansible-role-2.9'
ROLE_SCHEMA := src/ansible-role-2.9
EXCLUDE_LIST := exclude.lst

.PHONY: clean all

$(ROLE_SCHEMA):
	curl $(ROLE_URL) -o $(ROLE_SCHEMA)

$(TASK_SCHEMA): $(ROLE_SCHEMA) $(TASK_SCHEMA_TEMPLATE) $(EXCLUDE_LIST)
	./create_task_schema.py -o $(TASK_SCHEMA) -t $(TASK_SCHEMA_TEMPLATE) -r $(ROLE_SCHEMA) -e @$(EXCLUDE_LIST)

$(PLAYBOOK_SCHEMA): $(PLAYBOOK_SCHEMA_TEMPLATE)
	./create_playbook_schema.py -o $(PLAYBOOK_SCHEMA) -t $(PLAYBOOK_SCHEMA_TEMPLATE) -s $(TASK_SCHEMA)

clean:
	rm -f $(PLAYBOOK_SCHEMA) $(TASK_SCHEMA)

all: $(TASK_SCHEMA) $(PLAYBOOK_SCHEMA)
