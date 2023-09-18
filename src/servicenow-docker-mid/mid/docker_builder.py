import os

import requests
import csv
import subprocess
import argparse
import zipfile
from dotenv import load_dotenv
import docker


def generate_download_links(data, country, platform):
    download_links = []

    for row in data:
        api_url, date, tags = row
        date1 = date.split('_')[0]
        year1 = date1.split('-')[2]
        month1 = date1.split('-')[0]
        day1 = date1.split('-')[1]
        tag_parts = tags.split('-')
        tag = '-'.join(tag_parts[1:])  # Remove "glide-" prefix
        template = f"https://install.service-now.com/glide/distribution/builds/package/app-signed/mid-{platform}-container-recipe/{year1}/{month1}/{day1}/mid-{platform}-container-recipe.{tag}_{date}.{platform}.x86-64.zip"
        download_links.append(template)

    print(download_links)

    return download_links


def download_and_build(download_links, platform):
    for link in download_links:
        # Download the package from the link
        response = requests.get(link, stream=True)
        if response.status_code == 200:
            filename = link.split("/")[-1]
            with open(filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Downloaded {filename}")

            # Create a folder with the same name as the zip file
            folder_name = os.path.splitext(filename)[0]
            os.makedirs(folder_name, exist_ok=True)

            # Unzip the downloaded package into the folder
            with zipfile.ZipFile(filename, "r") as zip_ref:
                zip_ref.extractall(folder_name)

            os.remove(filename)  # Remove the zip file after extraction

            docker_client = docker.from_env()

            # Load the DOCKER_TAG environment variable from the .env file
            load_dotenv(dotenv_path=f"{folder_name}/.env")
            docker_tag = os.getenv("DOCKER_TAG")

            # Run Docker command inside the extracted folder
            print(docker_tag)
            docker_image_name = docker_tag.split(':')[0]
            docker_image_tag = docker_tag.split(':')[1]
            # build_context = f"{folder_name}"
            docker_platform = f"{platform}/amd64"
            # Create a new builder instance using Docker Buildx
            subprocess.run(["docker", "buildx", "create", "--use"])
            docker_command = ["docker", "buildx", "build",
                              "--platform", "windows/amd64", "--push",
                              "-t", docker_tag, "."]
            subprocess.run(docker_command, cwd=folder_name, check=True)
            print(f"Docker build completed for {filename}")
            # build_options = {
            #     "path": build_context,
            #     "dockerfile": "Dockerfile",  # Path to your Dockerfile
            #     "tag": docker_image_name+":"+docker_image_tag,
            # }
            # for platform in platforms:
            #     print(f"Building for platform: {platform}")
            #     build_options["platform"] = platform
            #     response = docker_client.images.build(**build_options)
            #     for line in response:
            #         if "stream" in line:
            #             print(line["stream"].strip())
            push_docker_image(docker_image_name, docker_image_tag)


def push_docker_image(docker_image_name, docker_image_tag):
    # Set up a Docker client
    docker_client = docker.from_env()
    # Authenticate with the Docker registry
    docker_username = os.getenv("DOCKER_USERNAME")
    docker_password = os.getenv("DOCKER_PASSWORD")
    docker_client.login(username=docker_username, password=docker_password)

    # Tag the Docker image
    docker_image = docker_client.images.get(docker_image_name+':'+docker_image_tag)
    docker_image.tag(repository='arumugamsubramanian/mid', tag=docker_image_tag)

    # Push the Docker image to the registry
    docker_client.images.push(repository='arumugamsubramanian/mid', tag=docker_image_tag)


def main():
    parser = argparse.ArgumentParser(description="Download and build Docker images.")
    parser.add_argument("country", help="The country for which to process data")
    parser.add_argument("platform", help="The platform (windows or linux)")

    args = parser.parse_args()
    country = args.country
    platform = args.platform

    # Read CSV data from the local root path
    csv_file = f"{country}_data.csv"

    with open(csv_file, newline="") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row
        data = list(reader)

    # Generate download links
    download_links = generate_download_links(data, country, platform)

    # Download and build packages
    download_and_build(download_links, platform)


if __name__ == "__main__":
    main()
