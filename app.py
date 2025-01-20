import streamlit as st
from pyneuphonic import Neuphonic, TTSConfig, save_audio, Agent
from pyneuphonic.player import AudioPlayer
import asyncio

# PLACE YOUR API KEY HERE
api_key = "3348afafcb8324881d514535507797386e605fa07548e2f9a0aad1f67b802bf5.8c49e6f4-15e8-4c64-b84b-a1e13151ddc8"

# Initialising Neuphonic client
client = Neuphonic(api_key=api_key)

# Streamlit App UI
st.title("AI Audio Interpreter")

# Section to list available voices
if st.button("List Available Voices"):
    response = client.voices.list()
    voices = response.data['voices']
    st.write("Available Voices:")
    for voice in voices:
        st.write(f"Name: {voice['name']}, ID: {voice['id']}")

# Text-to-Speech Section
st.header("Text-to-Speech (TTS)")
input_text = st.text_input("Enter text to convert to speech:", "Hello, world!")
selected_voice = st.text_input("Enter Voice ID (optional):", "")
speed = st.slider("Select Speed (1.0 = normal):", 0.5, 2.0, 1.0)

if st.button("Generate Audio"):
    tts_config = TTSConfig(
        model='neu_hq',  # Change model if needed
        speed=speed,
        voice=selected_voice if selected_voice else None  # Use provided voice ID or default
    )

    # Generate audio
    sse = client.tts.SSEClient()
    response = sse.send(input_text, tts_config=tts_config)
    audio_bytes = bytearray()
    for item in response:
        audio_bytes += item.data.audio

    # Save audio and display
    save_audio(audio_bytes=audio_bytes, file_path="output.wav")
    st.audio("output.wav", format="audio/wav")
    st.success("Audio generated and saved as 'output.wav'.")

# AI Agent Section
st.header("AI Agent Interaction")
prompt = st.text_area("Enter Agent Prompt:", "You are a helpful agent. Answer in 10 words or less.")
greeting = st.text_input("Enter Agent Greeting:", "Hi, how can I help you today?")

if st.button("Create AI Agent"):
    agent_id = client.agents.create(
        name="Streamlit Agent",
        prompt=prompt,
        greeting=greeting
    ).data['id']

    agent = Agent(client, agent_id=agent_id, tts_model='neu_hq')
    st.success(f"Agent created with ID: {agent_id}")
    st.write(f"Greeting: {greeting}")

# Start the agent if already created
if st.button("Start Agent"):
    async def start_agent():
        await agent.start()

    asyncio.run(start_agent())
    st.success("Agent started and listening for input.")
