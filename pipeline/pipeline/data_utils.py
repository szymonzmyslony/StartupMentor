import requests


def has_youtube_reference(response):
    text = response.text
    return text.find("youtube.com") != -1


def has_spotify_reference(response):
    # Send an HTTP GET request to fetch the HTML content of the web page
    text = response.text
    return text.find("spotify.com") != -1


def sort_yc_links(urls):
    youtube_urls = []
    text_urls = []
    spotify_urls = []

    for url in urls:
        response = requests.get(url)
        hasYoutube = has_youtube_reference(response)
        hasSpotify = has_spotify_reference(response)
        if hasYoutube:
            youtube_urls.append(url)
        elif hasSpotify:
            spotify_urls.append(url)
        else:
            text_urls.append(url)
    return youtube_urls, spotify_urls, text_urls
