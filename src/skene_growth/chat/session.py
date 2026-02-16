"""Interactive chat session for skene-growth."""

import asyncio
import json
from pathlib import Path
from typing import Optional

from loguru import logger
from pydantic import SecretStr
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from skene_growth.config import load_config
from skene_growth.llm import create_llm_client

console = Console()


class ChatSession:
    """
    Interactive terminal chat session about the codebase.

    Uses the LLM to answer questions about growth features, architecture,
    tech stack, and other aspects discovered by the scanner.
    """

    def __init__(
        self,
        path: Path,
        api_key: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        max_steps: int = 4,
        tool_output_limit: int = 4000,
        debug: bool = False,
    ):
        self.path = path.resolve()
        self.debug = debug
        self.max_steps = max_steps
        self.tool_output_limit = tool_output_limit
        self.conversation_history = []

        # Load configuration
        config = load_config(path)

        # Resolve API key
        self.api_key = api_key or config.get("api_key")
        if not self.api_key:
            raise ValueError(
                "API key required. Set ANTHROPIC_API_KEY environment variable, "
                "or pass --api-key argument, or configure in .skene-growth.config"
            )

        # Resolve provider and model
        self.provider = provider or config.get("provider", "anthropic")
        self.model = model or config.get("model", self._default_model(self.provider))

        # Load manifest if it exists
        self.manifest_data = None
        manifest_path = self.path / "growth-manifest.json"
        if manifest_path.exists():
            try:
                with open(manifest_path, "r") as f:
                    self.manifest_data = json.load(f)
                logger.debug(f"Loaded manifest from {manifest_path}")
            except Exception as e:
                logger.warning(f"Failed to load manifest: {e}")

        # Initialize LLM client
        self.llm_client = create_llm_client(
            provider=self.provider,
            api_key=SecretStr(self.api_key),
            model_name=self.model,
        )

    def _default_model(self, provider: str) -> str:
        """Get default model for provider."""
        defaults = {
            "anthropic": "claude-3-5-sonnet-20241022",
            "openai": "gpt-4",
            "gemini": "gemini-2.5-pro",
            "google": "gemini-2.5-pro",
        }
        return defaults.get(provider.lower(), "claude-3-5-sonnet-20241022")

    async def start(self):
        """Start the interactive chat session."""
        # Show welcome message
        self._show_welcome()

        # Main chat loop
        while True:
            try:
                # Get user input
                user_input = await asyncio.to_thread(
                    console.input, "\n[bold cyan]You:[/bold cyan] "
                )

                # Trim whitespace
                user_input = user_input.strip()

                # Check for exit commands
                if user_input.lower() in ["exit", "quit", "bye", "q"]:
                    console.print("\n[yellow]Goodbye! 👋[/yellow]")
                    break

                # Skip empty input
                if not user_input:
                    continue

                # Add to conversation history
                self.conversation_history.append(
                    {"role": "user", "content": user_input}
                )

                # Generate response
                await self._generate_response()

            except (EOFError, KeyboardInterrupt):
                console.print("\n[yellow]Chat ended by user[/yellow]")
                break
            except Exception as e:
                console.print(f"\n[red]Error:[/red] {e}")
                if self.debug:
                    import traceback

                    traceback.print_exc()

    def _show_welcome(self):
        """Show welcome message with codebase info."""
        welcome_lines = [
            f"**Analyzing:** `{self.path}`",
            f"**Model:** `{self.llm_client.get_model_name()}`",
            "",
            "Ask me anything about:",
            "- Growth features and capabilities",
            "- Tech stack and architecture",
            "- GTM gaps and opportunities",
            "- Implementation details",
            "",
            "*Type 'exit' or 'quit' to end the session*",
        ]

        # Add manifest info if available
        if self.manifest_data:
            tech_stack = self.manifest_data.get("tech_stack", {})
            growth_hubs = self.manifest_data.get("growth_hubs", [])

            welcome_lines.insert(
                4,
                f"**Growth Manifest:** Found {len(growth_hubs)} growth hubs, "
                f"{len(tech_stack)} tech stack items",
            )

        welcome_text = "\n".join(welcome_lines)
        console.print(Panel(Markdown(welcome_text), title="Skene Growth Chat"))

    async def _generate_response(self):
        """Generate and display LLM response."""
        # Build context-aware prompt
        prompt = self._build_prompt()

        try:
            # Show thinking indicator
            with console.status("[bold blue]Thinking...", spinner="dots"):
                response = await self.llm_client.generate_content(prompt)

            # Add to conversation history
            self.conversation_history.append({"role": "assistant", "content": response})

            # Display response
            console.print("\n[bold green]Skene:[/bold green]")
            console.print(Markdown(response))

        except Exception as e:
            console.print(f"[red]Failed to generate response:[/red] {e}")
            logger.error(f"LLM generation failed: {e}")

    def _build_prompt(self) -> str:
        """Build context-aware prompt with manifest data."""
        # System context
        system_context = [
            "You are Skene Growth, an AI assistant specialized in analyzing codebases for PLG (Product-Led Growth) opportunities.",
            "You help developers understand their codebase's growth features, tech stack, and potential improvements.",
        ]

        # Add manifest context if available
        if self.manifest_data:
            system_context.append("\n## Codebase Analysis\n")
            system_context.append(f"Project: {self.manifest_data.get('name', 'Unknown')}")

            # Tech stack
            tech_stack = self.manifest_data.get("tech_stack", {})
            if tech_stack:
                languages = tech_stack.get("languages", [])
                frameworks = tech_stack.get("frameworks", [])
                if languages:
                    system_context.append(f"Languages: {', '.join(languages)}")
                if frameworks:
                    system_context.append(f"Frameworks: {', '.join(frameworks)}")

            # Growth hubs
            growth_hubs = self.manifest_data.get("growth_hubs", [])
            if growth_hubs:
                system_context.append(f"\nGrowth Features: {len(growth_hubs)} hubs detected")
                for hub in growth_hubs[:3]:  # Show top 3
                    hub_type = hub.get("type", "unknown")
                    hub_location = hub.get("location", "")
                    system_context.append(f"  - {hub_type} at {hub_location}")

            # GTM gaps
            gtm_gaps = self.manifest_data.get("gtm_gaps", [])
            if gtm_gaps:
                system_context.append(f"\nGTM Gaps: {len(gtm_gaps)} opportunities identified")

        # Build full prompt with conversation history
        prompt_parts = ["\n".join(system_context), "\n\n## Conversation\n"]

        # Add conversation history (last 10 messages)
        for msg in self.conversation_history[-10:]:
            role = "User" if msg["role"] == "user" else "Skene"
            prompt_parts.append(f"{role}: {msg['content']}")

        return "\n".join(prompt_parts)
