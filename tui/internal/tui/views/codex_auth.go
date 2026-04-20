package views

import (
	"skene/internal/constants"
	"skene/internal/services/auth"
	"skene/internal/tui/components"
	"skene/internal/tui/styles"

	"github.com/charmbracelet/lipgloss"
)

// CodexAuthView shows local Codex CLI login status.
type CodexAuthView struct {
	width        int
	height       int
	providerName string
	modelName    string
	checking     bool
	status       auth.CodexStatus
	header       *components.WizardHeader
	spinner      *components.Spinner
}

// NewCodexAuthView creates a new Codex auth status view.
func NewCodexAuthView(providerName, modelName string) *CodexAuthView {
	return &CodexAuthView{
		providerName: providerName,
		modelName:    modelName,
		checking:     true,
		header:       components.NewWizardHeader(2, constants.StepNameAuthentication),
		spinner:      components.NewSpinner(),
	}
}

// SetSize updates dimensions.
func (v *CodexAuthView) SetSize(width, height int) {
	v.width = width
	v.height = height
	v.header.SetWidth(width)
}

// SetChecking updates the pending state.
func (v *CodexAuthView) SetChecking(checking bool) {
	v.checking = checking
}

// SetStatus applies a resolved Codex status.
func (v *CodexAuthView) SetStatus(status auth.CodexStatus) {
	v.status = status
	v.checking = false
}

// TickSpinner advances the spinner animation.
func (v *CodexAuthView) TickSpinner() {
	v.spinner.Tick()
}

// Render draws the Codex auth status view.
func (v *CodexAuthView) Render() string {
	sectionWidth := v.width - 20
	if sectionWidth < 60 {
		sectionWidth = 60
	}
	if sectionWidth > 80 {
		sectionWidth = 80
	}

	wizHeader := lipgloss.NewStyle().Width(sectionWidth).Render(v.header.Render())
	contentSection := v.renderContent(sectionWidth)

	helpItems := []components.HelpItem{
		{Key: constants.HelpKeyEnter, Desc: constants.HelpDescRetry},
		{Key: constants.HelpKeyR, Desc: constants.HelpDescRetry},
		{Key: constants.HelpKeyEsc, Desc: constants.HelpDescGoBack},
		{Key: constants.HelpKeyCtrlC, Desc: constants.HelpDescQuit},
	}
	if v.checking {
		helpItems = []components.HelpItem{
			{Key: constants.HelpKeyEsc, Desc: constants.HelpDescGoBack},
			{Key: constants.HelpKeyCtrlC, Desc: constants.HelpDescQuit},
		}
	}

	footer := lipgloss.NewStyle().
		Width(v.width).
		Align(lipgloss.Center).
		Render(components.FooterHelp(helpItems, v.width))

	content := lipgloss.JoinVertical(
		lipgloss.Left,
		wizHeader,
		"",
		contentSection,
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

func (v *CodexAuthView) renderContent(width int) string {
	header := styles.SectionHeader.Render("Codex Login")
	infoRows := []string{
		styles.Label.Render("Provider: ") + styles.Body.Render(v.providerName),
	}
	if v.modelName != "" {
		infoRows = append(infoRows, styles.Label.Render("Model:    ")+styles.Body.Render(v.modelName))
	}

	var statusBlock string
	switch {
	case v.checking:
		statusBlock = lipgloss.JoinVertical(
			lipgloss.Left,
			v.spinner.SpinnerWithText("Checking local Codex login..."),
			styles.Muted.Render("Skene will use your existing Codex CLI session."),
		)
	case v.status.LoggedIn:
		statusBlock = lipgloss.JoinVertical(
			lipgloss.Left,
			styles.SuccessText.Render("✓ Codex CLI is ready"),
			styles.Muted.Render(v.status.Message),
		)
	default:
		setupHint := "Run `codex login`, then press Enter or r to retry."
		if !v.status.Installed {
			setupHint = "Install the Codex CLI, run `codex login`, then press Enter or r to retry."
		}
		statusBlock = lipgloss.JoinVertical(
			lipgloss.Left,
			lipgloss.NewStyle().Foreground(styles.ErrorColor).Render("✗ "+v.status.Message),
			styles.Muted.Render(setupHint),
		)
	}

	content := lipgloss.JoinVertical(
		lipgloss.Left,
		header,
		"",
		lipgloss.JoinVertical(lipgloss.Left, infoRows...),
		"",
		statusBlock,
	)

	return styles.Box.Width(width).Render(content)
}

// GetHelpItems returns context-specific help.
func (v *CodexAuthView) GetHelpItems() []components.HelpItem {
	if v.checking {
		return []components.HelpItem{
			{Key: constants.HelpKeyEsc, Desc: constants.HelpDescGoBack},
			{Key: constants.HelpKeyCtrlC, Desc: constants.HelpDescQuit},
		}
	}
	return []components.HelpItem{
		{Key: constants.HelpKeyEnter, Desc: constants.HelpDescRetry},
		{Key: constants.HelpKeyR, Desc: constants.HelpDescRetry},
		{Key: constants.HelpKeyEsc, Desc: constants.HelpDescGoBack},
		{Key: constants.HelpKeyCtrlC, Desc: constants.HelpDescQuit},
	}
}
