


from google.cloud import storage
import os
import subprocess

def extract_audio_ffmpeg(filePath):
    filePathOutput = os.path.splitext(filePath)[0] + '.mp3'
    subprocess.call(['ffmpeg', '-i', filePath, filePathOutput])
    return filePathOutput

def merge_video_with_audio_ffmpeg(videoFilePath,audioFilePath,filePathOutput,start_time_audio="00:00:05"):
    subprocess.call(['ffmpeg', '-i', videoFilePath,
                     '-itsoffset', start_time_audio,
                     '-i', audioFilePath,
                     '-c:v', 'copy',
                     '-map', '0:v:0',
                     '-map', '1:a:0',
                     filePathOutput, '-y'])


def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    # bucket_name = "your-bucket-name"
    # source_file_name = "local/path/to/file"
    # destination_blob_name = "storage-object-name"

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(
        "File {} uploaded to {}.".format(
            source_file_name, destination_blob_name
        )
    )

from google.cloud import speech_v1p1beta1
from google.cloud.speech_v1p1beta1 import enums


def speech_to_text(bucket_name, audio_blob_name):
    client = speech_v1p1beta1.SpeechClient()
    # storage_uri = 'gs://cloud-samples-data/speech/brooklyn_bridge.mp3'
    storage_uri = 'gs://' + bucket_name + '/' + audio_blob_name
    # The language of the supplied audio
    language_code = "en-GB"
    # Sample rate in Hertz of the audio data sent
    sample_rate_hertz = 44100

    encoding = enums.RecognitionConfig.AudioEncoding.MP3
    config = {
        "language_code": language_code,
        "sample_rate_hertz": sample_rate_hertz,
        "encoding": encoding,
        "enable_word_time_offsets": True
    }
    audio = {"uri": storage_uri}

    response = client.recognize(config, audio)
    for result in response.results:
        # First alternative is the most probable result
        alternative = result.alternatives[0]
        for word in alternative.words:
            print("Start Time: {}".format(word.start_time))
            print("End Time: {}".format(word.end_time))

        print(u"Transcript: {}".format(alternative.transcript))
    return alternative.transcript


def translate(text,language):
    from google.cloud import translate_v2 as translate
    translate_client = translate.Client()

    if isinstance(text, bytes):
        text = text.decode('utf-8')

    # Text can also be a sequence of strings, in which case this method
    # will return a sequence of results for each text.
    result = translate_client.translate(
        text, target_language=language)

    print(u'Text: {}'.format(result['input']))
    print(u'Translation: {}'.format(result['translatedText']))

    print(u'Detected source language: {}'.format(
        result['detectedSourceLanguage'])
    )
    return result['translatedText']

def text_to_speech(speak, languageCode, outputFilePath, speed=1.0):
    """Synthesizes speech from the input string of text or ssml.

    Note: ssml must be well-formed according to:
        https://www.w3.org/TR/speech-synthesis/
    """
    from google.cloud import texttospeech

    # Instantiates a client
    client = texttospeech.TextToSpeechClient()

    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=speak)

    # Build the voice request, select the language code ("en-US") and the ssml
    # voice gender ("neutral")
    voice = texttospeech.VoiceSelectionParams(
        language_code=languageCode, ssml_gender=texttospeech.SsmlVoiceGender.MALE
    )

    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=speed
    )

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # The response's audio_content is binary.
    with open(outputFilePath, "wb") as out:
        # Write the response to the output file.
        out.write(response.audio_content)
        print('Audio content written to file "{}"'.format(outputFilePath))

original_video="introduction_original.mp4"
language="ar"
speed=0.7


audio_file_path = extract_audio_ffmpeg(original_video)
upload_blob("translations_code_mental", audio_file_path, os.path.basename(audio_file_path))
transcript = speech_to_text("translations_code_mental", audio_file_path)
translation = translate(transcript, language)
text_to_speech(translation, language, "{}.mp3".format(language), speed=speed)
merge_video_with_audio_ffmpeg(original_video, "{}.mp3".format(language),"{}_{}.mp4".format( os.path.splitext(original_video)[0], language),start_time_audio="00:00:02")