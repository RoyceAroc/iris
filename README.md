## Running our Application

```
cd frontend && npx expo run
```

```
cd backend && uv run src/main.py
```

## Inspiration 🤔

Have you ever wondered how blind people cross the road? How imminent hazards like a "wet floor sign" or a pothole to their right might inflict harm? Here are some scary statistics:

- A survey of 300 blind people found that about 40% experienced head height collisions at least once a year. [source](https://www.researchgate.net/publication/228828914_Mobility-related_accidents_experienced_by_people_with_visual_impairment#:~:text=A%20survey%20of%20300%20blind,once%20a%20month%20%5B2%5D%20.)
- 68% of people with visual impairment had been directly exposed to at least one serious life event. [source](https://pmc.ncbi.nlm.nih.gov/articles/PMC8583190/)
  ![Risk Statistics](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/56ad/8583190/7d6401a6ce75/ijerph-18-11536-g001.jpg)
- There is a 46% increased risk of road traffic crash among those with visual impairment. [source](The summary estimate revealed a 46% increased risk of road traffic crash among those with visual impairment)

![Image](https://imageio.forbes.com/specials-images/imageserve/64d465e88b2ee7a174b1ea3f/A-blind-man-with-a-white-cane-crosses-the-road/0x0.jpg?format=jpg&crop=768,711,x0,y238,safe&width=960)

This hackathon we decided to build Iris.

## What it does + How we built it 🛠️

Iris is a sleek headset built for the blind and visually impaired, designed to provide real-time guidance through the world. By attaching an iPhone as a camera to an affordable 3D-printed headset, users can navigate their surroundings with confidence. Iris doesn’t just describe the environment – it actively guides the wearer through A.I. agent specialists. Using real-time models such as captioning, classification, image segmentation agents, and depth estimation agents, Iris detects hazards in under 100 milliseconds. When a danger is identified, it instantly provides a haptic buzz, signaling the user of danger. From there, Iris delivers step-by-step spoken instructions via TTS, directing the wearer on how to safely navigate around obstacles, cross streets, or reorient themselves in complex environments.

Taking a VLM model, we were able to tune it for real-time workloads via aggressive PyTorch compiler optimization, cudNN utilization, specific matmul precision, and usage of optimal attention kernels like flash / paged attention. To achieve high network throughput, we developed a custom userspace protocol to stream tokens to clients, and to reduce agent latency, we quantized models to architecture-specific dtypes.

Built using Expo, the mobile app is compatible on both Android and iOS devices. Iris is also able to take STT commands and decode it into agentic workflows such as hazard detection, scene similarity scoring, and object detection (via Groq LPU APIs) which are carried out in real-time. Want to know when the pedestrian sign turns white for you to walk across? Want to know where your water bottle is? Iris has your back.

## Challenges we ran into 😿

Even the slightest delay in detecting a hazard could mean the difference between safe navigation and serious injury for a blind user. Latency was a critical factor, so we spent a significant amount of time tuning our models to minimize Time to Detection (what we call TTD). We implemented attention optimizations, leveraged cuDNN for accelerated inference, and fine-tuned every aspect of our pipeline. But no amount of optimization could make up for the fact that we were hitting a hard wall – our compute resources simply weren’t enough. That’s when we reached out to Brev.dev, which gave us access to the compute power we needed to push our models further, drastically improving both training and inference speed.

Compute wasn’t our only bottleneck. Network bandwidth became a serious constraint. Our initial protocol relied on JSON, which, while easy to work with, was bloated – filled with unnecessary delimiters and whitespace that slowed down transmission. Every millisecond mattered. To eliminate this overhead, we designed a custom datagram protocol, stripping out redundant characters and ensuring that every byte carried meaningful information. The result was a lean, high-speed data stream that helped us shave off critical delays.

Finally, there was the challenge of hardware. One of our core goals was affordability – if our solution wasn’t accessible to blind users, it wasn’t a solution at all. Off-the-shelf headsets were too expensive, so we designed our own. We developed a custom STL model for 3D printing a headset that could securely hold an iPhone, ensuring a low-cost but effective hardware setup. This way, users could leverage the sensors and processing power of their existing devices without needing expensive proprietary hardware.

## Accomplishments that we're proud of 💯

Iris started as a simple idea: an intelligent headset that could actively guide blind users through the world. But for us, it was also personal. One of our team members has a blind relative, and hearing firsthand about the daily challenges of navigating city streets without reliable assistance pushed us to make Iris as fast and reliable as possible. What we ended up with was a fully functional, multimodal A.I. system capable of real-time hazard detection and step-by-step navigation. Here are some of Iris' capabilties:

- Iris can chain together vision-language models, depth estimation, and object detection to dynamically respond to user queries in real time.
- We designed and 3D-printed an affordable, durable headset that transforms an iPhone into an AI-powered navigation assistant
- Users can issue STT commands like “Where’s the door?” or “Can I cross the street?” and receive responses near-instantly.

## What we learned 💭

This project pushed us deep into the weeds of HPC optimization, hardware, and networking in exciting ways. One of the biggest lessons came from wrestling with the PyTorch compiler. We thought we understood it – until we started hitting obscure bottlenecks that weren’t obvious at first glance. Some layers weren’t fusing correctly, some optimizations were actually slowing things down, and cuDNN didn’t always behave the way we assumed it would. We spent hours profiling CUDA graphs, attempting optimal Tensor core and register usage, tweaking VRAM memory layouts, and rewriting parts of our model just to squeeze out those last few milliseconds.

On the hardware side, we learned that designing an STL file isn’t just about making a model that looks right – it has to print right. Our first 3D print warped mid-print. Through trial and error, we figured out how to design for material constraints, adjust print settings for strength, and optimize for minimal waste. Eventually, we had a sleek, durable headset that could securely hold an iPhone – something that felt incredibly rewarding after our early failures.

## What's next for Iris 🚀

Iris has proven its ability to provide real-time hazard detection and navigation, but we’re just getting started. Here’s what’s next:

- Right now, Iris warns of hazards through a single vibration alert. We plan to implement a more advanced haptic feedback system that provides directional guidance such as buzzing stronger on the left or right to indicate safer paths or signaling when the user should stop.
- Beyond hazard detection, Iris will integrate more specialized agents like sign language interpretation and personalized object recognition (i.e., users can “teach” Iris what their personal items look like, so it can help locate them.)
- We want to put Iris in the hands of real users. Our next step is testing with more visually impaired individuals to refine the experience, gather feedback, and iterate on both software and hardware. We truly see this as something that changes the lives of blind individuals for the better.
