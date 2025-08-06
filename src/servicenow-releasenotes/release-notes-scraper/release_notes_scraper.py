import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import csv
import argparse
from collections import defaultdict


def scrape_release_notes(country):
    # Initialize a set to store unique API URLs
    unique_api_urls = set()

    # URL to the page containing the hyperlinks
    base_url = f"https://servicenow-be-prod.servicenow.com/api/bundle/{country}-release-notes/page/release-notes" \
               f"/available-versions.html"
    # Send an HTTP GET request to the URL
    response = requests.get(base_url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract hyperlinks with the pattern "/bundle/vancouver-release-notes/page/release-notes/quality/"
        pattern = rf'\/bundle\/{country}-release-notes\/page\/release-notes\/quality\/[\w-]+\.html'
        matches = re.findall(pattern, str(soup))

        # Iterate through the unique links, prepend "/api/" before "bundle," and add to the set
        for unique_link in matches:
            # Add "/api/" before "bundle" in the URL
            api_url = urljoin(base_url, unique_link.replace("/bundle/", "/api/bundle/"))
            unique_api_urls.add(api_url)

    # Initialize dictionaries to store unique build date and build tag values for each API URL
    unique_build_dates = defaultdict(set)
    unique_build_tags = defaultdict(set)

    # Iterate through the unique API URLs and process the data
    for api_url in unique_api_urls:
        # Send an HTTP GET request to the API URL
        api_response = requests.get(api_url)

        # Check if the API request was successful (status code 200)
        if api_response.status_code == 200:
            # Parse the JSON data from the response
            response_json = api_response.json()

            # Extract lines containing "Build date:" and "Build tag:" using regular expressions
            build_info_pattern = r'(Build date:|Build tag:)(.*?)\n'
            build_info_matches = re.findall(build_info_pattern, response_json["topic_html"], re.DOTALL)

            for match in build_info_matches:
                key = match[0].strip()
                value = match[1].strip()
                # Remove HTML tags from the value
                value = BeautifulSoup(value, "html.parser").text
                if "Build date:" in key:
                    unique_build_dates[api_url].add(value)
                elif "Build tag:" in key:
                    unique_build_tags[api_url].add(value)

    return unique_api_urls, unique_build_dates, unique_build_tags


def main():
    parser = argparse.ArgumentParser(description="Release Notes Scraper")
    parser.add_argument("country", choices=["xanadu", "yokohama", "zurich", "vancouver", "washingtondc"], help="Select a country for scraping")

    args = parser.parse_args()
    country = args.country

    unique_api_urls, unique_build_dates, unique_build_tags = scrape_release_notes(country)

    # Create a CSV file for the current country
    with open(f"{country}_dataset_dump.csv", mode='w', newline='') as csv_file:
        fieldnames = ["api_url", "date", "tags"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        # Write data to the CSV file
        for api_url in unique_api_urls:
            for date in unique_build_dates[api_url]:
                for tag in unique_build_tags[api_url]:
                    writer.writerow({"api_url": api_url, "date": date, "tags": tag})


if __name__ == "__main__":
    main()
