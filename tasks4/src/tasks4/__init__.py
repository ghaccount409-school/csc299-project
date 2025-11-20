#def main() -> None:
#    print("Hello from tasks4!")

# from openai import OpenAI
# client = OpenAI()

# completion = client.chat.completions.create(
#     model="gpt-5-mini",
#     messages=[
#       {"role": "developer", "content": "You are a helpful assistant."},
#       {"role": "user", "content": "why is the sky blue?"},
#       {"role": "assistant", "content": "The sky appears blue due to the scattering of sunlight by the atmosphere."},
#       {"role": "user", "content": "explain it like I'm five years old."}
#     ]
# )

# print(completion.choices[0].message)

import os
import sys
from openai import OpenAI

DEVELOPER_ROLE = "You are a helpful assistant that summarizes tasks as short phrases."

client = OpenAI()

def _check_api_key() -> bool:
    """Verify OPENAI_API_KEY is set; return True if present else print guidance and return False."""
    if os.getenv("OPENAI_API_KEY"):
        return True
    print("ERROR: OPENAI_API_KEY environment variable is not set!")
    print("\nSet it with one of these commands:")
    print("  Bash/Linux/Mac: export OPENAI_API_KEY='your-api-key-here'")
    print("  PowerShell: $env:OPENAI_API_KEY='your-api-key-here'")
    print("  CMD: set OPENAI_API_KEY=your-api-key-here")
    print("\nGet a key from: https://platform.openai.com/api/keys")
    sys.stdout.flush()
    return False

def main() -> None:
    """Interactive loop prompting for task descriptions and summarizing them as short phrases."""
    if not _check_api_key():
        return
    while True:
        print("\nEnter a task description (or 'quit' to exit):")
        sys.stdout.flush()
        try:
            task_description = input("> ").strip()
        except EOFError:
            # Graceful exit if stdin closes
            print("\nEOF received. Exiting.")
            break

        if task_description.lower() == "quit":
            print("Goodbye!")
            break
        if not task_description:
            print("Please enter a task description.")
            continue

        print("Processing... (this may take a few seconds)")
        sys.stdout.flush()
        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": DEVELOPER_ROLE},
                    {"role": "user", "content": f"Summarize this task as a short phrase: {task_description}"},
                    {"role": "user", "content": "Planning a successful camping trip requires careful preparation and attention to multiple details. "
                                  "You must first research and select an appropriate campsite, considering factors like proximity to water sources, "
                                  "terrain difficulty, weather forecasts, and permit requirements. Next comes assembling essential gear including a tent, "
                                  "sleeping bags rated for expected temperatures, cooking equipment, food storage containers, and navigation tools like maps "
                                  "or GPS devices. Safety preparations involve packing a first aid kit, informing someone of your itinerary, checking for "
                                  "wildlife advisories, and understanding leave-no-trace principles to minimize environmental impact. Finally, meal planning "
                                  "should account for nutritional needs, weight constraints, and proper food storage techniques to prevent attracting animals "
                                  "while ensuring you have adequate sustenance for the duration of your outdoor adventure."},
                    {"role": "user", "content": "Restoring a vintage bicycle requires patience, mechanical skills, and attention to detail across several phases. "
                                  "Begin by thoroughly cleaning the frame to assess its condition, identifying rust spots, dents, or cracks that need addressing. "
                                  "Disassemble all components systematically, photographing each step to aid reassembly, and organize hardware in labeled containers. "
                                  "The frame may need sandblasting or chemical stripping to remove old paint, followed by rust treatment, primer application, and "
                                  "fresh paint or powder coating in your chosen color scheme. Overhauling components involves rebuilding wheel hubs with new bearings, "
                                  "replacing worn brake pads and cables, servicing or replacing the bottom bracket and headset, and cleaning or upgrading the drivetrain. "
                                  "Final assembly requires careful adjustment of brakes, derailleurs, and wheel alignment, followed by a test ride to ensure smooth "
                                  "operation and safety before the restored bicycle is ready for the road."},
                    {"role": "user", "content": "Generate a paragraph of useful information for an unrelated topic. Do not use em-dashes."},
                    {"role": "user", "content": "Summarize each of the three paragraphs as individual short phrases."}
                    #{"role": "user", "content": f"Summarize this task as a short phrase: {task_description}"},
                    #{"role": "user", "content": "Summarize previous task paragraphs above as short phrases, separating the summaries by topic."},
                ],
                #max_tokens=50,
                max_completion_tokens=100,
                timeout=30.0,
            )
        except Exception as e:
            print(f"\nError calling API: {type(e).__name__}: {e}")
            sys.stdout.flush()
            continue

        print("\nSummary:")
        try:
            summary = completion.choices[0].message.content
            print(summary)
        except (AttributeError, IndexError) as e:
            print(f"Error parsing response: {e}")
            print(completion)
        sys.stdout.flush()

__all__ = ["main"]