# CopilotKit Tool-Based Generative UI Analysis

## Demo URL
https://demo-viewer-five.vercel.app/feature/tool_based_generative_ui

## Key Concept
Tool-Based Generative UI uses `useCopilotAction` to define tools that the AI can call, which then render custom UI components. This is more action-oriented than state-based rendering.

## Core Implementation

### React Hook: `useCopilotAction`
```typescript
useCopilotAction({
  name: "generate_haiku",
  description: "Generate a haiku with image",
  parameters: [
    {
      name: "topic",
      type: "string",
      description: "Topic for the haiku"
    }
  ],
  render: ({ status, args, result }) => {
    // Return UI based on action execution
    if (status === "executing") {
      return <div>Generating haiku about {args.topic}...</div>
    }
    if (status === "complete" && result) {
      return <HaikuCard haiku={result} />
    }
  },
  handler: async ({ topic }) => {
    // Call backend to generate haiku
    const haiku = await generateHaiku(topic);
    return haiku;
  }
});
```

## Haiku Demo Specifics
- Generates Japanese haiku with English translation
- Includes themed background images
- Valid image names predefined in array
- Images stored as Japanese-themed photography

### Haiku Data Structure
```typescript
interface Haiku {
  japanese: string[];
  english: string[];
  image_names: string[];
  selectedImage: string | null;
}
```

## Image Assets Used
```typescript
const VALID_IMAGE_NAMES = [
  "Osaka_Castle_Turret_Stone_Wall_Pine_Trees_Daytime.jpg",
  "Tokyo_Skyline_Night_Tokyo_Tower_Mount_Fuji_View.jpg",
  "Cherry_Blossoms_Sakura_Night_View_City_Lights_Japan.jpg",
  // ... more Japanese-themed images
];
```

## Key Differences from Agentic UI
- **Tool-based**: Triggered by specific AI function calls
- **Action-oriented**: Executes discrete tasks with parameters
- **Render per action**: UI tied to specific tool execution
- **Handler function**: Contains business logic for the tool

## Backend Integration
- Agent: `tool_based_generative_ui`
- Can work with or without CrewAI
- Tools exposed to LLM for function calling

## For Video Copilot Use Case

### Potential Tools to Define
```typescript
// Generate video scene
useCopilotAction({
  name: "generate_scene",
  parameters: [
    { name: "prompt", type: "string" },
    { name: "style", type: "string" },
    { name: "duration", type: "number" }
  ],
  render: ({ status, result }) => {
    if (status === "executing") {
      return <VideoGeneratingCard />
    }
    return <VideoPreview url={result.url} />
  }
});

// Apply video effect
useCopilotAction({
  name: "apply_effect",
  parameters: [
    { name: "effect_type", type: "string" },
    { name: "intensity", type: "number" }
  ],
  render: ({ status, result }) => {
    return <EffectPreview before={original} after={result} />
  }
});
```

## Visual Elements
- Card-based haiku display
- Japanese/English text side by side
- Background image integration
- Clean, minimalist design
- Chat sidebar for interaction

## Benefits for Video Production
1. **Discrete Actions**: Each video operation as a tool
2. **Visual Feedback**: Preview results inline
3. **Parameter Control**: AI can adjust settings
4. **Composability**: Chain multiple tools together