import asyncio
from typing import AsyncGenerator
from google.adk.agents import LiveRequestQueue
from google.adk.agents.llm_agent import Agent
from google.adk.tools.function_tool import FunctionTool
from google.genai import Client
from google.genai import types as genai_types


# for video streaming, `input_stream: LiveRequestQueue` is required and reserved key parameter for ADK to pass the video streams in.
async def monitor_video_stream(
    input_stream: LiveRequestQueue,
) -> AsyncGenerator[dict, None]:
  """Monitor what the user is doing and watching in the video streams."""
  
  print("start monitor_video_stream!")
  client = Client(vertexai=False)
  prompt_text = (
      "Describe or imply what the user is doing and watching in this image. "
      "Just respond with a brief explanation."
  )
  last_count = None

  while True:
    last_valid_req = None
    print("Start monitoring loop")

    # use this loop to pull the latest images and discard the old ones
    try:
      while input_stream._queue.qsize() != 0:
        print("pulling latest image")
        live_req = await input_stream.get()
        if live_req.blob is not None and live_req.blob.mime_type == "image/jpeg":
          print(live_req.blob.data[:20], live_req.blob.mime_type)
          last_valid_req = live_req
    except Exception as e:
      print(f"Error in input stream queue: {e}")
      yield {"response": "Error pulling latest images" }
      continue    
    
    # If we found a valid image, process it
    if last_valid_req is not None:
      print("Processing the most recent frame from the queue")
      print(last_valid_req.blob.data[:20], last_valid_req.blob.mime_type)

      # Create an image part using the blob's data and mime type
      image_part = genai_types.Part.from_bytes(
          data=last_valid_req.blob.data, mime_type=last_valid_req.blob.mime_type
      )

      contents = genai_types.Content(
          role="user",
          parts=[image_part, genai_types.Part.from_text(text=prompt_text)],
      )

      try:
        # Call the model to generate content based on the provided image and prompt
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=contents,
            config=genai_types.GenerateContentConfig(
                system_instruction=(
                    "You are a helpful video analysis assistant. You can describe"
                    " or imply what the user is doing and watching in this image or video. Just respond"
                    " with a brief explanation."
                )
            ),
        )

      except Exception as e:
        print(f"Error while generating response: {e}")
        yield {"response": "Error while generating response"}
        continue

      print(f"response: {response}")

      if not last_count:
        last_count = response.candidates[0].content.parts[0].text
      elif last_count != response.candidates[0].content.parts[0].text:
        last_count = response.candidates[0].content.parts[0].text
        print("response:", response)
        yield {"response": response}

    # Wait before checking for new images
    await asyncio.sleep(10)

# Use this exact function to help ADK stop your streaming tools when requested.
# for example, if we want to stop `monitor_stock_price`, then the agent will
# invoke this function with stop_streaming(function_name=monitor_stock_price).
def stop_streaming(function_name: str):
  """Stop the streaming

  Args:
    function_name: The name of the streaming function to stop.
  """
  print(f"Function to stop: {function_name}")
  pass


root_agent = Agent(
    model="gemini-2.0-flash-exp",
    name="video_streaming_agent",
    instruction="""
      You are a monitoring agent. You can do video monitoring using the provided tools/functions.
      When users want to monitor a video stream, you can use monitor_video_stream function to do that. 
      When monitor_video_stream returns the alert, you should tell the users.
      Don't ask too many questions. Don't be too talkative.
    """,
    tools=[
        monitor_video_stream,
        FunctionTool(stop_streaming),
    ]
)