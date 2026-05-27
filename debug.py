#!/usr/bin/env -S uv run
# import click

# from linux_host.deploy_linux_host.linux_host_deploy_config import linux_host_deploy_config
# from linux_host.deploy_linux_host.tasks_linux_host import upload_jsonc_config_and_certs
# from shared_lib.deploy_shared.cli_helpers import common_options, get_connection


# @click.group()
# def cli():
#     pass


# @cli.command()
# @common_options
# def debug(hostname: str, user: str | None, port: int | None, noninteractive: bool):
#     if not noninteractive and not click.confirm(f'Run script on {hostname}?'):
#         return

#     jsonc_config_path = linux_host_deploy_config.local_linux_host_config_dir / 'config.jsonc'
#     c = get_connection(hostname, user, port)
#     upload_jsonc_config_and_certs(c, jsonc_config_path)


# if __name__ == '__main__':
#     cli()
