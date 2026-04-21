package views

import (
	"skene/internal/constants"
	"skene/internal/tui/components"
	"skene/internal/tui/styles"

	"github.com/charmbracelet/lipgloss"
)

// AnalysisMode represents the selected analysis type.
type AnalysisMode int

const (
	ModeSimple   AnalysisMode = iota
	ModeAdvanced
)

// AnalysisConfigView shows a mode selector, summary, and Run Analysis button.
type AnalysisConfigView struct {
	width        int
	height       int
	header       *components.WizardHeader
	providerName string
	modelName    string
	projectDir   string
	selectedMode AnalysisMode
}

// NewAnalysisConfigView creates a new analysis configuration view.
func NewAnalysisConfigView(provider, model, projectDir string) *AnalysisConfigView {
	return &AnalysisConfigView{
		providerName: provider,
		modelName:    model,
		projectDir:   projectDir,
		selectedMode: ModeSimple,
		header:       components.NewWizardHeader(3, constants.StepNameAnalysisConfig),
	}
}

// SetSize updates dimensions.
func (v *AnalysisConfigView) SetSize(width, height int) {
	v.width = width
	v.height = height
	v.header.SetWidth(width)
}

// HandleUp moves mode selection up.
func (v *AnalysisConfigView) HandleUp() {
	if v.selectedMode > ModeSimple {
		v.selectedMode--
	}
}

// HandleDown moves mode selection down.
func (v *AnalysisConfigView) HandleDown() {
	if v.selectedMode < ModeAdvanced {
		v.selectedMode++
	}
}

// GetAnalysisMode returns the currently selected analysis mode.
func (v *AnalysisConfigView) GetAnalysisMode() AnalysisMode {
	return v.selectedMode
}

// IsSimpleMode returns true if simple analysis is selected.
func (v *AnalysisConfigView) IsSimpleMode() bool {
	return v.selectedMode == ModeSimple
}

// GetUseGrowth always returns true (only package).
func (v *AnalysisConfigView) GetUseGrowth() bool {
	return true
}

// Render the analysis config view.
func (v *AnalysisConfigView) Render() string {
	sectionWidth := v.width - 20
	if sectionWidth < 60 {
		sectionWidth = 60
	}
	if sectionWidth > 80 {
		sectionWidth = 80
	}

	wizHeader := lipgloss.NewStyle().Width(sectionWidth).Render(v.header.Render())

	modeSection := v.renderModeSelector(sectionWidth)
	summarySection := v.renderSummary(sectionWidth)

	button := lipgloss.NewStyle().
		Width(sectionWidth).
		Align(lipgloss.Center).
		Render(styles.ButtonActive.Render(constants.AnalysisConfigRunButton))

	footer := lipgloss.NewStyle().
		Width(v.width).
		Align(lipgloss.Center).
		Render(components.FooterHelp([]components.HelpItem{
			{Key: constants.HelpKeyUpDown, Desc: constants.HelpDescSelect},
			{Key: constants.HelpKeyEnter, Desc: constants.HelpDescStartAnalysis},
			{Key: constants.HelpKeyEsc, Desc: constants.HelpDescGoBack},
			{Key: constants.HelpKeyCtrlC, Desc: constants.HelpDescQuit},
		}, v.width))

	content := lipgloss.JoinVertical(
		lipgloss.Left,
		wizHeader,
		"",
		modeSection,
		"",
		summarySection,
		"",
		button,
	)

	padded := lipgloss.NewStyle().PaddingTop(2).Render(content)

	centered := lipgloss.Place(
		v.width,
		v.height-3,
		lipgloss.Center,
		lipgloss.Top,
		padded,
	)

	return centered + "\n" + footer
}

func (v *AnalysisConfigView) renderModeSelector(width int) string {
	descWidth := width - 8

	modes := []struct {
		name string
		desc string
	}{
		{constants.AnalysisModeSimple, constants.AnalysisModeSimpleDesc},
		{constants.AnalysisModeAdvanced, constants.AnalysisModeAdvancedDesc},
	}

	var items []string
	for i, mode := range modes {
		isSelected := AnalysisMode(i) == v.selectedMode

		var name, desc string
		if isSelected {
			name = styles.ListItemSelected.Render(mode.name)
		} else {
			name = styles.ListItem.Render(mode.name)
		}
		desc = lipgloss.NewStyle().Foreground(styles.MutedColor).PaddingLeft(2).Width(descWidth).Render(mode.desc)

		items = append(items, name+"\n"+desc)

		if i < len(modes)-1 {
			items = append(items, "")
		}
	}

	list := lipgloss.JoinVertical(lipgloss.Left, items...)
	return styles.Box.Width(width).Render(list)
}

func (v *AnalysisConfigView) renderSummary(width int) string {
	header := styles.SectionHeader.Render(constants.AnalysisConfigSummary)

	valueWidth := width - 20
	if valueWidth < 30 {
		valueWidth = 30
	}
	rows := []string{
		styles.Label.Render("Provider:   ") + lipgloss.NewStyle().Foreground(styles.TextColor).Width(valueWidth).Render(v.providerName),
		styles.Label.Render("Model:      ") + lipgloss.NewStyle().Foreground(styles.TextColor).Width(valueWidth).Render(v.modelName),
		styles.Label.Render("Directory:  ") + lipgloss.NewStyle().Foreground(styles.TextColor).Width(valueWidth).Render(v.projectDir),
		styles.Label.Render("Output:     ") + lipgloss.NewStyle().Foreground(styles.TextColor).Width(valueWidth).Render(constants.DefaultOutputDir+"/"),
	}

	content := lipgloss.JoinVertical(
		lipgloss.Left,
		header,
		"",
		lipgloss.JoinVertical(lipgloss.Left, rows...),
	)

	return styles.Box.Width(width).Render(content)
}

// GetHelpItems returns context-specific help.
func (v *AnalysisConfigView) GetHelpItems() []components.HelpItem {
	return []components.HelpItem{
		{Key: constants.HelpKeyUpDown, Desc: constants.HelpDescSelect},
		{Key: constants.HelpKeyEnter, Desc: constants.HelpDescStartAnalysis},
		{Key: constants.HelpKeyEsc, Desc: constants.HelpDescGoBack},
		{Key: constants.HelpKeyCtrlC, Desc: constants.HelpDescQuit},
	}
}
