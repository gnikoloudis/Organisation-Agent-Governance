import asyncio
import os
import sys
from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.types import GeminiConfig, StepSource, StepType


# Cost rates per 1,000,000 tokens based on active models in 2026 tiers
MODEL_COST_MAP = {
    "gemini-3.1-pro": {"input": 0.35, "output": 1.05},
    "gemini-3.5-flash": {"input": 0.075, "output": 0.30},
    "claude-4.6": {"input": 3.00, "output": 15.00}
}

def calculate_session_cost(model_name: str, total_usage) -> float:
    """Calculates active dollar cost from the conversation usage container."""
    if not total_usage:
        return 0.0
    
    rates = MODEL_COST_MAP.get(model_name, {"input": 0.50, "output": 1.50})
    
    # Safely extract input/output counts depending on attribute naming
    input_tokens = getattr(total_usage, "prompt_token_count", None)
    if input_tokens is None:
        input_tokens = getattr(total_usage, "input_tokens", 0)
        
    output_tokens = getattr(total_usage, "candidates_token_count", None)
    if output_tokens is None:
        output_tokens = getattr(total_usage, "output_tokens", 0)
    else:
        # Include thinking tokens in output cost if available
        output_tokens += getattr(total_usage, "thoughts_token_count", 0) or 0
    
    # Fallback if only total_token_count is populated
    if input_tokens == 0 and output_tokens == 0:
        total_tokens = getattr(total_usage, "total_token_count", None)
        if total_tokens is None:
            total_tokens = getattr(total_usage, "total_tokens", 0)
        # Split 80/20 input/output assumption for ballpark estimation
        input_tokens, output_tokens = int(total_tokens * 0.8), int(total_tokens * 0.2)

    input_cost = (input_tokens / 1_000_000) * rates["input"]
    output_cost = (output_tokens / 1_000_000) * rates["output"]
    return input_cost + output_cost

async def run_tracked_agent():
    # Retrieve the API key from environment
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: The GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        print("Please set it in your environment before running this script.", file=sys.stderr)
        print("Example (PowerShell):", file=sys.stderr)
        print("  $env:GEMINI_API_KEY = \"your_api_key_here\"", file=sys.stderr)
        print("Example (CMD):", file=sys.stderr)
        print("  set GEMINI_API_KEY=your_api_key_here", file=sys.stderr)
        sys.exit(1)
        
    gemini_cfg = GeminiConfig(api_key=api_key)
    
    config = LocalAgentConfig(
        gemini_config=gemini_cfg,
        system_instructions="You are an optimization assistant tracking development metrics."
    )
    
    async with Agent(config) as agent:
        # 1. Execute the prompt via the Layer 2 Conversation manager
        prompt = "Review the mapping layout parameters for the coastal dining application."
        print(f"User: {prompt}\n")
        
        response = await agent.chat(prompt)
        
        # 2. Stream standard response tokens to stdout dynamically
        print("Agent Response: ", end="")
        async_response_text = ""
        async for token in response:
            sys.stdout.write(token)
            sys.stdout.flush()
            async_response_text += token
        print("\n" + "-"*40)
 
        # 3. Step-by-Step Trajectory Audit (Replacing the broken tool hook)
        # We iterate over the immediate history to check execution steps and durations
        for step in agent.conversation.history:
            if step.source == StepSource.MODEL and step.type == StepType.TOOL_CALL:
                # If tool data metadata contains call details
                tool_name = getattr(step, "name", "Unknown Tool")
                duration = getattr(step, "duration", 0.0)
                print(f"[Audit Log] Tool executed: {tool_name} | Duration: {duration}s")
 
        # 4. Extract Total Token Usage & Compute Billing Impact
        # Antigravity updates conversation.total_usage state continuously
        usage = getattr(agent.conversation, "total_usage", None)
        
        agent_config = getattr(agent, "_config", None)
        model_name = "gemini-3.5-flash"
        if agent_config and hasattr(agent_config, "gemini_config"):
            model_name = agent_config.gemini_config.models.default.name
        
        if usage:
            total_tokens = getattr(usage, "total_token_count", 0) or 0
            est_cost = calculate_session_cost(model_name, usage)
            
            print(f"\n[Session Summary]")
            print(f"Active Model: {model_name}")
            print(f"Total Cumulative Tokens: {total_tokens}")
            print(f"Estimated Turn Cost: ${est_cost:.6f}")
            
            # Compaction Guardrails 
            if total_tokens > 135000:
                print("⚠️ Warning: Session exceeds 135k tokens. Automatic context compaction pending.")

if __name__ == "__main__":
    asyncio.run(run_tracked_agent())