# ************ v7 includes facial recongition *********************
# IMPORT SECTION - ALL NEEDED IMPORTS AND NAMES
import pyttsx3  # pip3 install pyttsx3
# import pyaudio  # needed because used by speech_recognition
import speech_recognition as sr  # pip3 install SpeechRecognition
# import os  # not needed: used for google cloud tts which we did not use
# from google.cloud import texttospeech  # not needed: used for google cloud tts which we did not use
# import json  # needed because of watson responses
from ibm_watson import AssistantV2  # pip3 install ibm-watson
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator  # this should install with ibm-watson (see above line)

from gtts import gTTS  # pip3 install gtts
from playsound import playsound  # pip3 install playsound
from faceRec_class import FaceRec  #class located in the faceRec_class directory


def releaseResponse_Named(response_text="", name=""):
    if name != "":
        name = name.split()[0]
    response_text = response_text.replace("<name>", name)
    # use tts to say the response out loud
    print('Response:', response_text)
    tts = gTTS(text=response_text, lang='en')
    tts.save("response.mp3")
    playsound("response.mp3")

def releaseResponse_Normal(response_text=""):
    # use tts to say the response out loud
    print('Response:', response_text)
    tts = gTTS(text=response_text, lang='en')
    tts.save("response.mp3")
    playsound("response.mp3")


# Authenticate the assistant via authID
authenticator = IAMAuthenticator('OmqmIsjTLK5USgmfReFMLz6P58fkXR5PdMlEb0_Fu1Cg')
assistant = AssistantV2(
    version='2019-11-19',
    authenticator=authenticator
)

# Set the API location url and the assistant's ID
assistant.set_service_url('https://gateway.watsonplatform.net/assistant/api')
assistant_id = 'ee080c9a-51ec-4186-b777-afd2d568ac77'

# Create the assistant's session (new session is generated each time the code is run)
new_session = assistant.create_session(assistant_id)
session = new_session.get_result()
session_id = session['session_id']

# init facial recognition class
fr = FaceRec(
    embedding_file="../tensorflow-face-rec/embeddings.npz", 
    facenet_model="../tensorflow-face-rec/model/facenet_keras.h5", 
    display=True)

# Getting here means the session was successful and therefore we need to ask the user if they are ready to begin
input("Press Enter when ready...")

# DISREGARD THESE LINES, THEY ARE FOR GOOGLE CLOUD TTS WHICH WE DID NOT USE
'''
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "FILE DIR HERE"
client = texttospeech.TextToSpeechClient()
'''


# Initialize the speech recognizer and change threshold
r = sr.Recognizer()
r.dynamic_energy_threshold = False
r.energy_threshold = 700  # 400

# BEGIN MAIN LOOP
quit_check = False  # Note that there is currently no exit condition for this. The program has to be manually stopped.
while quit_check is not True:

    # Begin probing the mic
    with sr.Microphone(device_index=6) as source:
        print("Looking for 'hey charlie'")
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)  # this line means it is listening
        # needs a few try/except - see the excepts for more info
        try:
            text = r.recognize_google(audio)  # this line converts what you say into a string!!
            print("You said: {}".format(text))

            # if what you said was ONLY "hey charlie", then it will look AGAIN for a followup line
            if text.lower() == "hey charlie" or text.lower() == "charlie":
                # print("hey charlie recognized without any input")
                print("Talk into mic now")
                audio = r.listen(source)  # listening for followup sentence

                try:
                    text = r.recognize_google(audio)  # recognize the followup sentence
                    print("You said: {}".format(text))

                    # begin the assistant magic
                    response = assistant.message(
                        assistant_id=assistant_id,
                        session_id=session_id,
                        input={
                            'message_type': 'text',
                            'text': text  # this is the text that is FED INTO THE ASSISTANT
                        }
                    ).get_result()  # this is the text that is SPIT OUT OF THE ASSISTANT (as json)

                    # now parse out the response from the json object
                    pulled_list = response["output"]["generic"]
                    response_text = pulled_list[0].get('text')

                    if "<name>" in response_text:
                        name, prob = fr.face_cap()
                        releaseResponse_Named(response_text, name)
                    else:
                        releaseResponse_Normal(response_text)

                except sr.UnknownValueError:
                    print("Could not recognize what you said")

            # if the sentence STARTS WITH "hey charlie" that means there is already an attached sentence
            elif (text.lower()).startswith("hey charlie") or (text.lower()).startswith("charlie"):
                # print("hey charlie recognized with input")

                parsed_text = text[12:]  # get the string without the "hey charlie" at the beginning
                # print("PARSED:", parsed_text)

                # begin the assistant magic
                response = assistant.message(
                    assistant_id=assistant_id,
                    session_id=session_id,
                    input={
                        'message_type': 'text',
                        'text': parsed_text  # this is the text that is FED INTO THE ASSISTANT
                    }
                ).get_result()  # this is the text that is SPIT OUT OF THE ASSISTANT (as json)

                # now parse out the response from the json object
                pulled_list = response["output"]["generic"]
                response_text = pulled_list[0].get('text')

                if "<name>" in response_text:
                    name, prob = fr.face_cap()
                    releaseResponse_Named(response_text, name)
                else:
                    releaseResponse_Normal(response_text)


            # DISREGARD THE CODE BLOCK BELOW, IT IS USED FOR GOOGLE CLOUD TTS WHICH WE DID NOT USE
            """
            synthesis_input = texttospeech.types.SynthesisInput(text=text)

            voice = texttospeech.types.VoiceSelectionParams(
                language_code="en-US",
                name="en-US-Wavenet-D",  # A
                ssml_gender=texttospeech.enums.SsmlVoiceGender.NEUTRAL)  # MALE

            audio_config = texttospeech.types.AudioConfig(
                audio_encoding=texttospeech.enums.AudioEncoding.MP3, pitch=3.00)

            response = client.synthesize_speech(synthesis_input, voice, audio_config)
            """

        except sr.UnknownValueError:
            print("Could not recognize what you said")