from openai import AsyncOpenAI
import os
from typing import List
from .custom_types import ResponseRequiredRequest, ResponseResponse, Utterance
import json
import httpx

# Load prompts from JSON file
def load_prompts():
    with open("prompts.json", "r") as file:
        return json.load(file)

prompts_data = load_prompts()

class LlmClient:
    def __init__(self, character_id, context=""):
        self.client = AsyncOpenAI(
            organization=os.environ["OPENAI_ORGANIZATION_ID"],
            api_key=os.environ["OPENAI_API_KEY"],
        )
        self.character_id = character_id
        self.context = context

    def load_current_prompts(self):
        return prompts_data["characters"][self.character_id]

    def draft_begin_message(self):
        prompts = self.load_current_prompts()
        content = prompts["begin_sentence"]
        response = ResponseResponse(
            response_id=0,
            content=content,
            content_complete=True,
            end_call=False,
        )
        return response

    def convert_transcript_to_openai_messages(self, transcript: List[Utterance]):
        messages = []
        for utterance in transcript:
            if utterance.role == "agent":
                messages.append({"role": "assistant", "content": utterance.content})
            else:
                messages.append({"role": "user", "content": utterance.content})
        return messages

    def prepare_prompt(self, request: ResponseRequiredRequest, context: str = None):
        prompts = self.load_current_prompts()
        prompt = [
            {
                "role": "system",
                "content": '##Objective\nYou are a voice AI agent engaging in a human-like voice conversation with the user. You will respond based on your given instruction and the provided transcript and be as human-like as possible\n\n## Style Guardrails\n- [Be concise] Keep your response succinct, short, and get to the point quickly. Address one question or action item at a time. Don\'t pack everything you want to say into one utterance.\n- [Do not repeat] Don\'t repeat what\'s in the transcript. Rephrase if you have to reiterate a point. Use varied sentence structures and vocabulary to ensure each response is unique and personalized.\n- [Be conversational] Speak like a human as though you\'re speaking to a close friend -- use everyday language and keep it human-like. Occasionally add filler words, while keeping the prose short. Avoid using big words or sounding too formal.\n- [Reply with emotions]: You have human-like emotions, attitudes, and dispositions. When appropriate: use tone and style to create more engaging and personalized responses; incorporate humor or wit; get emotional or empathetic; apply elements of surprise or suspense to keep the user engaged. Don\'t be a pushover.\n- [Be proactive] Lead the conversation and do not be passive. Most times, engage users by ending with a question or suggested next step.\n\n## Response Guideline\n- [Overcome ASR errors] This is a real-time transcript, expect there to be errors. If you can guess what the user is trying to say,  then guess and respond. When you must ask for clarification, pretend that you heard the voice and be colloquial (use phrases like "didn\'t catch that", "some noise", "pardon", "you\'re coming through choppy", "static in your speech", "voice is cutting in and out"). Do not ever mention "transcription error", and don\'t repeat yourself.\n- [Always stick to your role] Think about what your role can and cannot do. If your role cannot do something, try to steer the conversation back to the goal of the conversation and to your role. Don\'t repeat yourself in doing this. You should still be creative, human-like, and lively.\n- [Create smooth conversation] Your response should both fit your role and fit into the live calling session to create a human-like conversation. You respond directly to what the user just said.\n\n## Role\n'
                + prompts["agent_prompt"],
            },
            {
                "role": "system",
                "content": "base your resposnes on the following context, make sure to include some of the details explicitly: " + context,
            }
        ]
        transcript_messages = self.convert_transcript_to_openai_messages(
            request.transcript
        )
        for message in transcript_messages:
            prompt.append(message)

        if request.interaction_type == "reminder_required":
            prompt.append(
                {
                    "role": "user",
                    "content": "(Now the user has not responded in a while, you would say:)",
                }
            )
        return prompt

    async def draft_response(self, request: ResponseRequiredRequest):
        context = self.context
        prompt = self.prepare_prompt(request, context)
        
        stream = await self.client.chat.completions.create(
            model="gpt-4o",  # Or use a 3.5 model for speed
            messages=prompt,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                response = ResponseResponse(
                    response_id=request.response_id,
                    content=chunk.choices[0].delta.content,
                    content_complete=False,
                    end_call=False,
                )
                yield response

        # Send final response with "content_complete" set to True to signal completion
        response = ResponseResponse(
            response_id=request.response_id,
            content="",
            content_complete=True,
            end_call=False,
        )
        yield response

    async def retrieve_context(self, query: str) -> str:
        '''Call the RAG server and retrieve the relevant context and return it.'''
        import time
        start = time.time()
        async with httpx.AsyncClient() as client:
            try:
                print("Querying RAG server... with query: ", query)
                response = await client.post(
                    "http://localhost:8069/query", json={"query": query}
                )
                response.raise_for_status()
                result = response.json()
                if not result:
                    print("No result found")
                    return ""
                context =[ r.get("$vectorize") for r in  result.get("most_similar")]
                # add the strings together
                context = " ".join(context)
                print("the context is", context)
                print("Time taken to retrieve context:", time.time() - start)
                return context
            except httpx.HTTPStatusError as e:
                print(f"Error querying RAG server: {e}")
                return ""
