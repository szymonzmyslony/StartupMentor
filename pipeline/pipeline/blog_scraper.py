import requests
from bs4 import BeautifulSoup
import json
import markdown


def parse_md_into_string(text):
    html = markdown.markdown(text)

    # Use BeautifulSoup to convert HTML to plain text
    soup = BeautifulSoup(html, "html.parser")
    plain_text = soup.get_text()
    return plain_text


def extract_article_to_json(url, parse_yt_id=False):
    # Send a GET request to the URL
    response = requests.get(url)

    # Check if the request was successful
    # Get the content of the response
    content = response.text

    # Use BeautifulSoup to parse the HTML content
    soup = BeautifulSoup(content, "lxml")

    # Extract the div with the 'data-page' attribute
    data_div = soup.find("div", attrs={"data-page": True})

    if not data_div:
        print("Data not found in the page.")
        return

    # Extract the JSON string from the 'data-page' attribute
    json_string = data_div["data-page"]

    # Parse the JSON string to a Python dictionary
    data = json.loads(json_string)

    # Extract the required information
    props = data["props"]
    if "article" not in props.keys():
        return None
    title = props["article"]["title"]
    content = props["article"]["content"]
    description = props["article"]["description"]

    extracted_data = {
        "title": title,
        "content": content,
        "url": url,
        "description": description,
        "transcript": None,
    }
    if parse_yt_id:
        article = props["article"]
        if "transcript" in article.keys():
            transcript = article["transcript"]
            extracted_data["transcript"] = transcript

        youtube_id = props["article"]["youtube_id"]
        extracted_data["youtube_id"] = youtube_id

    # Create a dictionary with the extracted data

    return extracted_data

    # Specify the filename you want to save the content to
    # filename = "webpage_content.json"

    # Save the extracted data to a JSON file
    # with open(filename, "w", encoding="utf-8") as file:
    #     json.dump(extracted_data, file, ensure_ascii=False, indent=4)

    # print(f"Data extracted and saved to {filename} successfully.")
    # else:
    #     print(f"Failed to retrieve the web page. Status code: {response.status_code}")
