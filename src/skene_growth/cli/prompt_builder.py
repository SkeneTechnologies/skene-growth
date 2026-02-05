"""Prompt building and deep link utilities for build command."""

import asyncio
import os
import platform
import re
import shlex
import subprocess
from pathlib import Path
from urllib.parse import quote

from rich.console import Console

console = Console()


def extract_ceo_next_action(memo_content: str) -> str | None:
    """Extract the CEO's Next Action or NEXT ACTION section from the memo.

    Args:
        memo_content: Full memo markdown content

    Returns:
        Extracted next action text or None if not found
    """
    # Look for the CEO's Next Action section (flexible patterns)
    pattern = (
        r"##?\s*(?:1|2|7)?\.\s*(?:THE\s+)?(?:CEO'?s?\s+)?Next\s+Action.*?\n\n"
        r"\*\*(.*?):\*\*\s*(.*?)(?=\n\n###|\n\n##|\Z)"
    )
    match = re.search(pattern, memo_content, re.IGNORECASE | re.DOTALL)

    if match:
        intro = match.group(1).strip()  # e.g., "Within 24 hours", "Ship in 24 Hours"
        action = match.group(2).strip()

        # Combine intro and action for context
        full_action = f"{intro}: {action}" if intro else action

        # Clean up markdown and extra formatting
        full_action = re.sub(r"\[.*?\]", "", full_action)  # Remove markdown links
        full_action = re.sub(r"\n\n+", "\n\n", full_action)  # Normalize line breaks
        return full_action

    # Fallback: Look for any text after CEO's Next Action or NEXT ACTION heading
    pattern2 = r"##?\s*(?:1|2|7)?\.\s*(?:THE\s+)?(?:CEO'?s?\s+)?NEXT\s+ACTION.*?\n+(.*?)(?=\n\n###|\n\n##|\Z)"
    match2 = re.search(pattern2, memo_content, re.IGNORECASE | re.DOTALL)

    if match2:
        action = match2.group(1).strip()
        # Clean up markdown formatting
        action = re.sub(r"\[.*?\]", "", action)  # Remove markdown links
        action = re.sub(r"\n\n+", "\n\n", action)  # Normalize line breaks
        # Remove the bold markers if present
        action = re.sub(r"\*\*", "", action)
        return action

    return None


def extract_technical_execution(plan_content: str) -> dict[str, str] | None:
    """Extract the Technical Execution section from the growth plan.

    Args:
        plan_content: Full growth plan markdown content

    Returns:
        Dictionary with 'next_build', 'confidence', 'exact_logic', 'data_triggers', 'sequence'
        or None if not found
    """
    # Look for Technical Execution section (section 5 or 7)
    pattern = r"##?\s*(?:5|7)?\.\s*TECHNICAL\s+EXECUTION.*?\n(.*?)(?=\n\n###|\n\n##|\Z)"
    match = re.search(pattern, plan_content, re.IGNORECASE | re.DOTALL)

    if not match:
        return None

    section_content = match.group(1)

    result = {
        "next_build": "",
        "confidence": "",
        "exact_logic": "",
        "data_triggers": "",
        "sequence": "",
    }

    # Extract "The Next Build"
    pattern = (
        r"\*\*The Next Build[:\*]*\s*([^*]+?)\*\*\s*\n\s*(.*?)" r"(?=\*\*Confidence|\*\*Exact|\*\*Sequence|\*\*|$)"
    )
    next_build_match = re.search(pattern, section_content, re.IGNORECASE | re.DOTALL)
    if next_build_match:
        title = next_build_match.group(1).strip()
        description = next_build_match.group(2).strip()
        result["next_build"] = f"{title}\n{description}"
    else:
        # Fallback: simpler pattern
        fallback_pattern = (
            r"\*\*The Next Build[:\*]*\*\*\s*[:\-]?\s*(.*?)" r"(?=\*\*Confidence|\*\*Exact|\*\*Sequence|\*\*|$)"
        )
        next_build_match = re.search(fallback_pattern, section_content, re.IGNORECASE | re.DOTALL)
        if next_build_match:
            result["next_build"] = next_build_match.group(1).strip()

    # Extract Confidence Score
    confidence_pattern = r"\*\*Confidence\s+Score[:\*]*\*\*[:\s]*(.*?)(?=\*\*|$)"
    confidence_match = re.search(confidence_pattern, section_content, re.IGNORECASE | re.DOTALL)
    if confidence_match:
        result["confidence"] = confidence_match.group(1).strip()

    # Extract Exact Logic
    logic_pattern = r"\*\*Exact\s+Logic.*?\*\*(.*?)" r"(?=\*\*Exact\s+Data|\*\*Sequence|\*\*|$)"
    logic_match = re.search(logic_pattern, section_content, re.IGNORECASE | re.DOTALL)
    if logic_match:
        result["exact_logic"] = logic_match.group(1).strip()

    # Extract Exact Data Triggers
    triggers_pattern = r"\*\*Exact\s+Data\s+Triggers.*?\*\*(.*?)" r"(?=\*\*Sequence|\*\*|$)"
    triggers_match = re.search(triggers_pattern, section_content, re.IGNORECASE | re.DOTALL)
    if triggers_match:
        result["data_triggers"] = triggers_match.group(1).strip()

    # Extract Sequence
    sequence_pattern = r"\*\*Sequence[:\*]*\*\*(.*?)(?=\n\n###|\n\n##|\Z)"
    sequence_match = re.search(sequence_pattern, section_content, re.IGNORECASE | re.DOTALL)
    if sequence_match:
        result["sequence"] = sequence_match.group(1).strip()

    return result if any(result.values()) else None


async def _show_progress_indicator(stop_event: asyncio.Event) -> None:
    """Show progress indicator with filled boxes every second."""
    count = 0
    while not stop_event.is_set():
        count += 1
        # Print filled box (█) every second
        console.print("[cyan]█[/cyan]", end="")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=1.0)
            break
        except asyncio.TimeoutError:
            continue
    # Print newline when done
    if count > 0:
        console.print()


async def build_prompt_with_llm(
    plan_path: Path,
    technical_execution: dict[str, str],
    llm,
) -> str:
    """Use LLM to build an intelligent prompt from the growth plan.

    Args:
        plan_path: Path to the growth plan file
        technical_execution: Extracted technical execution section
        llm: LLM client instance

    Returns:
        LLM-generated prompt for Cursor AI
    """
    # Prepare the context for the LLM - include all engineering content
    context_parts = []

    if technical_execution.get("next_build"):
        context_parts.append(f"What We're Building: {technical_execution['next_build']}")

    if technical_execution.get("confidence"):
        context_parts.append(f"Confidence: {technical_execution['confidence']}")

    if technical_execution.get("exact_logic"):
        context_parts.append(f"Exact Logic:\n{technical_execution['exact_logic']}")

    if technical_execution.get("data_triggers"):
        context_parts.append(f"Data Triggers:\n{technical_execution['data_triggers']}")

    if technical_execution.get("sequence"):
        context_parts.append(f"Sequence:\n{technical_execution['sequence']}")

    context = "\n\n".join(context_parts) if context_parts else "No additional context available."

    # Prompt the LLM to generate an implementation prompt
    meta_prompt = (
        f"You are a prompt engineer. Create a focused, actionable prompt "
        f"for an AI coding assistant to help implement the engineering work "
        f"described in the growth plan.\n\n"
        f"## Input Information\n\n"
        f"**Growth Plan Reference:** @{plan_path}\n\n"
        f"**Technical Execution Context:**\n"
        f"{context}\n\n"
        f"## Your Task\n\n"
        f"Generate a clear, concise prompt that:\n"
        f"1. States the engineering work to be completed based on the "
        f"Technical Execution context\n"
        f"2. Includes all relevant technical context (What We're Building, "
        f"Confidence, Logic, Data Triggers, Sequence)\n"
        f"3. References the growth plan file for additional context using "
        f"@{plan_path}\n"
        f"4. Asks for step-by-step implementation with code examples\n"
        f"5. Is direct and actionable (no fluff)\n"
        f"6. Is formatted clearly with markdown headers\n\n"
        f"Generate the prompt now (output ONLY the prompt, no explanations):"
    )

    # Start progress indicator
    stop_event = asyncio.Event()
    progress_task = None
    
    try:
        progress_task = asyncio.create_task(_show_progress_indicator(stop_event))
        generated_prompt = await llm.generate_content(meta_prompt)
        
        # Clean up any markdown code fences if present
        generated_prompt = generated_prompt.strip()
        if generated_prompt.startswith("```"):
            lines = generated_prompt.split("\n")
            generated_prompt = "\n".join(lines[1:-1]) if len(lines) > 2 else generated_prompt
        return generated_prompt
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] LLM prompt generation failed: {e}")
        console.print("[dim]Falling back to template...[/dim]")
        return build_prompt_from_template(plan_path, technical_execution)
    finally:
        # Stop progress indicator
        if progress_task is not None:
            stop_event.set()
            try:
                await progress_task
            except Exception:
                pass


def build_prompt_from_template(plan_path: Path, technical_execution: dict[str, str]) -> str:
    """Build a prompt from static template (fallback).

    Args:
        plan_path: Path to the growth plan file
        technical_execution: Extracted technical execution section

    Returns:
        Template-generated prompt for Cursor AI
    """
    # Build technical context - include all engineering content
    context_parts = []

    if technical_execution.get("next_build"):
        context_parts.append(f"**What We're Building:** {technical_execution['next_build']}")

    if technical_execution.get("confidence"):
        context_parts.append(f"**Confidence:** {technical_execution['confidence']}")

    if technical_execution.get("exact_logic"):
        context_parts.append(f"**Exact Logic:**\n{technical_execution['exact_logic']}")

    if technical_execution.get("data_triggers"):
        context_parts.append(f"**Data Triggers:**\n{technical_execution['data_triggers']}")

    if technical_execution.get("sequence"):
        context_parts.append(f"**Sequence:**\n{technical_execution['sequence']}")

    context = "\n\n".join(context_parts) if context_parts else ""

    context_section = f"\n\n## Technical Execution Context\n\n{context}" if context else ""

    prompt = (
        f"I need to implement the engineering work described in the growth plan. "
        f"Reference @{plan_path} for full context.{context_section}\n\n"
        "Please help me implement this work. Break it down into concrete, "
        "actionable steps with code examples."
    )

    return prompt


def open_cursor_deeplink(prompt: str) -> None:
    """Open Cursor with a deep link containing the prompt.

    Args:
        prompt: The prompt text to send to Cursor

    Raises:
        RuntimeError: If opening the deep link fails
    """
    # URL encode the prompt
    encoded_prompt = quote(prompt, safe="")

    # Construct the deep link
    deep_link = f"cursor://anysphere.cursor-deeplink/prompt?text={encoded_prompt}"

    # Determine the command based on platform
    system = platform.system()

    try:
        if system == "Darwin":  # macOS
            subprocess.run(["open", deep_link], check=True)
        elif system == "Linux":
            subprocess.run(["xdg-open", deep_link], check=True)
        elif system == "Windows":
            subprocess.run(["start", deep_link], shell=True, check=True)
        else:
            raise RuntimeError(f"Unsupported platform: {system}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to open Cursor deep link: {e}")
    except FileNotFoundError:
        raise RuntimeError(
            f"Could not find command to open URLs on {system}. "
            "Please ensure Cursor is installed and try opening the link manually."
        )


def open_claude_terminal(prompt: str) -> None:
    """Open a new terminal window with Claude CLI and the prompt.

    Args:
        prompt: The prompt text to send to Claude

    Raises:
        RuntimeError: If opening the terminal fails
    """
    system = platform.system()
    
    # Get the current working directory
    cwd = os.getcwd()
    cwd_escaped = shlex.quote(cwd)

    # Escape the prompt for shell execution (used for Linux and Windows)
    shell_escaped_prompt = shlex.quote(prompt)

    try:
        if system == "Darwin":  # macOS
            # Build command to change directory and run claude
            # The shell command is: cd {cwd} && claude {shell_escaped_prompt}
            shell_command = f"cd {cwd_escaped} && claude {shell_escaped_prompt}"
            # Escape this string for AppleScript (escape " and \)
            applescript_escaped_command = shell_command.replace("\\", "\\\\").replace('"', '\\"')
            
            # Use osascript to open Terminal with claude command
            applescript = f"""
tell application "Terminal"
    activate
    do script "{applescript_escaped_command}"
end tell
"""
            subprocess.run(["osascript", "-e", applescript], check=True)

        elif system == "Linux":
            # Try common terminal emulators in order of preference
            # Change to the current directory before running claude
            command = f"cd {cwd_escaped} && claude {shell_escaped_prompt}; exec bash"
            terminals = [
                ["gnome-terminal", "--", "bash", "-c", command],
                ["konsole", "-e", "bash", "-c", command],
                ["xterm", "-e", "bash", "-c", command],
            ]

            for terminal_cmd in terminals:
                try:
                    subprocess.run(terminal_cmd, check=True)
                    return
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue

            raise RuntimeError("Could not find a terminal emulator. Please install gnome-terminal, konsole, or xterm.")

        elif system == "Windows":
            # Use cmd.exe to open a new window with claude
            # Change to the current directory before running claude
            cmd = f'start cmd /k "cd /d {cwd_escaped} && claude {shell_escaped_prompt}"'
            subprocess.run(cmd, shell=True, check=True)

        else:
            raise RuntimeError(f"Unsupported platform: {system}")

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to open terminal with Claude: {e}")
    except FileNotFoundError:
        raise RuntimeError(
            f"Could not find required command on {system}. "
            "Please ensure Claude CLI is installed (https://docs.anthropic.com/claude-code)"
        )
