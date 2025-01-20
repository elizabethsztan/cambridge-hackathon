import streamlit as st
import asyncio
import os
from pyneuphonic import Neuphonic, TTSConfig, save_audio
from pyneuphonic.models import AgentConfig, APIResponse, AgentResponse, WebsocketEvents
from pyneuphonic.player import AsyncAudioPlayer, AsyncAudioRecorder

# PLACE YOUR API KEY HERE
api_key = "1701b983c6aa9def986084fad58939215af401e941c4fe219cf2e35780d805ed.c9441799-387a-4c62-979d-166ee460a801"

# Initialize Neuphonic Client
client = Neuphonic(api_key=api_key)

# Function to save transcripts
def save_transcript(text, section):
    try:
        with open(f'transcripts/{section}.txt', 'a') as f:
            f.write(f'{text}\n')
    except FileNotFoundError:
        os.makedirs('transcripts', exist_ok=True)
        with open(f'transcripts/{section}.txt', 'a') as f:
            f.write(f'{text}\n')

# Default on-message handler
def default_on_message(message: APIResponse[AgentResponse]):
    if message.data.type == 'user_transcript':
        st.write(f"User: {message.data.text}")
        if 'work items' in message.data.text.lower():
            save_transcript(message.data.text, 'work_items')
        elif 'cooking' in message.data.text.lower():
            save_transcript(message.data.text, 'cooking')
        else:
            save_transcript(message.data.text, 'quick_note')
    elif message.data.type == 'llm_response':
        st.write(f"Agent: {message.data.text}")

# Define the Agent Class
class StreamlitAgent:
    def __init__(self, client: Neuphonic, agent_id, mute=False, on_message=default_on_message):
        self.config = AgentConfig(agent_id=agent_id, mode='asr')  # Configure ASR mode
        self.mute = mute
        self.client = client
        self.ws = client.agents.AsyncWebsocketClient()
        self.player = AsyncAudioPlayer() if not self.mute else None
        self.recorder = AsyncAudioRecorder(websocket=self.ws, player=self.player)
        self.on_message_hook = on_message

    async def on_message(self, message: APIResponse[AgentResponse]):
        if message.data.type == 'audio_response' and not self.mute:
            await self.player.play(message.data.audio)
        if self.on_message_hook:
            self.on_message_hook(message)

    async def start(self):
        self.ws.on(WebsocketEvents.MESSAGE, self.on_message)
        self.ws.on(WebsocketEvents.CLOSE, self.on_close)
        if not self.mute:
            await self.player.open()
        await self.ws.open(self.config)
        await self.recorder.record()

    async def on_close(self):
        if not self.mute:
            await self.player.close()
        await self.recorder.close()

# Streamlit Interface
st.title("AI Audio Recording Assistant")
st.write("Use this app to interact with the Neuphonic AI Agent for recording ideas.")

# Section to configure the agent
st.header("Agent Configuration")
prompt = st.text_area("Agent Prompt", value="You are a helpful agent. Listen to my idea until I say 'that is all', then say 'thank you, recorded.'")
greeting = st.text_input("Agent Greeting", value="I am ready to record your ideas.")

if st.button("Create Agent"):
    response = client.agents.create(name="Streamlit Agent", prompt=prompt, greeting=greeting)
    agent_id = response.data['id']
    st.success(f"Agent created with ID: {agent_id}")

    # Start the agent
    agent = StreamlitAgent(client=client, agent_id=agent_id)
    st.session_state.agent = agent
else:
    agent = st.session_state.get("agent", None)

# Start the agent and record input
if agent and st.button("Start Recording"):
    async def start_agent():
        await agent.start()
    asyncio.run(start_agent())
    st.success("Agent started. You can now interact with it.")

# Show saved transcripts
st.header("Transcripts")
if os.path.exists("transcripts"):
    for file in os.listdir("transcripts"):
        with open(f"transcripts/{file}", "r") as f:
            st.subheader(file.replace(".txt", "").capitalize())
            st.text(f.read())
else:
    st.write("No transcripts available.")

