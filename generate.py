import os
import time
import zipfile
import io
from contextlib import contextmanager
import requests
import yaml
import docker

def yaml_to_json(filename):
    with open(filename) as fp:
        data = yaml.load(fp)
    return data

def _download_zip(url, directory):
    r = requests.get(url, headers={'Content-type': 'application/json'})
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(directory)

def _request_build(json_spec, language):
    url = f'http://localhost:8080/api/gen/clients/{language}'
    options = dict(packageName='ml_api',
                   projectName="ml-api",
                   packageVersion='0.0.1')
    data = dict(options=options, spec=json_spec)
    r = requests.post(url, json=data)
    return 'http://localhost:8080/api/gen/download/' + r.json()['code']

@contextmanager
def container(*args, **kwargs):
    client = docker.from_env()
    container = client.containers.run(*args, **kwargs)
    time.sleep(5)
    try:
        yield container
    finally:
        container.kill()
        container.remove()

def generate_api(json_spec, languages):
    with container('swaggerapi/swagger-generator',
                   ports={8080:8080},
                   detach=True):
        print('container created')
        for lang in languages:
            url = _request_build(json_spec, lang)
            _download_zip(url, 'src/')
            print(f'language {lang} created')


if __name__ == '__main__':
    generate_api(yaml_to_json('api.yaml'), ['python', 'html2'])

