import os
import pymupdf as fitz
from google import genai
from google.genai import types

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

full_text = ""

doc = fitz.open("Test_Document.pdf")

for n, page in enumerate(doc):
    full_text += page.get_text()
    full_text += "\n"

    images = page.get_images(full=True)
    for img_index, img in enumerate(images):
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        image_ext = base_image["ext"]

        filename = f"page{n + 1}_image_{img_index}.{image_ext}"
        with open(filename, "wb") as f:
            f.write(image_bytes)
        print("Saved image from page", n + 1)

        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=f"image/{image_ext}"),
                    "Describe this image in 2-3 sentences. Include any numbers or labels you can read.",
                ],
            )
            image_description = response.text
        except Exception as e:
            print("API call failed for image description")
            print("Reason:", e)
            image_description = ""

        print("Image description:", image_description)
        full_text += f"\n[Image description: {image_description}]\n"

print("\n--- Full text with image description included ---")
print(full_text)
print("\nTotal characters:", len(full_text))


chunk_size = 2000
chunks = []

for i in range(0, len(full_text), chunk_size):
    chunk = full_text[i:i + chunk_size]
    chunks.append(chunk)

print("Number of chunks:", len(chunks))

for n, c in enumerate(chunks):
    print(f"\n--- Chunk {n + 1} ---")
    print(c)


summaries = []

for n, c in enumerate(chunks):
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=f"Summarize this text in 1-2 sentences:\n\n{c}",
        )
        summary = response.text
    except Exception as e:
        print(f"API call failed for chunk {n + 1}")
        print("Reason:", e)
        summary = ""

    summaries.append(summary)
    print(f"\n--- Summary of Chunk {n + 1} ---")
    print(summary)



final_summary_input = "\n".join(summaries)

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=f"Combine these summaries into one cohesive final summary of the whole document:\n\n{final_summary_input}",
)

final_summary = response.text

print("\n--- FINAL DOCUMENT SUMMARY ---")
print(final_summary)       



table_only = """Release
Month
Metric Improved
Change
Routing
March
Routing Accuracy
+12%
Templates
July
Avg. Response Time
-18%
Escalation
November
Escalation Precision
+9%"""

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=f"Summarize this text in 1-2 sentences:\n\n{table_only}",
)

print("\n--- Summary of TABLE ONLY (no surrounding context) ---")
print(response.text)