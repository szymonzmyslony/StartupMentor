from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter


def get_transcript(video_id):
    transcript = YouTubeTranscriptApi.get_transcript(video_id)

    formatter = TextFormatter()
    # .format_transcript(transcript) turns the transcript into a JSON string.
    transcript_text = formatter.format_transcript(transcript)

    return transcript_text
