<meta name="google-site-verification" content="7GDgH2ehnd6eSCo7SP5EnOQc7L2cneDc6eBceH4j8wA" />
# backup portainer github

[![Docker Pulls](https://img.shields.io/docker/pulls/lepikouze/backup-portainer-github)](https://hub.docker.com/r/lepikouze/backup-portainer-github)
[![GitHub last commit](https://img.shields.io/github/last-commit/lepikouze/backup-portainer-github)](https://github.com/lepikouze/backup-portainer-github/commits/main)
[![GitHub License](https://img.shields.io/github/license/lepikouze/backup-portainer-github)](https://github.com/lepikouze/backup-portainer-github/blob/main/LICENSE)

This Docker container automates the backup of Docker stacks and environment files from Portainer to a GitHub repository. The solution is highly configurable, allowing you to schedule backups at specific intervals or via cron expressions.

## Table of Contents

- [Portainer Backup to GitHub](#portainer-backup-to-github)
  - [Features](#features)
  - [Quick Start](#quick-start)
    - [Docker Compose](#docker-compose)
    - [CLI](#cli)
  - [Environment Variables](#environment-variables)
  - [Volumes](#volumes)
  - [Usage](#usage)
  - [Support](#support)
  - [Contributing](#contributing)
  - [License](#license)
  - [Acknowledgements](#acknowledgements)

## Features

- **Automated Backups**: Schedule regular backups of your Portainer stacks and environment files.
- **Sensitive Information Masking**: Automatically hides sensitive information such as API keys and tokens.
- **Flexible Scheduling**: Choose between cron-based scheduling or time intervals for backups.
- **GitHub Integration**: Commits and pushes updates directly to a specified GitHub repository.

## Quick Start
You can start using this container by deploying it with:

### Docker Compose:

```yaml
version: '3.9'

services:
  backup-portainer-github:
    container_name: ${TARGET_CONTAINER_NAME} 
    image: ghcr.io/lepikouze/backup-portainer-github:latest
    environment:
      PUID: 1000
      PGID: 1000
      PORTAINER_URL: ${PORTAINER_URL}
      PORTAINER_USERNAME: ${PORTAINER_USERNAME}
      PORTAINER_PASSWORD: ${PORTAINER_PASSWORD}
      TARGET_CONTAINER_NAME: ${TARGET_CONTAINER_NAME}
      STACKS_BASE_PATH: /stacks
      GITHUB_USERNAME: ${GITHUB_USERNAME}
      GITHUB_TOKEN: ${GITHUB_TOKEN}
      GITHUB_REPO_NAME: ${GITHUB_REPO_NAME}
      README_TITLE: ${README_TITLE} # Optional
      README_DESCRIPTION: ${README_DESCRIPTION} # Optional
      GITHUB_REPO_PATH: ${GITHUB_REPO_PATH} # Optional
      #CRON_SCHEDULE: 0 0 4 * * 1 # Optional, use this OR INTERVAL_SECONDS, not both
      INTERVAL_SECONDS: 60 # Optional, use this OR CRON_SCHEDULE, not both
    ports:
      - "5000:5000"
    volumes:
      - /folder/data:${GITHUB_REPO_PATH} # Optional
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /portainer_compose_directory:/stacks:ro

    restart: unless-stopped
```
### CLI
```bash
# Set environment variables (replace with your actual values)
export PUID=1000
export PGID=1000
export PORTAINER_URL=https://your-portainer-url
export PORTAINER_USERNAME=your-portainer-username
export PORTAINER_PASSWORD=your-portainer-password
export TARGET_CONTAINER_NAME=portainer-backup
export STACKS_BASE_PATH=/stacks
export GITHUB_USERNAME=your-github-username
export GITHUB_TOKEN=your-github-token
export GITHUB_REPO_NAME=your-github-repo-name
export README_TITLE="Portainer Backup Automation"  # Optional
export README_DESCRIPTION="Automated backup of Portainer stacks and environment files."  # Optional
export GITHUB_REPO_PATH=/folder/data/repo  # Optional
# export CRON_SCHEDULE="0 0 4 * * 1"  # Optional, uncomment if using cron schedule
export INTERVAL_SECONDS=60 # Optional, comment if using cron schedule

# Run the Docker container
docker run -d \
  --name $TARGET_CONTAINER_NAME \
  --env PUID=$PUID \
  --env PGID=$PGID \
  --env PORTAINER_URL=$PORTAINER_URL \
  --env PORTAINER_USERNAME=$PORTAINER_USERNAME \
  --env PORTAINER_PASSWORD=$PORTAINER_PASSWORD \
  --env TARGET_CONTAINER_NAME=$TARGET_CONTAINER_NAME \
  --env STACKS_BASE_PATH=$STACKS_BASE_PATH \
  --env GITHUB_USERNAME=$GITHUB_USERNAME \
  --env GITHUB_TOKEN=$GITHUB_TOKEN \
  --env GITHUB_REPO_NAME=$GITHUB_REPO_NAME \
  --env README_TITLE="$README_TITLE" \  # Optional
  --env README_DESCRIPTION="$README_DESCRIPTION" \  # Optional
  --env GITHUB_REPO_PATH=$GITHUB_REPO_PATH \  # Optional
  --env INTERVAL_SECONDS=$INTERVAL_SECONDS \  # Optional, use this OR CRON_SCHEDULE, not both
  -p 5000:5000 \
  -v /folder/data:$GITHUB_REPO_PATH \ # Optional
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v /portainer_compose_directory:/stacks:ro \
  ghcr.io/lepikouze/backup-portainer-github:latest \
  --restart unless-stopped
```


## Environment Variables

| Name                  | Description                                                                                       | Default                                |
| --------------------- | ------------------------------------------------------------------------------------------------- | -------------------------------------- |
| `PUID`                | User ID for file permissions within the container.                                                | `1000`                                 |
| `PGID`                | Group ID for file permissions within the container.                                               | `1000`                                 |
| `PORTAINER_URL`       | The URL of the Portainer instance to be backed up.                                                | **Required**                              |
| `PORTAINER_USERNAME`  | Username for Portainer authentication.                                                            | **Required**                               |
| `PORTAINER_PASSWORD`  | Password for Portainer authentication.                                                            | **Required**                              |
| `TARGET_CONTAINER_NAME` | The name of this backup container within the Portainer environment.                             | **Required**                               |
| `STACKS_BASE_PATH`    | Path inside the container where the Portainer stacks are stored.                                  | `/stacks`                              |
| `GITHUB_USERNAME`     | GitHub username to authenticate and push backups.                                                 | **Required**                               |
| `GITHUB_TOKEN`        | GitHub personal access token to authenticate and push backups.                                    | **Required**                               |
| `GITHUB_REPO_NAME`    | Name of the GitHub repository where backups are stored.                                           | **Required**                               |
| `README_TITLE`        | Title for the `README.md` file in the GitHub repository.                                          | `Portainer Backup Automation`          |
| `README_DESCRIPTION`  | Description for the `README.md` file in the GitHub repository.                                    | `Automated backup of Portainer stacks and environment files.` |
| `GITHUB_REPO_PATH`    | Local path inside the container where the GitHub repository is cloned.                            | `/tmp/repo`                            |
| `CRON_SCHEDULE`       | (Optional) Cron expression for scheduling backups.                                                | `use this OR INTERVAL_SECONDS, not both`                                 |
| `INTERVAL_SECONDS`    | (Optional) Interval in seconds between each backup execution.                                     | `use this OR CRON_SCHEDULE, not both`                                 |

## Volumes

| Path (Host)                                      | Path (Container)                      | Description                                                                |
| ------------------------------------------------ | ------------------------------------- | -------------------------------------------------------------------------- |
| `/folder/data`                   | `${GITHUB_REPO_PATH}`                 | Directory where backup data will be stored inside the container.           |
| `/var/run/docker.sock`                           | `/var/run/docker.sock:ro`             | Docker socket to interact with the Docker API on the host (read-only).     |
| `/portainer_compose_directory`                 | `/stacks:ro`                          | Directory containing Portainer stacks, mounted in read-only mode.          |

## Usage

### Build and Run the Container

Clone the repository and navigate to its directory:

```bash
git clone https://github.com/lepikouze/backup-portainer-github.git
cd backup-portainer-github
docker-compose up -d
```

### Access the Web Interface:
Once the container is running, you can access the web interface via: 
```bash
http://localhost:5000
```
## Support

For support, please open an issue in the [GitHub repository](https://github.com/lepikouze/backup-portainer-github/issues). When reporting issues, please include logs and relevant configuration details to help with troubleshooting.


## Contributing

Contributions are welcome! Please submit a Pull Request or open an Issue to discuss any changes or improvements.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

This project was inspired by [SavageSoftware/portainer-backup](https://github.com/SavageSoftware/portainer-backup).





