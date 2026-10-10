Screen: The Crossing, PRSE experiment and gameplay.
Mode: exploration/action with an optional diagnostic research workbench.
Purpose: Explore a physics-driven semantic world, directly test object causality, and understand which changes the physical and semantic models actually preserve.
Primary questions: Where am I and what is interactable? What happened after an action? Can I control my character and cancel automation? Is the game simulation running?
Visible answer: Full playable canvas, location/event feedback, nearby action, mission/condition, concise physics-ready status, controls and input.
Secondary questions: What is the current scene state? Which objects are physically instantiated? Which events are causal vs scripted? What can be tested next? Research workbench disclosure with viewable object states/events and quick reproducible actions.
Hidden by default: physics object internals, developer log, source revisions, model prompts, raw structured data, research reports and performance counters.
Trust: Explicit that the browser physics runs locally, not a continuously watching LLM; unsupported features must not be implied. Ready/error state always visible. An experiment shows authoritative core state, not fabricated model interpretation.
Actions: Move and jump, interact, type an action, save/load, cancel goal remain prominent. Optional experiment controls do not replace normal play. Fire experiment uses real typed gameplay actions rather than direct state mutation. No external state changes.
Rejected: automatic LLM claims, exposing model internal strings on gameplay HUD, cluttering main view with lab diagnostics, raw logging of typed private text, interrupting other processes.
Acceptance: Current game journey unchanged; Enter focus, save/load and mobile layout pass; research view shows factual changes after candle light/ignition, including no spontaneous ignition; no background network call from main gameplay; no overlap or clipped controls in mobile view.
