import os
import requests
import git
import logging
from git import Repo, InvalidGitRepositoryError
from datetime import datetime
from flask import Flask, render_template_string, redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import time

app = Flask(__name__)

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment variables
PORTAINER_URL = os.getenv('PORTAINER_URL', 'http://localhost:9000')
USERNAME = os.getenv('PORTAINER_USERNAME')
PASSWORD = os.getenv('PORTAINER_PASSWORD')
CONTAINER_NAME = os.getenv('TARGET_CONTAINER_NAME', 'backup_portainer')
STACKS_BASE_PATH = os.getenv('STACKS_BASE_PATH', '/stacks')

GITHUB_USERNAME = os.getenv('GITHUB_USERNAME')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO_NAME = os.getenv('GITHUB_REPO_NAME')
GITHUB_REPO_URL = f"https://{GITHUB_USERNAME}:{GITHUB_TOKEN}@github.com/{GITHUB_USERNAME}/{GITHUB_REPO_NAME}.git"
GITHUB_REPO_PATH = os.getenv('GITHUB_REPO_PATH', '/tmp/repo')  # Default to /tmp/repo

README_TITLE = os.getenv('README_TITLE', 'Backup Portainer')
README_DESCRIPTION = os.getenv('README_DESCRIPTION', 'Backup all stacks and .env from portainer')

# List of sensitive keywords to mask
SENSITIVE_KEYWORDS = ['token', 'key', 'password', 'secret', 'apikey', 'api_key']

if not GITHUB_USERNAME or not GITHUB_TOKEN or not GITHUB_REPO_NAME:
    raise ValueError("GITHUB_USERNAME, GITHUB_TOKEN, or GITHUB_REPO_NAME is not defined. Please set these environment variables.")

def get_portainer_token():
    """
    Fetches an authentication token from Portainer.
    """
    logger.info("Fetching Portainer authentication token.")
    url = f"{PORTAINER_URL}/api/auth"
    payload = {"username": USERNAME, "password": PASSWORD}
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()["jwt"]

def get_endpoints(token):
    """
    Retrieves a list of endpoints from Portainer.
    """
    logger.info("Fetching endpoints from Portainer.")
    url = f"{PORTAINER_URL}/api/endpoints"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_stacks(token):
    """
    Retrieves a list of stacks from Portainer.
    """
    logger.info("Fetching stacks from Portainer.")
    url = f"{PORTAINER_URL}/api/stacks"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_containers(token, endpoint_id):
    """
    Retrieves a list of containers for a specific endpoint from Portainer.
    """
    logger.info(f"Fetching containers for endpoint ID {endpoint_id}.")
    url = f"{PORTAINER_URL}/api/endpoints/{endpoint_id}/docker/containers/json?all=true"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def check_or_clone_repo():
    """
    Checks if the GitHub repository is already cloned locally.
    If not, it clones the repository to the specified path.
    """
    if os.path.exists(GITHUB_REPO_PATH):
        try:
            repo = Repo(GITHUB_REPO_PATH)
            if repo.bare:
                raise InvalidGitRepositoryError
            logger.info("The directory is a valid Git repository.")
        except InvalidGitRepositoryError:
            logger.info("The directory is not a valid Git repository. Cloning the repository...")
            repo = Repo.clone_from(GITHUB_REPO_URL, GITHUB_REPO_PATH)
    else:
        logger.info("The directory does not exist. Cloning the repository...")
        repo = Repo.clone_from(GITHUB_REPO_URL, GITHUB_REPO_PATH)
    return repo

def filter_sensitive_info(content):
    """
    Masks sensitive information in the given content.
    """
    lines = content.splitlines()
    filtered_lines = []
    for line in lines:
        for keyword in SENSITIVE_KEYWORDS:
            if keyword in line.lower():
                key, value = line.split('=', 1)
                line = f"{key}=XXXXX"
                break
        filtered_lines.append(line)
    return '\n'.join(filtered_lines)

def read_file_content(path):
    """
    Reads the content of a file at the specified path.
    Returns an error message if the file does not exist.
    """
    try:
        with open(path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        return f"{os.path.basename(path)} not found"
    except Exception as e:
        return f"Error reading {os.path.basename(path)}: {str(e)}"

def read_docker_compose_file(stack_id):
    """
    Reads the docker-compose.yml file for a given stack ID.
    """
    compose_file_path = os.path.join(STACKS_BASE_PATH, str(stack_id), 'docker-compose.yml')
    return read_file_content(compose_file_path)

def read_env_file(stack_id):
    """
    Reads the stack.env file for a given stack ID and filters out sensitive information.
    """
    env_file_path = os.path.join(STACKS_BASE_PATH, str(stack_id), 'stack.env')
    content = read_file_content(env_file_path)
    return filter_sensitive_info(content)

def remove_deleted_stacks(repo, endpoints, stacks):
    """
    Removes folders corresponding to deleted stacks from the GitHub repository.
    """
    existing_stack_names = set(stack['Name'] for stack in stacks)

    for endpoint in endpoints:
        endpoint_dir = os.path.join(GITHUB_REPO_PATH, endpoint['Name'])
        if not os.path.exists(endpoint_dir):
            continue

        for stack_dir in os.listdir(endpoint_dir):
            if stack_dir not in existing_stack_names:
                full_path = os.path.join(endpoint_dir, stack_dir)
                if os.path.isdir(full_path):
                    logger.info(f"Removing obsolete directory: {full_path}")
                    repo.git.rm('-r', full_path)
                    repo.index.commit(f"Remove obsolete stack: {stack_dir}")

def update_readme(repo, endpoints, stacks):
    """
    Updates the README.md file in the GitHub repository with information about the stacks.
    """
    readme_path = os.path.join(GITHUB_REPO_PATH, 'README.md')
    with open(readme_path, 'w') as f:
        f.write(f"# {README_TITLE}\n\n")
        f.write(f"{README_DESCRIPTION}\n\n")

        for endpoint in endpoints:
            f.write(f"## Node {endpoint['Name']}\n")
            f.write("| STATUS | CONTAINER | Published Ports | DATE LAST UPDATE |\n")
            f.write("| --------------- | --------------- | --------------- | --------------- |\n")

            containers = get_containers(get_portainer_token(), endpoint['Id'])
            for container in containers:
                status_icon = "🟢" if container['State'] == "running" else "🔴"
                container_name = container['Names'][0].lstrip('/')  # Remove leading "/"

                # Filter to show only publicly accessible ports and remove duplicates
                ports = set([str(p['PublicPort']) for p in container.get('Ports', []) if 'PublicPort' in p])
                ports_str = ", ".join(sorted(ports))  # Sort to ensure consistent ordering

                last_update = datetime.now().strftime("%d/%m/%Y")
                f.write(f"| {status_icon} | {container_name} | {ports_str or 'N/A'} | {last_update} |\n")
            f.write("\n")

def backup_to_github(token, endpoints, stacks):
    """
    Backs up Portainer stacks and their associated files to the GitHub repository.
    """
    # Check or clone the GitHub repository
    repo = check_or_clone_repo()

    updated_stacks = set()

    # Remove folders corresponding to deleted stacks
    remove_deleted_stacks(repo, endpoints, stacks)

    # Organize the files according to the structure
    for endpoint in endpoints:
        endpoint_name = endpoint['Name']
        endpoint_dir = os.path.join(GITHUB_REPO_PATH, endpoint_name)
        os.makedirs(endpoint_dir, exist_ok=True)

        endpoint_stacks = [stack for stack in stacks if stack['EndpointId'] == endpoint['Id']]
        for stack in endpoint_stacks:
            stack_name = stack['Name']
            stack_dir = os.path.join(endpoint_dir, stack_name)
            os.makedirs(stack_dir, exist_ok=True)

            # Save docker-compose.yml
            compose_content = read_docker_compose_file(stack['Id'])
            compose_file_path = os.path.join(stack_dir, 'docker-compose.yml')
            with open(compose_file_path, 'w') as f:
                f.write(compose_content)
                updated_stacks.add(stack_name)
                logger.info(f"Updated: {stack_name}/docker-compose.yml")

            # Save stack.env if exists
            env_content = read_env_file(stack['Id'])
            if 'not found' not in env_content:  # Check if stack.env exists
                env_file_path = os.path.join(stack_dir, 'stack.env')
                with open(env_file_path, 'w') as f:
                    f.write(env_content)
                    updated_stacks.add(stack_name)
                    logger.info(f"Updated: {stack_name}/stack.env")

    # Update README.md
    update_readme(repo, endpoints, stacks)
    updated_stacks.add("README.md")
    logger.info("Updated: README.md")

    # Commit and push to GitHub
    if updated_stacks:
        repo.git.add(A=True)
        commit_message = "Update: " + ", ".join(sorted(updated_stacks))  # Sort for consistent order
        repo.index.commit(commit_message)
        origin = repo.remote(name='origin')
        origin.push()
        logger.info(f"Commit and push completed: {commit_message}")

def scheduled_backup():
    """
    Executes the scheduled backup process.
    """
    logger.info("Executing scheduled backup...")
    token = get_portainer_token()
    endpoints = get_endpoints(token)
    stacks = get_stacks(token)
    backup_to_github(token, endpoints, stacks)
    logger.info("Backup completed.")

def setup_scheduler():
    """
    Sets up the background scheduler to run the backup at specified intervals or cron schedules.
    """
    scheduler = BackgroundScheduler()

    # Read environment variables for cron and interval schedules
    cron_schedule = os.getenv('CRON_SCHEDULE')  # e.g., "0 0 4 * * 1" (every Monday at 4 AM)
    interval_seconds = os.getenv('INTERVAL_SECONDS')  # e.g., 3600 for every hour

    if cron_schedule:
        logger.info(f"Setting up cron schedule: {cron_schedule}")
        trigger = CronTrigger.from_crontab(cron_schedule)
        scheduler.add_job(scheduled_backup, trigger)

    if interval_seconds:
        logger.info(f"Setting up interval schedule: {interval_seconds} seconds")
        trigger = IntervalTrigger(seconds=int(interval_seconds))
        scheduler.add_job(scheduled_backup, trigger)

    scheduler.start()

@app.route('/')
def display_stacks():
    """
    Displays the Portainer stacks and their status on the web interface.
    """
    token = get_portainer_token()
    endpoints = get_endpoints(token)
    stacks = get_stacks(token)

    output = f"<h1>Container Name Check: {CONTAINER_NAME}</h1>"
    output += '<form action="/backup" method="post"><button type="submit">Backup to GitHub</button></form>'

    for endpoint in endpoints:
        output += f"<h2>Processing endpoint: {endpoint['Name']} (ID: {endpoint['Id']})</h2>"
        endpoint_stacks = [stack for stack in stacks if stack['EndpointId'] == endpoint['Id']]

        for stack in endpoint_stacks:
            output += f"<h3>Stack: {stack['Name']}</h3>"
            output += f"<p>Status: {stack['Status']}</p>"

            config_path = stack.get('ProjectPath')
            if config_path:
                output += f"<p>Config Path: {config_path}</p>"

                # Read and display the content of docker-compose.yml
                compose_content = read_docker_compose_file(stack['Id'])
                output += f"<pre>{compose_content}</pre>"

                # Read and display the content of stack.env
                env_content = read_env_file(stack['Id'])
                output += f"<h4>Environment Variables:</h4><pre>{env_content}</pre>"

    return render_template_string(output)

@app.route('/backup', methods=['POST'])
def backup():
    """
    Manually triggers the backup process to GitHub.
    """
    logger.info("Manual backup triggered.")
    token = get_portainer_token()
    endpoints = get_endpoints(token)
    stacks = get_stacks(token)
    backup_to_github(token, endpoints, stacks)
    logger.info("Manual backup completed.")
    return redirect(url_for('display_stacks'))

if __name__ == '__main__':
    logger.info("Starting application.")
    check_or_clone_repo()  # Check or clone the repository at startup
    setup_scheduler()  # Set up the scheduler

    app.run(host='0.0.0.0', port=5000)

    # Keep the application running
    while True:
        time.sleep(1)
