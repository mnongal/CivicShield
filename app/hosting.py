"""Explicit host configuration for local development and Render."""
import os


def allowed_hosts():
    hosts = ['127.0.0.1', 'localhost', '[::1]', 'testserver']
    render_host = os.getenv('RENDER_EXTERNAL_HOSTNAME', '').strip()
    if render_host:
        hosts.append(render_host)
    hosts.extend(host.strip() for host in os.getenv('ALLOWED_HOSTS', '').split(',') if host.strip())
    return hosts
