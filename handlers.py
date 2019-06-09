#!/usr/bin/env python3

import os
import random
import string
import kopf
import kubernetes.client
import psycopg2
import yaml


def connect_to_postgres() -> psycopg2:
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_POST', 5432),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )


@kopf.on.create('k8s.jkroepke.de', 'v1', 'postgresdatabase')
def create_fn(spec: dict, meta: dict, **_):
    name = meta.get('name')
    create_user = spec.get('createUser')

    conn = connect_to_postgres()

    secret_data = {'database-name': name}

    if create_user:
        # https://gist.github.com/23maverick23/4131896
        password = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(32))

        try:
            query = f"CREATE USER \"{0}\" WITH UNENCRYPTED PASSWORD '{1}';".format(name, password)

            with conn.cursor() as cursor:
                cursor.execute(query)

            message = f"Created user {0}.".format(name)
            kopf.info(spec, reason="Create user", message=message)
        except Exception as e:
            message = f"Can't create user: {0}".format(str(e))
            raise kopf.HandlerFatalError(message)

        secret_data['database-user'] = name
        secret_data['database-password'] = password

    try:
        query = f"CREATE DATABASE \"{0}\";".format(name)

        owner = spec.get('owner')
        if not owner:
            query += f" OWNER {0}".format(owner)

        encoding = spec.get('encoding')
        if not encoding:
            query += f" ENCODING {0}".format(encoding)

        lc_collate = spec.get('lcCollate')
        if not lc_collate:
            query += f" LC_COLLATE {0}".format(lc_collate)

        lc_ctype = spec.get('lcCollate')
        if not lc_ctype:
            query += f" LC_CTYPE {0}".format(lc_ctype)

        comment_query = f"COMMENT ON TABLE \"{0}\" IS '{1}';".format(
            name,
            "@".join([
                meta.get('namespace'),
                meta.get('uid')
            ])
        )

        with conn.cursor() as cursor:
            cursor.execute(query)
            cursor.execute(comment_query)

        message = f"Created database {0}.".format(name)
        kopf.info(spec, reason="Create database", message=message)
    except Exception as e:
        message = f"Can't create database: {0}".format(str(e))
        raise kopf.HandlerFatalError(message)

    secret = kubernetes.client.V1Secret(
        api_version="v1",
        kind="Secret",
        metadata={'name': f"postgres-database-{0}".format(name)},
        string_data=secret_data,
    )

    doc = yaml.dump(secret.to_dict())

    # Make it our child: assign the namespace, name, labels, owner references, etc.
    kopf.adopt(doc, owner=spec)

    # Actually create an object by requesting the Kubernetes API.
    api = kubernetes.client.CoreV1Api()
    response = api.create_namespaced_secret(namespace=doc['metadata']['namespace'], body=doc)

    return {'children': [response.metadata.uid]}


@kopf.on.update('k8s.jkroepke.de', 'v1', 'postgresdatabase')
def update_fn(spec: dict, old: dict, new: dict, diff, **_):
    pass


@kopf.on.delete('k8s.jkroepke.de', 'v1', 'postgresdatabase')
def delete_fn(spec: dict, meta: dict, **_):
    name = meta.get('name')
    create_user = spec.get('createUser')
    conn = connect_to_postgres()

    try:
        query = f"DROP DATABASE IF EXISTS \"{0}\";".format(name)
        with conn.cursor() as cursor:
            cursor.execute(query)

        message = f"Delete database {0}.".format(name)
        kopf.info(spec, reason="Delete database", message=message)
    except Exception as e:
        message = 'Failed to delete postgresql database.'
        raise kopf.HandlerFatalError(message)

    if create_user:
        try:
            query = f"DROP USER IF EXISTS \"{0}\";".format(name)
            with conn.cursor() as cursor:
                cursor.execute(query)

            message = f"Delete user {0}.".format(name)
            kopf.info(spec, reason="Delete user", message=message)
        except Exception as e:
            message = 'Failed to delete postgresql user.'
            raise kopf.HandlerFatalError(message)

    return {'message': message}
