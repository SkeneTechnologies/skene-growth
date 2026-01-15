# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

### Major Updates

- **PLG Lifecycle Templates with Metrics**: Complete redesign of growth template structure to include:
  - **Lifecycles**: 3-7 stages representing the complete user journey
  - **Milestones**: 3-7 actionable milestones per lifecycle stage
  - **Metrics**: 3-5 measurable KPIs per lifecycle with benchmarks and measurement methods
  - Automatic structure detection and rendering in markdown
  
- **Enhanced System Prompt**: Updated LLM prompt to generate comprehensive PLG templates using manifest data:
  - Creates custom lifecycle stages based on business type
  - Generates specific milestones for each stage
  - Includes measurable metrics with benchmarks (e.g., "> 25%", "< 4 hours")
  - Uses manifest as primary input (not generic descriptions)

- **Flexible Growth Templates**: Templates are now fully customizable by business type. The LLM generates custom lifecycle stages, keywords, and visuals tailored to your specific product journey (e.g., design agency, B2B SaaS, marketplace). Example templates are used as reference, not rigid structures.

- **Business Type Parameter**: Added `--business-type` flag to `analyze` command to specify custom template generation (e.g., `--business-type "design-agency"`). LLM infers business type if not specified.

- **Template Examples**: Added multiple template formats:
  - `plg-lifecycle-template.json` - New B2B SaaS template with lifecycles/milestones/metrics
  - `design-agency-template.json` - Design agency client journey

### Other Updates

- Add LLM-generated growth template outputs (`growth-template.json` and `growth-template.md`).
- Enhanced validation to enforce metrics in all lifecycle stages.
- Automatic template format detection in markdown generator.
- Support for both new (lifecycle/metrics) and legacy (visuals/keywords) template structures.
- Metrics rendered as bulleted lists (not tables) in markdown output for better readability.
- Analysis summary now includes lifecycle stages count and names from generated growth template.
- Growth template `created_at` date is now automatically set to the current date when analysis is run.
