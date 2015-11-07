from os import environ
try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

COMPOSE_FILE = Path(environ.get('COMPOSE_FILE', 'docker-compose.yml')).resolve()
PROJECT_NAME = environ.get('COMPOSE_PROJECT_NAME', COMPOSE_FILE.parent.stem)

def get_project(compose_file=COMPOSE_FILE):
    from compose import __version__ as compose_version
    from compose.config import find, load
    from compose.project import Project
    from compose.cli.docker_client import docker_client

    if compose_version.startswith('1.4'):
        yaml_file = find('.', str(compose_file))
    else:
        # compose >= 1.5
        yaml_file = find('.', [str(compose_file)])

    config = load(yaml_file)
    return Project.from_dicts(PROJECT_NAME, config, docker_client())

def main():
    project = get_project()
    for service in project.get_services():
        if service.name == 'web':
            print(repr(service.options))
            volumes = service.options['volumes']
            assert volumes == sorted(volumes)

if __name__ == '__main__':
    main()
