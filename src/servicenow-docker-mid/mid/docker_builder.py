import json
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
        try:
            date1 = date.split('_')[0]
            year1 = date1.split('-')[2]
            month1 = date1.split('-')[0]
            day1 = date1.split('-')[1]
            tag_parts = tags.split('-')
            tag = '-'.join(tag_parts[1:])  # Remove "glide-" prefix
            template = f"https://install.service-now.com/glide/distribution/builds/package/app-signed/mid-{platform}-container-recipe/{year1}/{month1}/{day1}/mid-{platform}-container-recipe.{tag}_{date}.{platform}.x86-64.zip"
            download_links.append(template)
            # print(download_links)
        except IndexError:
            print(f"Skipping invalid date format: {api_url}, {date}, {tags}")
            continue
    return download_links


def download_and_build(download_links, platform, rebuild):
    print("1=============================================================")
    failed_items = []
    for link in download_links:
        try:
            response = requests.get(link, stream=True)
            print(f"{link} --> {response}\n")
            if response.status_code == 200:
                filename = link.split("/")[-1]
                with open(filename, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"Downloaded {filename}\n")

                folder_name = os.path.splitext(filename)[0]
                os.makedirs(folder_name, exist_ok=True)

                with zipfile.ZipFile(filename, "r") as zip_ref:
                    zip_ref.extractall(folder_name)

                os.remove(filename)

                env_file_path = f"{folder_name}/.env"
                with open(env_file_path, 'r') as file:
                    line = file.readline().strip()
                    key, value = line.split('=')

                if key == "DOCKER_TAG":
                    docker_tag = value
                    docker_image_name = docker_tag.split(':')[0]
                    docker_image_tag = docker_tag.split(':')[1]
                    docker_tag_exists_command = [
                        "docker", "manifest", "inspect",
                        "arumugamsubramanian/"f"{docker_image_name}:{docker_image_tag}"
                    ]
                    if rebuild:
                        print("Since rebuild flag is passed, rebuilding the image")
                        print(f"Building docker image {docker_image_name}-{platform}:{docker_image_tag}\n")
                        docker_command = [
                            "docker", "build", "-t",
                            f"{docker_image_name}-{platform}:{docker_image_tag}", "."
                        ]
                        subprocess.run(docker_command, cwd=folder_name, check=True)
                        print(f"Docker build completed for {filename}\n")
                        push_docker_image(docker_image_name + '-' + platform, docker_image_tag)
                        print("2=============================================================")
                    else:
                        expected_platforms = [
                            {"os": "linux", "architecture": "amd64"},
                            {"os": "windows", "architecture": "amd64"}
                        ]
                        if check_tag_and_platform_exists(
                                f"arumugamsubramanian/{docker_image_name}-{platform}:{docker_image_tag}",
                                expected_platforms):
                            print("docker image was already built, so skipping\n")
                            print("3=============================================================")
                        else:
                            print(f"Building docker image {docker_image_name}-{platform}:{docker_image_tag}\n")
                            docker_command = [
                                "docker", "build", "-t",
                                f"{docker_image_name}-{platform}:{docker_image_tag}", "."
                            ]
                            subprocess.run(docker_command, cwd=folder_name, check=True)
                            print(f"Docker build completed for {filename}\n")
                            push_docker_image(docker_image_name + '-' + platform, docker_image_tag)
                            print("4=============================================================")
            else:
                print("5=============================================================")
                failed_items.append(link)
        except Exception as e:
            print(f"Failed to process {link}: {e}")
            failed_items.append(link)
            continue

    if failed_items:
        print("\nThe following items failed to build or process:")
        for item in failed_items:
            print(item)


def check_tag_and_platform_exists(docker_tag, expected_platforms):
    docker_tag_exists_command = ["docker", "manifest", "inspect", docker_tag]

    try:
        subprocess.check_output(docker_tag_exists_command, stderr=subprocess.STDOUT)
        # print("docker image was already built, so skipping")
        return True
        # subprocess.check_output(docker_manifest_inspect_command, stderr=subprocess.STDOUT)
        # manifest_info = subprocess.check_output(docker_tag_exists_command, stderr=subprocess.STDOUT)
        # manifest_info = manifest_info.decode('utf-8')
        #
        # image_info = json.loads(manifest_info)[0]
        # arch = image_info['Architecture']
        # os = image_info['Os']
        #
        # # print(image_info['Os'])
        # # print(image_info['Architecture'])
        # # print(expected_platforms)
        # is_image_exists = False
        # for expected_platform in expected_platforms:
        #     if os == expected_platform["os"] and arch == expected_platform["architecture"]:
        #         is_image_exists = True
        #
        # return is_image_exists

    except subprocess.CalledProcessError as e:
        print(e.output.decode())
        if "Error response from daemon" in e.output.decode():
            print("Tag does not exist. Proceeding with the build.")
            return False
        elif "no such manifest" in e.output.decode():
            print("Tag does not exist. Proceeding with the build.")
            return False
        elif "image operating system" in e.output.decode():
            print("Tag does not exist. Proceeding with the build.")
            return False
        else:
            print("An error occurred:", e.output.decode())
            return True


def push_docker_image(docker_image_name, docker_image_tag):
    # Set up Docker login credentials
    docker_username = os.getenv("DOCKER_USERNAME")
    docker_password = os.getenv("DOCKER_PASSWORD")

    # Docker login command
    docker_login_command = f"docker login -u {docker_username} -p {docker_password}"

    # Docker tag command
    docker_tag_command = f"docker tag {docker_image_name}:{docker_image_tag} arumugamsubramanian/{docker_image_name}:{docker_image_tag}"

    # Docker push command
    docker_push_command = f"docker push arumugamsubramanian/{docker_image_name}:{docker_image_tag}"

    try:
        # Run Docker login
        subprocess.run(docker_login_command, shell=True, check=True)

        # Run Docker tag
        subprocess.run(docker_tag_command, shell=True, check=True)

        # Run Docker push
        subprocess.run(docker_push_command, shell=True, check=True)

        print(f"Successfully pushed Docker image: arumugamsubramanian/{docker_image_name}:{docker_image_tag}")

    except subprocess.CalledProcessError as e:
        print(f"Error executing Docker command: {e}")


def main():
    parser = argparse.ArgumentParser(description="Download and build Docker images.")
    parser.add_argument("--country", choices=['vancouver', 'washingtondc', 'xanadu', 'yokohama', 'zurich', 'pdi'], required=True,
                        help="The country for which to process data")
    parser.add_argument("--platform", choices=['windows', 'linux'], required=True,
                        help="The platform (windows or linux)")
    parser.add_argument("--rebuild", action="store_true", help="rebuild the image for all the tags")

    args = parser.parse_args()
    country = args.country
    platform = args.platform
    rebuild = args.rebuild

    # Read CSV data from the local root path
    csv_file = f"{country}_data.csv"

    with open(csv_file, newline="") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row
        data = list(reader)

    # Generate download links
    download_links = generate_download_links(data, country, platform)

    # Download and build packages
    download_and_build(download_links, platform, rebuild)


if __name__ == "__main__":
    main()
