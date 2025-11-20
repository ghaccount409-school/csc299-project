from openai import OpenAI
client = OpenAI()

completion = client.chat.completions.create(
    model="gpt-5-mini",
    messages=[
      {"role": "developer", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Moroccan cuisine is a vibrant mosaic of flavors where sweet and savory "
                                  "dance together in perfect harmony. Fragrant spices like cumin, cinnamon, and saffron mingle with fresh "
                                  "herbs such as mint and cilantro, creating layers of warmth and brightness in every bite. Slow-cooked "
                                  "tagines showcase tender meats infused with citrusy preserved lemons and briny olives, while couscous "
                                  "provides a delicate, fluffy backdrop for rich stews and roasted vegetables. Even street foods--like smoky "
                                  "grilled brochettes or honey-soaked pastries--carry the signature balance of spice, sweetness, and aromatic "
                                  "depth that makes Moroccan cooking unforgettable."},
      {"role": "user", "content": "Bioluminescent organisms are living creatures capable of producing their "
                                  "own light through biochemical reactions involving the molecule luciferin and the enzyme luciferase. "
                                  "Found in environments ranging from the deep ocean to forest floors, these organisms use light for a "
                                  "variety of purposes, such as attracting mates, deterring predators, and luring prey. Deep-sea species "
                                  "like lanternfish and comb jellies rely heavily on bioluminescence due to the absence of sunlight below "
                                  "the photic zone. On land, fireflies are among the most familiar examples, using rhythmic flashes to "
                                  "communicate during mating rituals. The study of bioluminescence has not only illuminated ecological "
                                  "interactions but has also led to innovations in biotechnology, including improved medical imaging and "
                                  "environmental monitoring tools."},
      {"role": "user", "content": "Generate a paragraph of useful information for an unrelated topic. Do not use em-dashes."},
      {"role": "user", "content": "Summarize each of the three paragraphs as individual short phrases."}
    ]
)

print(completion.choices[0].message)